from __future__ import annotations

from typing import List

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import SessionSkill


class SessionSkillDAO:
    @staticmethod
    async def list_by_session(db: AsyncSession, session_id: int) -> List[SessionSkill]:
        result = await db.execute(
            select(SessionSkill).where(SessionSkill.session_id == session_id).order_by(SessionSkill.skill_name.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def replace_for_session(db: AsyncSession, session_id: int, skills: list[dict]) -> List[SessionSkill]:
        await db.execute(delete(SessionSkill).where(SessionSkill.session_id == session_id))
        records: List[SessionSkill] = []
        for item in skills:
            record = SessionSkill(
                session_id=session_id,
                skill_name=item["skill_name"],
                skill_path=item["skill_path"],
                enabled=item.get("enabled", True),
            )
            db.add(record)
            records.append(record)
        await db.commit()
        for record in records:
            await db.refresh(record)
        return records
