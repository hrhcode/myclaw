from __future__ import annotations

from datetime import UTC, datetime
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Channel, ChannelChat


def _utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class ChannelDAO:
    @staticmethod
    async def list_all(db: AsyncSession) -> List[Channel]:
        result = await db.execute(select(Channel).order_by(Channel.created_at.desc()))
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(db: AsyncSession, channel_id: int) -> Optional[Channel]:
        return await db.get(Channel, channel_id)

    @staticmethod
    async def get_enabled(db: AsyncSession) -> List[Channel]:
        result = await db.execute(
            select(Channel).where(Channel.enabled.is_(True)).order_by(Channel.id.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def create(db: AsyncSession, **kwargs) -> Channel:
        channel = Channel(**kwargs)
        db.add(channel)
        await db.commit()
        await db.refresh(channel)
        return channel

    @staticmethod
    async def update(db: AsyncSession, channel: Channel, **changes) -> Channel:
        for key, value in changes.items():
            setattr(channel, key, value)
        await db.commit()
        await db.refresh(channel)
        return channel

    @staticmethod
    async def delete(db: AsyncSession, channel: Channel) -> None:
        await db.delete(channel)
        await db.commit()


class ChannelChatDAO:
    @staticmethod
    async def get_by_id(db: AsyncSession, chat_id: int) -> Optional[ChannelChat]:
        return await db.get(ChannelChat, chat_id)

    @staticmethod
    async def get_or_create(
        db: AsyncSession,
        channel_id: int,
        external_chat_id: str,
        external_chat_type: str,
    ) -> ChannelChat:
        result = await db.execute(
            select(ChannelChat).where(
                ChannelChat.channel_id == channel_id,
                ChannelChat.external_chat_id == external_chat_id,
            )
        )
        chat = result.scalars().first()
        if chat:
            return chat

        chat = ChannelChat(
            channel_id=channel_id,
            external_chat_id=external_chat_id,
            external_chat_type=external_chat_type,
        )
        db.add(chat)
        await db.commit()
        await db.refresh(chat)
        return chat

    @staticmethod
    async def list_by_channel(db: AsyncSession, channel_id: int) -> List[ChannelChat]:
        result = await db.execute(
            select(ChannelChat)
            .where(ChannelChat.channel_id == channel_id)
            .order_by(ChannelChat.last_message_at.desc().nullslast())
        )
        return list(result.scalars().all())

    @staticmethod
    async def update_conversation(
        db: AsyncSession, chat: ChannelChat, conversation_id: int
    ) -> ChannelChat:
        chat.conversation_id = conversation_id
        chat.last_message_at = _utc_now()
        await db.commit()
        await db.refresh(chat)
        return chat
