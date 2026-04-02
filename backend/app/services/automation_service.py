from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from datetime import tzinfo
from typing import Any, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from croniter import croniter
import pytz
from sqlalchemy.ext.asyncio import AsyncSession

from app.dao.automation_dao import AutomationDAO, AutomationRunDAO

logger = logging.getLogger(__name__)

SUPPORTED_SCHEDULE_TYPES = {"once", "interval", "daily", "weekly", "cron"}


def _utc_now() -> datetime:
    return datetime.utcnow().replace(tzinfo=None)


def _to_utc_naive(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=None)
    return value.astimezone(UTC).replace(tzinfo=None)


def _get_timezone(timezone: str) -> tzinfo:
    normalized = timezone or "UTC"
    if normalized.upper() == "UTC":
        return UTC
    try:
        return ZoneInfo(normalized)
    except ZoneInfoNotFoundError as exc:
        try:
            return pytz.timezone(normalized)
        except pytz.UnknownTimeZoneError as pytz_exc:
            raise ValueError(f"unsupported timezone: {timezone}") from pytz_exc


def _parse_hhmm(value: str) -> tuple[int, int]:
    try:
        hour_text, minute_text = value.split(":")
        hour = int(hour_text)
        minute = int(minute_text)
    except ValueError as exc:
        raise ValueError("time must use HH:MM format") from exc

    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError("time must be within 00:00-23:59")
    return hour, minute


def _parse_once_datetime(value: str, timezone: str) -> datetime:
    try:
        normalized = value.replace("Z", "+00:00")
        candidate = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError("one-time schedule must be a valid ISO datetime") from exc

    if candidate.tzinfo is None:
        candidate = candidate.replace(tzinfo=_get_timezone(timezone))
    return candidate.astimezone(UTC).replace(tzinfo=None)


def validate_schedule(schedule_type: str, schedule_value: str, timezone: str) -> None:
    if schedule_type not in SUPPORTED_SCHEDULE_TYPES:
        raise ValueError(f"unsupported schedule_type: {schedule_type}")

    _get_timezone(timezone)

    if schedule_type == "once":
        _parse_once_datetime(schedule_value, timezone)
        return

    if schedule_type == "interval":
        try:
            minutes = int(schedule_value)
        except ValueError as exc:
            raise ValueError("interval schedule must be an integer number of minutes") from exc
        if minutes < 1 or minutes > 60 * 24 * 365:
            raise ValueError("interval minutes must be between 1 and 525600")
        return

    if schedule_type == "daily":
        _parse_hhmm(schedule_value)
        return

    if schedule_type == "weekly":
        try:
            weekday_text, time_text = schedule_value.split("|")
            weekday = int(weekday_text)
        except ValueError as exc:
            raise ValueError("weekly schedule must use weekday|HH:MM format") from exc
        if weekday < 0 or weekday > 6:
            raise ValueError("weekly weekday must be between 0 (Monday) and 6 (Sunday)")
        _parse_hhmm(time_text)
        return

    localized_now = datetime.now(_get_timezone(timezone))
    try:
        croniter(schedule_value, localized_now)
    except (ValueError, KeyError) as exc:
        raise ValueError("invalid cron expression") from exc


def compute_next_run(
    schedule_type: str,
    schedule_value: str,
    *,
    timezone: str = "UTC",
    from_time: Optional[datetime] = None,
) -> Optional[datetime]:
    validate_schedule(schedule_type, schedule_value, timezone)
    base_utc = _to_utc_naive(from_time or _utc_now())

    if schedule_type == "once":
        candidate = _parse_once_datetime(schedule_value, timezone)
        return candidate if candidate > base_utc else None

    if schedule_type == "interval":
        minutes = int(schedule_value)
        return base_utc + timedelta(minutes=minutes)

    tz = _get_timezone(timezone)
    localized_base = base_utc.replace(tzinfo=UTC).astimezone(tz)

    if schedule_type == "daily":
        hour, minute = _parse_hhmm(schedule_value)
        candidate = localized_base.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if candidate <= localized_base:
            candidate += timedelta(days=1)
        return candidate.astimezone(UTC).replace(tzinfo=None)

    if schedule_type == "weekly":
        weekday_text, time_text = schedule_value.split("|")
        weekday = int(weekday_text)
        hour, minute = _parse_hhmm(time_text)
        days_ahead = (weekday - localized_base.weekday()) % 7
        candidate = localized_base.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(
            days=days_ahead
        )
        if candidate <= localized_base:
            candidate += timedelta(days=7)
        return candidate.astimezone(UTC).replace(tzinfo=None)

    iterator = croniter(schedule_value, localized_base)
    candidate = iterator.get_next(datetime)
    if candidate.tzinfo is None:
        candidate = candidate.replace(tzinfo=tz)
    return candidate.astimezone(UTC).replace(tzinfo=None)


