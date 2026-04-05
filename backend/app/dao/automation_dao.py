from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import AgentEvent, Automation, AutomationRun, Message


class AutomationDAO:
    @staticmethod
    async def list_all(db: AsyncSession) -> List[Automation]:
        result = await db.execute(select(Automation).order_by(Automation.updated_at.desc()))
        return list(result.scalars().all())

    @staticmethod
    async def list_due(db: AsyncSession, now: datetime) -> List[Automation]:
        result = await db.execute(
            select(Automation)
            .where(Automation.enabled.is_(True), Automation.next_run_at.is_not(None), Automation.next_run_at <= now)
            .order_by(Automation.next_run_at.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(db: AsyncSession, automation_id: int) -> Optional[Automation]:
        return await db.get(Automation, automation_id)

    @staticmethod
    async def create(db: AsyncSession, **kwargs) -> Automation:
        automation = Automation(**kwargs)
        db.add(automation)
        await db.commit()
        await db.refresh(automation)
        return automation

    @staticmethod
    async def update(db: AsyncSession, automation: Automation, **changes) -> Automation:
        for key, value in changes.items():
            setattr(automation, key, value)
        await db.commit()
        await db.refresh(automation)
        return automation

    @staticmethod
    async def delete(db: AsyncSession, automation: Automation) -> None:
        await db.delete(automation)
        await db.commit()


class AutomationRunDAO:
    @staticmethod
    async def list_all(db: AsyncSession, limit: int = 100) -> List[tuple]:
        """Return (AutomationRun, automation_name, response_snippet) tuples, ordered by triggered_at DESC."""
        # Subquery: for each run_id, pick the latest agent_event that has a message_id
        last_event = (
            select(
                AgentEvent.run_id.label("run_id"),
                func.max(AgentEvent.id).label("evt_id"),
            )
            .where(AgentEvent.message_id.is_not(None))
            .group_by(AgentEvent.run_id)
            .subquery()
        )
        snippet = func.substr(Message.content, 1, 120).label("response_snippet")
        result = await db.execute(
            select(AutomationRun, Automation.name.label("automation_name"), snippet)
            .join(Automation, AutomationRun.automation_id == Automation.id)
            .outerjoin(last_event, last_event.c.run_id == AutomationRun.run_id)
            .outerjoin(AgentEvent, AgentEvent.id == last_event.c.evt_id)
            .outerjoin(
                Message,
                (Message.id == AgentEvent.message_id) & (Message.role == "assistant"),
            )
            .order_by(AutomationRun.triggered_at.desc())
            .limit(limit)
        )
        return list(result.all())

    @staticmethod
    async def create(db: AsyncSession, **kwargs) -> AutomationRun:
        record = AutomationRun(**kwargs)
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return record

    @staticmethod
    async def update(db: AsyncSession, run: AutomationRun, **changes) -> AutomationRun:
        for key, value in changes.items():
            setattr(run, key, value)
        await db.commit()
        await db.refresh(run)
        return run

    @staticmethod
    async def count_running(db: AsyncSession) -> int:
        result = await db.execute(select(func.count()).select_from(AutomationRun).where(AutomationRun.status == "running"))
        return int(result.scalar_one() or 0)

    @staticmethod
    async def count_running_for_automation(db: AsyncSession, automation_id: int) -> int:
        result = await db.execute(
            select(func.count())
            .select_from(AutomationRun)
            .where(AutomationRun.automation_id == automation_id, AutomationRun.status == "running")
        )
        return int(result.scalar_one() or 0)

    @staticmethod
    async def count_recent_failures(db: AsyncSession, within_hours: int = 24) -> int:
        cutoff = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=within_hours)
        result = await db.execute(
            select(func.count())
            .select_from(AutomationRun)
            .where(AutomationRun.status == "failed", AutomationRun.triggered_at >= cutoff)
        )
        return int(result.scalar_one() or 0)
