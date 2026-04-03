from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Session


class SessionDAO:
    @staticmethod
    async def list_all(db: AsyncSession) -> List[Session]:
        result = await db.execute(select(Session).order_by(Session.is_default.desc(), Session.updated_at.desc()))
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(db: AsyncSession, session_id: int) -> Optional[Session]:
        return await db.get(Session, session_id)

    @staticmethod
    async def get_default(db: AsyncSession) -> Optional[Session]:
        result = await db.execute(select(Session).where(Session.is_default.is_(True)).limit(1))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        name: str,
        mode: str = "personal",
        workspace_path: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        tool_profile: str = "full",
        tool_allow: Optional[str] = None,
        tool_deny: Optional[str] = None,
        max_iterations: int = 30,
        context_summary: Optional[str] = None,
        memory_auto_extract: bool = False,
        memory_threshold: int = 8,
        is_default: bool = False,
    ) -> Session:
        if is_default:
            await db.execute(update(Session).values(is_default=False))
        session = Session(
            name=name,
            mode=mode,
            workspace_path=workspace_path,
            model=model,
            provider=provider,
            tool_profile=tool_profile,
            tool_allow=tool_allow,
            tool_deny=tool_deny,
            max_iterations=max_iterations,
            context_summary=context_summary,
            memory_auto_extract=memory_auto_extract,
            memory_threshold=memory_threshold,
            is_default=is_default,
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    @staticmethod
    async def update(db: AsyncSession, session: Session, **changes) -> Session:
        if changes.get("is_default"):
            await db.execute(update(Session).values(is_default=False))
        for key, value in changes.items():
            setattr(session, key, value)
        await db.commit()
        await db.refresh(session)
        return session

    @staticmethod
    async def delete(db: AsyncSession, session: Session) -> None:
        await db.delete(session)
        await db.commit()
