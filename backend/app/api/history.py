from __future__ import annotations

from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dao.agent_event_dao import AgentEventDAO
from app.dao.conversation_dao import ConversationDAO
from app.dao.message_dao import MessageDAO
from app.dao.tool_call_dao import ToolCallDAO
from app.models.models import Message
from app.schemas.schemas import (
    AgentEventInMessage,
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
    MessageResponse,
    ToolCallInMessage,
)

router = APIRouter()


@router.get("/conversations", response_model=list[ConversationResponse])
async def get_conversations(
    session_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    if session_id is not None:
        return await ConversationDAO.list_by_session(db, session_id)
    return await ConversationDAO.list_all(db)


@router.get("/conversations/stats")
async def get_conversation_stats(
    session_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    conversations = (
        await ConversationDAO.list_by_session(db, session_id)
        if session_id is not None
        else await ConversationDAO.list_all(db)
    )
    conversation_ids = [item.id for item in conversations]
    if not conversation_ids:
        return []

    result = await db.execute(
        select(Message)
        .where(Message.conversation_id.in_(conversation_ids))
        .order_by(Message.conversation_id, Message.created_at)
    )
    grouped: dict[int, list[Message]] = defaultdict(list)
    for message in result.scalars().all():
        grouped[message.conversation_id].append(message)

    response = []
    for conversation in conversations:
        messages = grouped.get(conversation.id, [])
        last_message = messages[-1] if messages else None
        response.append(
            {
                "conversation_id": conversation.id,
                "message_count": len(messages),
                "last_message_id": last_message.id if last_message else None,
                "last_message_content": last_message.content if last_message else None,
                "last_message_created_at": (
                    last_message.created_at.isoformat() if last_message else None
                ),
            }
        )
    return response


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    conversation: ConversationCreate,
    db: AsyncSession = Depends(get_db),
):
    return await ConversationDAO.create(
        db,
        conversation.title,
        session_id=conversation.session_id,
    )


@router.put("/conversations/{conversation_id}", response_model=ConversationResponse)
async def rename_conversation(
    conversation_id: int,
    data: ConversationUpdate,
    db: AsyncSession = Depends(get_db),
):
    conversation = await ConversationDAO.update_title(db, conversation_id, data.title)
    if not conversation:
        raise HTTPException(status_code=404, detail="conversation not found")
    return conversation


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
):
    conversations = await ConversationDAO.list_all(db)
    if len(conversations) <= 1:
        raise HTTPException(
            status_code=400,
            detail="cannot delete the last conversation",
        )

    deleted = await ConversationDAO.delete(db, conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="conversation not found")
    return {"message": "conversation deleted"}


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_conversation_messages(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
):
    conversation = await ConversationDAO.get_by_id(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="conversation not found")

    messages = await MessageDAO.get_conversation_history(db, conversation_id)
    assistant_message_ids = [message.id for message in messages if message.role == "assistant"]
    tool_call_records = await ToolCallDAO.list_by_message_ids(db, assistant_message_ids)
    agent_event_records = await AgentEventDAO.list_by_message_ids(db, assistant_message_ids)

    tool_call_map: dict[int, list] = defaultdict(list)
    for item in tool_call_records:
        tool_call_map[item.message_id].append(item)

    agent_event_map: dict[int, list] = defaultdict(list)
    for item in agent_event_records:
        agent_event_map[item.message_id].append(item)

    response_messages: list[MessageResponse] = []
    for message in messages:
        tool_calls = []
        agent_events = []
        if message.role == "assistant":
            tool_calls = [
                ToolCallInMessage(
                    id=tc.id,
                    tool_name=tc.tool_name,
                    tool_call_id=tc.tool_call_id,
                    arguments=tc.arguments,
                    result=tc.result,
                    status=tc.status,
                    error=tc.error,
                    execution_time_ms=tc.execution_time_ms,
                    created_at=tc.created_at,
                    completed_at=tc.completed_at,
                )
                for tc in tool_call_map[message.id]
            ]
            agent_events = [
                AgentEventInMessage(
                    id=event.id,
                    run_id=event.run_id,
                    event_type=event.event_type,
                    payload=event.payload,
                    sequence=event.sequence,
                    created_at=event.created_at,
                )
                for event in agent_event_map[message.id]
            ]

        response_messages.append(
            MessageResponse(
                id=message.id,
                session_id=message.session_id,
                conversation_id=message.conversation_id,
                role=message.role,
                content=message.content,
                created_at=message.created_at,
                tool_calls=tool_calls,
                agent_events=agent_events,
            )
        )

    return response_messages
