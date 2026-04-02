from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.schemas import (
    AutomationCreate,
    AutomationDispatchResponse,
    AutomationResponse,
    AutomationRunResponse,
    AutomationStatsResponse,
    AutomationUpdate,
)
from app.services.automation_service import AutomationService
from app.services.session_service import SessionService
from app.api.chat import agent_loop_controller

router = APIRouter()

automation_service = AutomationService()
session_service = SessionService()


@router.get("/automations", response_model=list[AutomationResponse])
async def list_automations(db: AsyncSession = Depends(get_db)):
    return await automation_service.list_all(db)


@router.get("/automations/stats", response_model=AutomationStatsResponse)
async def get_automation_stats(db: AsyncSession = Depends(get_db)):
    return await automation_service.get_stats(db)


@router.post("/automations", response_model=AutomationResponse)
async def create_automation(payload: AutomationCreate, db: AsyncSession = Depends(get_db)):
    session = await session_service.resolve_session(db, payload.session_id)
    payload_data = payload.model_dump()
    payload_data["session_id"] = session.id
    try:
        return await automation_service.create(db, **payload_data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/automations/{automation_id}", response_model=AutomationResponse)
async def update_automation(automation_id: int, payload: AutomationUpdate, db: AsyncSession = Depends(get_db)):
    changes = payload.model_dump(exclude_unset=True)
    if "session_id" in changes:
        session = await session_service.resolve_session(db, changes["session_id"])
        changes["session_id"] = session.id
    try:
        automation = await automation_service.update(db, automation_id, **changes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
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


@router.post("/automations/{automation_id}/run", response_model=AutomationDispatchResponse)
async def run_automation_now(automation_id: int, db: AsyncSession = Depends(get_db)):
    try:
        run_id = await automation_service.trigger_manual_run(
            db,
            automation_id,
            agent_loop_controller.dispatch_message_for_automation,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if run_id is None:
        raise HTTPException(status_code=404, detail="automation not found")
    return {
        "success": True,
        "automation_id": automation_id,
        "trigger_mode": "manual",
        "run_id": run_id,
    }
