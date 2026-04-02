"""
消息数据访问层
提供消息(Message)实体的数据库操作
"""
import logging
from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
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
        content: str
    ) -> Message:
        """
        创建新消息

        Args:
            db: 数据库会话
            conversation_id: 会话ID
            role: 角色 (user/assistant)
            content: 消息内容

        Returns:
            新创建的消息对象
        """
        logger.debug(f"[DAO-Message] 创建消息 - 会话ID: {conversation_id}, 角色: {role}")
        message = Message(
            session_id=session_id,
            conversation_id=conversation_id,
            role=role,
            content=content
        )
        db.add(message)
        await db.commit()
        await db.refresh(message)
        logger.info(f"[DAO-Message] 消息已创建，ID: {message.id}")
        return message

    @staticmethod
    async def get_by_id(db: AsyncSession, message_id: int) -> Optional[Message]:
        """
        根据ID获取消息

        Args:
            db: 数据库会话
            message_id: 消息ID

        Returns:
            消息对象，不存在返回None
        """
        result = await db.execute(
            select(Message).where(Message.id == message_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_conversation_history(db: AsyncSession, conversation_id: int) -> List[Message]:
        """
        获取会话的所有消息

        Args:
            db: 数据库会话
            conversation_id: 会话ID

        Returns:
            消息列表（按时间升序）
        """
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
        """
        获取会话的消息列表

        Args:
            db: 数据库会话
            conversation_id: 会话ID
            limit: 返回数量限制

        Returns:
            消息列表
        """
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
        """
        获取最近的消息

        Args:
            db: 数据库会话
            conversation_id: 会话ID
            limit: 返回消息数量

        Returns:
            最近的消息列表（降序）
        """
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def count_by_conversation(db: AsyncSession, conversation_id: int) -> int:
        """
        统计会话的消息数量

        Args:
            db: 数据库会话
            conversation_id: 会话ID

        Returns:
            消息数量
        """
        from sqlalchemy import func
        result = await db.execute(
            select(func.count(Message.id))
            .where(Message.conversation_id == conversation_id)
        )
        return result.scalar() or 0

    @staticmethod
    async def delete(db: AsyncSession, message_id: int) -> bool:
        """
        删除消息

        Args:
            db: 数据库会话
            message_id: 消息ID

        Returns:
            是否删除成功
        """
        message = await MessageDAO.get_by_id(db, message_id)
        if not message:
            logger.warning(f"[DAO-Message] 删除失败，消息不存在，ID: {message_id}")
            return False

        await db.delete(message)
        await db.commit()
        logger.info(f"[DAO-Message] 消息已删除，ID: {message_id}")
        return True

    @staticmethod
    async def delete_by_conversation(db: AsyncSession, conversation_id: int) -> int:
        """
        删除会话的所有消息

        Args:
            db: 数据库会话
            conversation_id: 会话ID

        Returns:
            删除的消息数量
        """
        result = await db.execute(
            delete(Message).where(Message.conversation_id == conversation_id)
        )
        await db.commit()
        count = result.rowcount
        logger.info(f"[DAO-Message] 会话 {conversation_id} 的 {count} 条消息已删除")
        return count

    @staticmethod
    async def get_unembedded_messages(
        db: AsyncSession,
        conversation_id: int,
        limit: int = 100
    ) -> List[Message]:
        """
        获取未生成向量嵌入的消息

        Args:
            db: 数据库会话
            conversation_id: 会话ID
            limit: 返回数量限制

        Returns:
            未嵌入的消息列表
        """
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
