from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dao.message_dao import MessageDAO
from app.schemas.schemas import (
    SessionCreate,
    SessionDispatchRequest,
    SessionHistorySummaryResponse,
    SessionResponse,
    SessionStatusResponse,
    SessionUpdate,
)
from app.services.conversation_service import ConversationService
from app.services.session_service import SessionService
from app.api.chat import agent_loop_controller

router = APIRouter()

session_service = SessionService()
conversation_service = ConversationService()


def _to_session_response(session) -> dict:
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
        "created_at": session.created_at,
        "updated_at": session.updated_at,
    }


@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(db: AsyncSession = Depends(get_db)):
    return [_to_session_response(session) for session in await session_service.list_all(db)]


@router.post("/sessions", response_model=SessionResponse)
async def create_session(payload: SessionCreate, db: AsyncSession = Depends(get_db)):
    try:
        session = await session_service.create(
            db,
            name=payload.name,
            mode=payload.mode,
            workspace_path=payload.workspace_path,
            model=payload.model,
            provider=payload.provider,
            tool_profile=payload.tool_profile,
            tool_allow=",".join(payload.tool_allow),
            tool_deny=",".join(payload.tool_deny),
            max_iterations=payload.max_iterations,
            context_summary=payload.context_summary,
            memory_auto_extract=payload.memory_auto_extract,
            memory_threshold=payload.memory_threshold,
            is_default=payload.is_default,
        )
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="session name already exists") from exc
    return _to_session_response(session)


@router.put("/sessions/{session_id}", response_model=SessionResponse)
async def update_session(session_id: int, payload: SessionUpdate, db: AsyncSession = Depends(get_db)):
    changes = payload.model_dump(exclude_unset=True)
    if "tool_allow" in changes:
        changes["tool_allow"] = ",".join(changes["tool_allow"] or [])
    if "tool_deny" in changes:
        changes["tool_deny"] = ",".join(changes["tool_deny"] or [])
    try:
        session = await session_service.update(db, session_id, **changes)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="session name already exists") from exc
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    return _to_session_response(session)


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await session_service.delete(db, session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="session not found")
    return {"success": True}


@router.get("/sessions/{session_id}/status", response_model=SessionStatusResponse)
async def get_session_status(session_id: int, db: AsyncSession = Depends(get_db)):
    status = await session_service.get_status(db, session_id)
    if not status:
        raise HTTPException(status_code=404, detail="session not found")
    return status


@router.get("/sessions/{session_id}/history-summary", response_model=SessionHistorySummaryResponse)
async def get_session_history_summary(session_id: int, db: AsyncSession = Depends(get_db)):
    conversations = await conversation_service.list_by_session(db, session_id, limit=3)
    if not conversations:
        session = await session_service.get_by_id(db, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="session not found")
        return {"session_id": session_id, "summary": "", "recent_messages": []}
    recent_messages: list[str] = []
    for conversation in conversations:
        messages = await MessageDAO.get_recent_messages(db, conversation.id, limit=6)
        recent_messages.extend([f"[{message.role}] {message.content}" for message in reversed(messages)])
    return {
        "session_id": session_id,
        "summary": "\n".join(recent_messages[-12:]),
        "recent_messages": recent_messages[-12:],
    }


@router.post("/sessions/{session_id}/dispatch")
async def dispatch_to_session(session_id: int, payload: SessionDispatchRequest, db: AsyncSession = Depends(get_db)):
    session = await session_service.get_by_id(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    result = await agent_loop_controller.dispatch_message(db, session_id, payload.message)
    return {"success": True, "session_id": session_id, "message": payload.message, "run_id": result.get("run_id")}
