from __future__ import annotations

import json
from typing import Any, Awaitable, Callable, Optional

from app.dao.conversation_dao import ConversationDAO
from app.dao.message_dao import MessageDAO
from app.dao.session_dao import SessionDAO
from app.services.session_service import SessionService
from app.tools.base import ToolDefinition, create_tool

_session_factory = None
_dispatcher: Optional[Callable[[int, str], Awaitable[dict[str, Any]]]] = None


def configure_session_tools(session_factory, dispatcher: Callable[[int, str], Awaitable[dict[str, Any]]]) -> None:
    global _session_factory, _dispatcher
    _session_factory = session_factory
    _dispatcher = dispatcher


async def _sessions_list(_db=None) -> dict[str, Any]:
    if _db is not None:
        sessions = await SessionService().list_all(_db)
        return {
            "success": True,
            "content": [
                {
                    "id": session.id,
                    "name": session.name,
                    "workspace_path": session.workspace_path,
                    "model": session.model,
                    "provider": session.provider,
                    "tool_profile": session.tool_profile,
                    "is_default": session.is_default,
                }
                for session in sessions
            ],
        }
    if _session_factory is None:
        return {"success": False, "error": "session runtime unavailable"}
    async with _session_factory() as db:
        sessions = await SessionService().list_all(db)
        return {
            "success": True,
            "content": [
                {
                    "id": session.id,
                    "name": session.name,
                    "workspace_path": session.workspace_path,
                    "model": session.model,
                    "provider": session.provider,
                    "tool_profile": session.tool_profile,
                    "is_default": session.is_default,
                }
                for session in sessions
            ],
        }


async def _session_status(session_id: int, _db=None) -> dict[str, Any]:
    if _db is not None:
        status = await SessionService().get_status(_db, session_id)
        if not status:
            return {"success": False, "error": f"session {session_id} not found"}
        return {"success": True, "content": status}
    if _session_factory is None:
        return {"success": False, "error": "session runtime unavailable"}
    async with _session_factory() as db:
        status = await SessionService().get_status(db, session_id)
        if not status:
            return {"success": False, "error": f"session {session_id} not found"}
        return {"success": True, "content": status}


async def _sessions_history(session_id: int, limit: int = 12, _db=None) -> dict[str, Any]:
    if _db is not None:
        conversations = await ConversationDAO.list_by_session(_db, session_id, limit=3)
        messages: list[str] = []
        for conversation in conversations:
            history = await MessageDAO.get_recent_messages(_db, conversation.id, limit=limit)
            messages.extend([f"[{message.role}] {message.content}" for message in reversed(history)])
        return {"success": True, "content": {"session_id": session_id, "summary": "\n".join(messages[-limit:]), "messages": messages[-limit:]}}
    if _session_factory is None:
        return {"success": False, "error": "session runtime unavailable"}
    async with _session_factory() as db:
        conversations = await ConversationDAO.list_by_session(db, session_id, limit=3)
        messages: list[str] = []
        for conversation in conversations:
            history = await MessageDAO.get_recent_messages(db, conversation.id, limit=limit)
            messages.extend([f"[{message.role}] {message.content}" for message in reversed(history)])
        summary = "\n".join(messages[-limit:])
        return {"success": True, "content": {"session_id": session_id, "summary": summary, "messages": messages[-limit:]}}


async def _sessions_send(session_id: int, message: str, _db=None) -> dict[str, Any]:
    if _dispatcher is None:
        return {"success": False, "error": "session dispatcher unavailable"}
    result = await _dispatcher(session_id, message)
    return {"success": True, "content": result}


def get_session_tools() -> list[ToolDefinition]:
    return [
        create_tool(
            name="sessions_list",
            description="List available personal sessions and their high level configuration.",
            parameters={"type": "object", "properties": {}, "required": []},
            execute=lambda **kwargs: _sessions_list(kwargs.get("_db")),
        ),
        create_tool(
            name="session_status",
            description="Get the current status and recent runs for a session.",
            parameters={
                "type": "object",
                "properties": {"session_id": {"type": "integer", "description": "Target session id"}},
                "required": ["session_id"],
            },
            execute=lambda **kwargs: _session_status(kwargs["session_id"], kwargs.get("_db")),
        ),
        create_tool(
            name="sessions_history",
            description="Fetch a compact summary of recent conversation history for another session.",
            parameters={
                "type": "object",
                "properties": {
                    "session_id": {"type": "integer", "description": "Target session id"},
                    "limit": {"type": "integer", "description": "Maximum summary lines", "default": 12},
                },
                "required": ["session_id"],
            },
            execute=lambda **kwargs: _sessions_history(kwargs["session_id"], kwargs.get("limit", 12), kwargs.get("_db")),
        ),
        create_tool(
            name="sessions_send",
            description="Send a task to another session and trigger a run there.",
            parameters={
                "type": "object",
                "properties": {
                    "session_id": {"type": "integer", "description": "Target session id"},
                    "message": {"type": "string", "description": "Message to dispatch"},
                },
                "required": ["session_id", "message"],
            },
            execute=lambda **kwargs: _sessions_send(kwargs["session_id"], kwargs["message"], kwargs.get("_db")),
        ),
    ]
