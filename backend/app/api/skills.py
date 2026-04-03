from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.schemas import SkillResponse
from app.services.skill_service import SkillService

router = APIRouter()

skill_service = SkillService()


@router.get("/skills", response_model=list[SkillResponse])
async def list_skills():
    return skill_service.discover_skills()
