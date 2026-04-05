from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dao.channel_dao import ChannelChatDAO, ChannelDAO
from app.schemas.schemas import (
    ChannelChatResponse,
    ChannelCreate,
    ChannelResponse,
    ChannelUpdate,
)

router = APIRouter()


def _channel_to_response(channel) -> ChannelResponse:
    import json

    config = json.loads(channel.config) if channel.config else {}
    return ChannelResponse(
        id=channel.id,
        name=channel.name,
        channel_type=channel.channel_type,
        enabled=channel.enabled,
        config=config,
        conversation_id=channel.conversation_id,
        status=channel.status,
        status_message=channel.status_message,
        last_event_at=channel.last_event_at,
        created_at=channel.created_at,
        updated_at=channel.updated_at,
    )


@router.get("/channels", response_model=list[ChannelResponse])
async def list_channels(db: AsyncSession = Depends(get_db)):
    channels = await ChannelDAO.list_all(db)
    return [_channel_to_response(c) for c in channels]


@router.post("/channels", response_model=ChannelResponse)
async def create_channel(payload: ChannelCreate, db: AsyncSession = Depends(get_db)):
    import json

    from app.channels.manager import channel_manager

    try:
        channel = await ChannelDAO.create(
            db,
            name=payload.name,
            channel_type=payload.channel_type,
            enabled=payload.enabled,
            config=json.dumps(payload.config, ensure_ascii=False),
            conversation_id=payload.conversation_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if payload.enabled:
        await channel_manager.start_channel(channel.id)

    return _channel_to_response(channel)


@router.get("/channels/{channel_id}", response_model=ChannelResponse)
async def get_channel(channel_id: int, db: AsyncSession = Depends(get_db)):
    channel = await ChannelDAO.get_by_id(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="channel not found")
    return _channel_to_response(channel)


@router.put("/channels/{channel_id}", response_model=ChannelResponse)
async def update_channel(
    channel_id: int,
    payload: ChannelUpdate,
    db: AsyncSession = Depends(get_db),
):
    import json

    from app.channels.manager import channel_manager

    channel = await ChannelDAO.get_by_id(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="channel not found")

    changes = payload.model_dump(exclude_unset=True)
    if "config" in changes and changes["config"] is not None:
        changes["config"] = json.dumps(changes["config"], ensure_ascii=False)

    try:
        channel = await ChannelDAO.update(db, channel, **changes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if "enabled" in changes:
        if changes["enabled"]:
            await channel_manager.restart_channel(channel_id)
        else:
            await channel_manager.stop_channel(channel_id)
    else:
        await channel_manager.restart_channel(channel_id)

    return _channel_to_response(channel)


@router.delete("/channels/{channel_id}")
async def delete_channel(channel_id: int, db: AsyncSession = Depends(get_db)):
    from app.channels.manager import channel_manager

    channel = await ChannelDAO.get_by_id(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="channel not found")

    await channel_manager.stop_channel(channel_id)
    await ChannelDAO.delete(db, channel)
    return {"success": True}


@router.post("/channels/{channel_id}/start", response_model=ChannelResponse)
async def start_channel_route(channel_id: int, db: AsyncSession = Depends(get_db)):
    from app.channels.manager import channel_manager

    channel = await ChannelDAO.get_by_id(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="channel not found")

    await channel_manager.start_channel(channel_id)
    channel = await ChannelDAO.get_by_id(db, channel_id)
    return _channel_to_response(channel)


@router.post("/channels/{channel_id}/stop", response_model=ChannelResponse)
async def stop_channel_route(channel_id: int, db: AsyncSession = Depends(get_db)):
    from app.channels.manager import channel_manager

    channel = await ChannelDAO.get_by_id(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="channel not found")

    await channel_manager.stop_channel(channel_id)
    channel = await ChannelDAO.get_by_id(db, channel_id)
    return _channel_to_response(channel)


@router.post("/channels/{channel_id}/restart", response_model=ChannelResponse)
async def restart_channel_route(channel_id: int, db: AsyncSession = Depends(get_db)):
    from app.channels.manager import channel_manager

    channel = await ChannelDAO.get_by_id(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="channel not found")

    await channel_manager.restart_channel(channel_id)
    channel = await ChannelDAO.get_by_id(db, channel_id)
    return _channel_to_response(channel)


@router.get("/channels/{channel_id}/chats", response_model=list[ChannelChatResponse])
async def list_channel_chats(channel_id: int, db: AsyncSession = Depends(get_db)):
    channel = await ChannelDAO.get_by_id(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="channel not found")

    chats = await ChannelChatDAO.list_by_channel(db, channel_id)
    return [
        ChannelChatResponse(
            id=chat.id,
            channel_id=chat.channel_id,
            external_chat_id=chat.external_chat_id,
            external_chat_type=chat.external_chat_type,
            conversation_id=chat.conversation_id,
            external_user_id=chat.external_user_id,
            external_user_name=chat.external_user_name,
            last_message_at=chat.last_message_at,
            created_at=chat.created_at,
        )
        for chat in chats
    ]
