from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.schemas import AutomationCreate, AutomationResponse, AutomationRunResponse, AutomationUpdate
from app.services.automation_service import AutomationService
from app.services.session_service import SessionService

router = APIRouter()

automation_service = AutomationService()
session_service = SessionService()


@router.get("/automations", response_model=list[AutomationResponse])
async def list_automations(db: AsyncSession = Depends(get_db)):
    return await automation_service.list_all(db)


@router.post("/automations", response_model=AutomationResponse)
async def create_automation(payload: AutomationCreate, db: AsyncSession = Depends(get_db)):
    session = await session_service.get_by_id(db, payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    return await automation_service.create(db, **payload.model_dump())


@router.put("/automations/{automation_id}", response_model=AutomationResponse)
async def update_automation(automation_id: int, payload: AutomationUpdate, db: AsyncSession = Depends(get_db)):
    automation = await automation_service.update(db, automation_id, **payload.model_dump(exclude_unset=True))
    if not automation:
        raise HTTPException(status_code=404, detail="automation not found")
    return automation


@router.delete("/automations/{automation_id}")
async def delete_automation(automation_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await automation_service.delete(db, automation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="automation not found")
    return {"success": True}


@router.get("/automations/{automation_id}/runs", response_model=list[AutomationRunResponse])
async def list_automation_runs(automation_id: int, db: AsyncSession = Depends(get_db)):
    return await automation_service.list_runs(db, automation_id)
