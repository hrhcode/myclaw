"""
会话数据访问层
提供会话(Conversation)实体的数据库操作
"""
import logging
from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import Conversation, Message, ToolCall

logger = logging.getLogger(__name__)


class ConversationDAO:
    """
    会话数据访问对象
    封装会话相关的数据库操作
    """

    @staticmethod
    async def create(db: AsyncSession, title: str) -> Conversation:
        """
        创建新会话

        Args:
            db: 数据库会话
            title: 会话标题

        Returns:
            新创建的会话对象
        """
        logger.debug(f"[DAO-Conversation] 创建会话，标题: {title[:20]}...")
        conversation = Conversation(title=title)
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        logger.info(f"[DAO-Conversation] 会话已创建，ID: {conversation.id}")
        return conversation

    @staticmethod
    async def get_by_id(db: AsyncSession, conversation_id: int) -> Optional[Conversation]:
        """
        根据ID获取会话

        Args:
            db: 数据库会话
            conversation_id: 会话ID

        Returns:
            会话对象，不存在返回None
        """
        result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_all(db: AsyncSession, limit: int = 50) -> List[Conversation]:
        """
        获取所有会话列表

        Args:
            db: 数据库会话
            limit: 返回数量限制

        Returns:
            会话列表
        """
        result = await db.execute(
            select(Conversation)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def update_title(db: AsyncSession, conversation_id: int, title: str) -> Optional[Conversation]:
        """
        更新会话标题

        Args:
            db: 数据库会话
            conversation_id: 会话ID
            title: 新标题

        Returns:
            更新后的会话对象，不存在返回None
        """
        conversation = await ConversationDAO.get_by_id(db, conversation_id)
        if not conversation:
            logger.warning(f"[DAO-Conversation] 更新失败，会话不存在，ID: {conversation_id}")
            return None

        conversation.title = title
        await db.commit()
        await db.refresh(conversation)
        logger.info(f"[DAO-Conversation] 会话标题已更新，ID: {conversation_id}")
        return conversation

    @staticmethod
    async def delete(db: AsyncSession, conversation_id: int) -> bool:
        """
        删除会话及其所有消息和工具调用记录

        Args:
            db: 数据库会话
            conversation_id: 会话ID

        Returns:
            是否删除成功
        """
        conversation = await ConversationDAO.get_by_id(db, conversation_id)
        if not conversation:
            logger.warning(f"[DAO-Conversation] 删除失败，会话不存在，ID: {conversation_id}")
            return False

        await db.execute(
            delete(ToolCall).where(ToolCall.conversation_id == conversation_id)
        )
        await db.execute(
            delete(Message).where(Message.conversation_id == conversation_id)
        )
        await db.delete(conversation)
        await db.commit()
        logger.info(f"[DAO-Conversation] 会话已删除，ID: {conversation_id}（包含消息和工具调用记录）")
        return True

    @staticmethod
    async def exists(db: AsyncSession, conversation_id: int) -> bool:
        """
        检查会话是否存在

        Args:
            db: 数据库会话
            conversation_id: 会话ID

        Returns:
            是否存在
        """
        conversation = await ConversationDAO.get_by_id(db, conversation_id)
        return conversation is not None
