from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import AgentRun


class AgentRunDAO:
    @staticmethod
    async def create(db: AsyncSession, **kwargs) -> AgentRun:
        record = AgentRun(**kwargs)
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return record

    @staticmethod
    async def get_by_run_id(db: AsyncSession, run_id: str) -> Optional[AgentRun]:
        result = await db.execute(select(AgentRun).where(AgentRun.run_id == run_id).limit(1))
        return result.scalar_one_or_none()

    @staticmethod
    async def update(db: AsyncSession, record: AgentRun, **changes) -> AgentRun:
        for key, value in changes.items():
            setattr(record, key, value)
        await db.commit()
        await db.refresh(record)
        return record

    @staticmethod
    async def list_by_session(db: AsyncSession, session_id: int, limit: int = 20) -> List[AgentRun]:
        result = await db.execute(
            select(AgentRun).where(AgentRun.session_id == session_id).order_by(AgentRun.started_at.desc()).limit(limit)
        )
        return list(result.scalars().all())
