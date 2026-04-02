from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.dao.agent_run_dao import AgentRunDAO
from app.dao.session_dao import SessionDAO
from app.models.models import Session


class SessionService:
    async def list_all(self, db: AsyncSession) -> list[Session]:
        return await SessionDAO.list_all(db)

    async def get_default(self, db: AsyncSession) -> Optional[Session]:
        return await SessionDAO.get_default(db)

    async def get_by_id(self, db: AsyncSession, session_id: int) -> Optional[Session]:
        return await SessionDAO.get_by_id(db, session_id)

    async def create(self, db: AsyncSession, **data) -> Session:
        if not data.get("workspace_path"):
            data["workspace_path"] = str(Path.cwd())
        return await SessionDAO.create(db, **data)

    async def update(self, db: AsyncSession, session_id: int, **changes) -> Optional[Session]:
        session = await SessionDAO.get_by_id(db, session_id)
        if not session:
            return None
        return await SessionDAO.update(db, session, **changes)

    async def delete(self, db: AsyncSession, session_id: int) -> bool:
        session = await SessionDAO.get_by_id(db, session_id)
        if not session:
            return False
        await SessionDAO.delete(db, session)
        return True

    async def resolve_session(self, db: AsyncSession, session_id: Optional[int] = None) -> Session:
        if session_id is not None:
            session = await SessionDAO.get_by_id(db, session_id)
            if session:
                return session
        default_session = await SessionDAO.get_default(db)
        if default_session:
            return default_session
        return await SessionDAO.create(
            db,
            name="main",
            mode="personal",
            workspace_path=os.getenv("MYCLAW_DEFAULT_WORKSPACE", str(Path.cwd())),
            is_default=True,
        )

    async def get_status(self, db: AsyncSession, session_id: int) -> Optional[dict]:
        session = await SessionDAO.get_by_id(db, session_id)
        if not session:
            return None
        recent_runs = await AgentRunDAO.list_by_session(db, session_id, limit=5)
        return {
            "id": session.id,
            "name": session.name,
            "mode": session.mode,
            "workspace_path": session.workspace_path,
            "model": session.model,
            "provider": session.provider,
            "tool_profile": session.tool_profile,
            "tool_allow": [item.strip() for item in (session.tool_allow or "").split(",") if item.strip()],
            "tool_deny": [item.strip() for item in (session.tool_deny or "").split(",") if item.strip()],
            "max_iterations": session.max_iterations,
            "context_summary": session.context_summary or "",
            "memory_auto_extract": session.memory_auto_extract,
            "memory_threshold": session.memory_threshold,
            "is_default": session.is_default,
            "recent_runs": [
                {
                    "run_id": run.run_id,
                    "conversation_id": run.conversation_id,
                    "user_message": run.user_message,
                    "stop_reason": run.stop_reason,
                    "compacted_summary": run.compacted_summary,
                    "started_at": run.started_at.isoformat() if run.started_at else None,
                    "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                }
                for run in recent_runs
            ],
        }
