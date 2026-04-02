from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.schemas import SessionSkillUpdateRequest, SkillResponse
from app.services.session_service import SessionService
from app.services.skill_service import SkillService

router = APIRouter()

skill_service = SkillService()
session_service = SessionService()


@router.get("/skills", response_model=list[SkillResponse])
async def list_skills():
    return skill_service.discover_skills()


@router.get("/sessions/{session_id}/skills")
async def get_session_skills(session_id: int, db: AsyncSession = Depends(get_db)):
    session = await session_service.get_by_id(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    return {"skills": await skill_service.list_session_skills(db, session_id)}


@router.put("/sessions/{session_id}/skills")
async def update_session_skills(
    session_id: int,
    payload: SessionSkillUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    session = await session_service.get_by_id(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    updated = await skill_service.update_session_skills(
        db,
        session_id,
        [item.model_dump() for item in payload.skills],
    )
    return {"skills": updated}
