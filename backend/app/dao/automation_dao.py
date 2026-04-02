from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Automation, AutomationRun


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
    async def list_by_automation(db: AsyncSession, automation_id: int, limit: int = 20) -> List[AutomationRun]:
        result = await db.execute(
            select(AutomationRun)
            .where(AutomationRun.automation_id == automation_id)
            .order_by(AutomationRun.triggered_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

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