class AutomationService:
    def __init__(self) -> None:
        self._task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self, session_factory, runner) -> None:
        if self._task and not self._task.done():
            return
        self._running = True
        self._task = asyncio.create_task(self._loop(session_factory, runner))

    async def stop(self) -> None:
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def list_all(self, db: AsyncSession):
        return await AutomationDAO.list_all(db)

    async def get_stats(self, db: AsyncSession) -> dict[str, Any]:
        automations = await AutomationDAO.list_all(db)
        running = await AutomationRunDAO.count_running(db)
        failed_recently = await AutomationRunDAO.count_recent_failures(db)
        enabled = [item for item in automations if item.enabled]
        next_run_at = min((item.next_run_at for item in enabled if item.next_run_at), default=None)
        last_run_at = max((item.last_run_at for item in automations if item.last_run_at), default=None)
        due_now = sum(1 for item in enabled if item.next_run_at and item.next_run_at <= _utc_now())
        return {
            "total": len(automations),
            "enabled": len(enabled),
            "disabled": len(automations) - len(enabled),
            "due_now": due_now,
            "running": running,
            "failed_recently": failed_recently,
            "next_run_at": next_run_at,
            "last_run_at": last_run_at,
        }

    def _prepare_payload(self, data: dict[str, Any], *, existing: Optional[Any] = None) -> dict[str, Any]:
        schedule_type = data.get("schedule_type", getattr(existing, "schedule_type", None))
        schedule_value = data.get("schedule_value", getattr(existing, "schedule_value", None))
        timezone = data.get("timezone", getattr(existing, "timezone", "UTC"))

        if not schedule_type or not schedule_value:
            raise ValueError("schedule_type and schedule_value are required")

        validate_schedule(schedule_type, schedule_value, timezone)

        payload = dict(data)
        payload["timezone"] = timezone
        if payload.get("enabled", getattr(existing, "enabled", True)):
            next_run_at = compute_next_run(
                schedule_type,
                schedule_value,
                timezone=timezone,
            )
            if schedule_type == "once" and next_run_at is None:
                raise ValueError("one-time schedule must be in the future")
            payload["next_run_at"] = next_run_at
        elif "next_run_at" not in payload and existing is not None:
            payload["next_run_at"] = existing.next_run_at
        return payload

    async def create(self, db: AsyncSession, **data):
        payload = self._prepare_payload(data)
        return await AutomationDAO.create(db, **payload)

    async def update(self, db: AsyncSession, automation_id: int, **changes):
        automation = await AutomationDAO.get_by_id(db, automation_id)
        if not automation:
            return None

        needs_recompute = any(key in changes for key in {"schedule_type", "schedule_value", "timezone", "enabled"})
        payload = self._prepare_payload(changes, existing=automation) if needs_recompute else changes
        return await AutomationDAO.update(db, automation, **payload)

    async def delete(self, db: AsyncSession, automation_id: int) -> bool:
        automation = await AutomationDAO.get_by_id(db, automation_id)
        if not automation:
            return False
        await AutomationDAO.delete(db, automation)
        return True

    async def list_runs(self, db: AsyncSession, automation_id: int):
        return await AutomationRunDAO.list_by_automation(db, automation_id)

    async def _execute_run(self, db: AsyncSession, automation, runner, *, trigger_mode: str) -> str:
        run = await AutomationRunDAO.create(
            db,
            automation_id=automation.id,
            session_id=automation.session_id,
            status="running",
            trigger_mode=trigger_mode,
        )
        completed_at = _utc_now()
        try:
            run_id = await runner(automation.session_id, automation.prompt, automation.id)
            await AutomationRunDAO.update(
                db,
                run,
                status="success",
                run_id=run_id,
                completed_at=completed_at,
            )
            automation_changes: dict[str, Any] = {"last_run_at": completed_at}
            if trigger_mode == "scheduled":
                if automation.schedule_type == "once":
                    automation_changes["enabled"] = False
                    automation_changes["next_run_at"] = None
                else:
                    automation_changes["next_run_at"] = compute_next_run(
                        automation.schedule_type,
                        automation.schedule_value,
                        timezone=automation.timezone,
                        from_time=completed_at,
                    )
            elif automation.schedule_type == "once":
                automation_changes["enabled"] = False
                automation_changes["next_run_at"] = None
            await AutomationDAO.update(db, automation, **automation_changes)
            return run_id
        except Exception as exc:
            logger.exception("[automation] run failed")
            await AutomationRunDAO.update(
                db,
                run,
                status="failed",
                error=str(exc),
                completed_at=completed_at,
            )
            automation_changes = {"last_run_at": completed_at}
            if trigger_mode == "scheduled":
                automation_changes["next_run_at"] = (
                    None
                    if automation.schedule_type == "once"
                    else compute_next_run(
                        automation.schedule_type,
                        automation.schedule_value,
                        timezone=automation.timezone,
                        from_time=completed_at,
                    )
                )
                if automation.schedule_type == "once":
                    automation_changes["enabled"] = False
            await AutomationDAO.update(db, automation, **automation_changes)
            raise

    async def trigger_manual_run(self, db: AsyncSession, automation_id: int, runner) -> Optional[str]:
        automation = await AutomationDAO.get_by_id(db, automation_id)
        if not automation:
            return None
        return await self._execute_run(db, automation, runner, trigger_mode="manual")

    async def run_due_once(self, db: AsyncSession, runner) -> None:
        due = await AutomationDAO.list_due(db, _utc_now())
        for automation in due:
            try:
                await self._execute_run(db, automation, runner, trigger_mode="scheduled")
            except Exception:
                logger.exception("[automation] scheduled execution failed for automation_id=%s", automation.id)

    async def _loop(self, session_factory, runner) -> None:
        while self._running:
            try:
                async with session_factory() as db:
                    await self.run_due_once(db, runner)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("[automation] scheduler loop failed")
            await asyncio.sleep(15)
