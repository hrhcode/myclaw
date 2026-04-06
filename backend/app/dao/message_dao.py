"""
消息数据访问层
提供消息(Message)实体的数据库操作
"""
import logging
from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.dao._utils import commit_or_flush
from app.models.models import Message

logger = logging.getLogger(__name__)


class MessageDAO:
    """
    消息数据访问对象
    封装消息相关的数据库操作
    """

    @staticmethod
    async def create(
        db: AsyncSession,
        session_id: Optional[int],
        conversation_id: int,
        role: str,
        content: str,
        *,
        commit: bool = True,
    ) -> Message:
        logger.debug(f"[DAO-Message] 创建消息 - 会话ID: {conversation_id}, 角色: {role}")
        message = Message(
            session_id=session_id,
            conversation_id=conversation_id,
            role=role,
            content=content
        )
        db.add(message)
        await commit_or_flush(db, commit)
        await db.refresh(message)
        logger.info(f"[DAO-Message] 消息已创建，ID: {message.id}")
        return message

    @staticmethod
    async def get_by_id(db: AsyncSession, message_id: int) -> Optional[Message]:
        result = await db.execute(
            select(Message).where(Message.id == message_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_conversation_history(db: AsyncSession, conversation_id: int) -> List[Message]:
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        )
        return list(result.scalars().all())

    @staticmethod
    async def list_by_conversation(
        db: AsyncSession,
        conversation_id: int,
        limit: Optional[int] = None
    ) -> List[Message]:
        query = select(Message).where(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.desc())

        if limit:
            query = query.limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_recent_messages(
        db: AsyncSession,
        conversation_id: int,
        limit: int = 20
    ) -> List[Message]:
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def count_by_conversation(db: AsyncSession, conversation_id: int) -> int:
        from sqlalchemy import func
        result = await db.execute(
            select(func.count(Message.id))
            .where(Message.conversation_id == conversation_id)
        )
        return result.scalar() or 0

    @staticmethod
    async def delete(db: AsyncSession, message_id: int, *, commit: bool = True) -> bool:
        message = await MessageDAO.get_by_id(db, message_id)
        if not message:
            logger.warning(f"[DAO-Message] 删除失败，消息不存在，ID: {message_id}")
            return False

        await db.delete(message)
        await commit_or_flush(db, commit)
        logger.info(f"[DAO-Message] 消息已删除，ID: {message_id}")
        return True

    @staticmethod
    async def delete_by_conversation(db: AsyncSession, conversation_id: int, *, commit: bool = True) -> int:
        result = await db.execute(
            delete(Message).where(Message.conversation_id == conversation_id)
        )
        await commit_or_flush(db, commit)
        count = result.rowcount
        logger.info(f"[DAO-Message] 会话 {conversation_id} 的 {count} 条消息已删除")
        return count

    @staticmethod
    async def get_unembedded_messages(
        db: AsyncSession,
        conversation_id: int,
        limit: int = 100
    ) -> List[Message]:
        result = await db.execute(
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.embedding.is_(None)
            )
            .order_by(Message.created_at)
            .limit(limit)
        )
        return list(result.scalars().all())
