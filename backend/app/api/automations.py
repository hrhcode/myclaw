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
from app.services.conversation_service import ConversationService
from app.services.session_service import SessionService
from app.api.chat import agent_loop_controller

router = APIRouter()

automation_service = AutomationService()
conversation_service = ConversationService()
session_service = SessionService()


async def _resolve_automation_conversation(db: AsyncSession, conversation_id: int | None):
    if conversation_id is not None:
        conversation = await conversation_service.get_by_id(db, conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="conversation not found")
        return conversation
    conversations = await conversation_service.list_all(db, limit=1)
    if not conversations:
        raise HTTPException(status_code=400, detail="no conversation available for automation")
    return conversations[0]


@router.get("/automations", response_model=list[AutomationResponse])
async def list_automations(db: AsyncSession = Depends(get_db)):
    return await automation_service.list_all(db)


@router.get("/automations/stats", response_model=AutomationStatsResponse)
async def get_automation_stats(db: AsyncSession = Depends(get_db)):
    return await automation_service.get_stats(db)


@router.post("/automations", response_model=AutomationResponse)
async def create_automation(payload: AutomationCreate, db: AsyncSession = Depends(get_db)):
    conversation = await _resolve_automation_conversation(db, payload.conversation_id)
    runtime_session = await session_service.resolve_session(db, conversation.session_id)
    payload_data = payload.model_dump()
    payload_data["conversation_id"] = conversation.id
    payload_data["session_id"] = runtime_session.id
    try:
        return await automation_service.create(db, **payload_data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/automations/{automation_id}", response_model=AutomationResponse)
async def update_automation(automation_id: int, payload: AutomationUpdate, db: AsyncSession = Depends(get_db)):
    changes = payload.model_dump(exclude_unset=True)
    if "conversation_id" in changes:
        conversation = await _resolve_automation_conversation(db, changes["conversation_id"])
        runtime_session = await session_service.resolve_session(db, conversation.session_id)
        changes["conversation_id"] = conversation.id
        changes["session_id"] = runtime_session.id
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


@router.delete("/automations/{automation_id}/runs")
async def clear_automation_runs(automation_id: int, db: AsyncSession = Depends(get_db)):
    try:
        deleted_count = await automation_service.clear_runs(db, automation_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if deleted_count is None:
        raise HTTPException(status_code=404, detail="automation not found")
    return {"success": True, "deleted_count": deleted_count}


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
