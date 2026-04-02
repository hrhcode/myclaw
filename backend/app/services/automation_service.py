from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.dao.automation_dao import AutomationDAO, AutomationRunDAO

logger = logging.getLogger(__name__)


def compute_next_run(schedule_type: str, schedule_value: str, *, from_time: Optional[datetime] = None) -> Optional[datetime]:
    base = from_time or datetime.utcnow()
    if schedule_type == "interval":
        minutes = max(int(schedule_value), 1)
        return base + timedelta(minutes=minutes)

    if schedule_type in {"daily", "weekly"}:
        parts = schedule_value.split("|")
        if schedule_type == "daily":
            hour, minute = [int(item) for item in parts[0].split(":")]
            candidate = base.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if candidate <= base:
                candidate += timedelta(days=1)
            return candidate
        weekday = int(parts[0])
        hour, minute = [int(item) for item in parts[1].split(":")]
        days_ahead = (weekday - base.weekday()) % 7
        candidate = base.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=days_ahead)
        if candidate <= base:
            candidate += timedelta(days=7)
        return candidate
    return None


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

    async def create(self, db: AsyncSession, **data):
        if not data.get("next_run_at"):
            data["next_run_at"] = compute_next_run(data["schedule_type"], data["schedule_value"])
        return await AutomationDAO.create(db, **data)

    async def update(self, db: AsyncSession, automation_id: int, **changes):
        automation = await AutomationDAO.get_by_id(db, automation_id)
        if not automation:
            return None
        if "schedule_type" in changes or "schedule_value" in changes:
            next_type = changes.get("schedule_type", automation.schedule_type)
            next_value = changes.get("schedule_value", automation.schedule_value)
            changes["next_run_at"] = compute_next_run(next_type, next_value)
        return await AutomationDAO.update(db, automation, **changes)

    async def delete(self, db: AsyncSession, automation_id: int) -> bool:
        automation = await AutomationDAO.get_by_id(db, automation_id)
        if not automation:
            return False
        await AutomationDAO.delete(db, automation)
        return True

    async def list_runs(self, db: AsyncSession, automation_id: int):
        return await AutomationRunDAO.list_by_automation(db, automation_id)

    async def run_due_once(self, db: AsyncSession, runner) -> None:
        due = await AutomationDAO.list_due(db, datetime.utcnow())
        for automation in due:
            run = await AutomationRunDAO.create(
                db,
                automation_id=automation.id,
                session_id=automation.session_id,
                status="running",
            )
            try:
                run_id = await runner(automation.session_id, automation.prompt, automation.id)
                await AutomationRunDAO.update(
                    db,
                    run,
                    status="success",
                    run_id=run_id,
                    completed_at=datetime.utcnow(),
                )
                await AutomationDAO.update(
                    db,
                    automation,
                    last_run_at=datetime.utcnow(),
                    next_run_at=compute_next_run(automation.schedule_type, automation.schedule_value),
                )
            except Exception as exc:
                logger.exception("[automation] run failed")
                await AutomationRunDAO.update(
                    db,
                    run,
                    status="failed",
                    error=str(exc),
                    completed_at=datetime.utcnow(),
                )
                await AutomationDAO.update(
                    db,
                    automation,
                    last_run_at=datetime.utcnow(),
                    next_run_at=compute_next_run(automation.schedule_type, automation.schedule_value),
                )

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
