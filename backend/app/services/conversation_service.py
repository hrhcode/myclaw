"""
会话服务层
提供会话领域的业务逻辑处理
"""
import logging
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import Conversation
from app.dao.conversation_dao import ConversationDAO
from app.dao.message_dao import MessageDAO

logger = logging.getLogger(__name__)


class ConversationService:
    """
    会话服务
    处理会话相关的业务逻辑
    """

    async def get_or_create(
        self,
        db: AsyncSession,
        message: str,
        conversation_id: Optional[int] = None
    ) -> Tuple[int, Conversation]:
        """
        获取或创建会话

        Args:
            db: 数据库会话
            message: 用户消息（用于生成新会话标题）
            conversation_id: 会话ID（None表示创建新会话）

        Returns:
            tuple: (conversation_id, conversation对象)

        Raises:
            ValueError: 会话不存在时
        """
        if conversation_id:
            conversation = await ConversationDAO.get_by_id(db, conversation_id)
            if not conversation:
                logger.error(f"[ConversationService] 会话不存在，ID: {conversation_id}")
                raise ValueError("会话不存在")
            logger.debug(f"[ConversationService] 获取现有会话，ID: {conversation_id}")
            return conversation_id, conversation
        else:
            title = message[:20] + "..." if len(message) > 20 else message
            logger.info(f"[ConversationService] 创建新会话，标题: {title}")
            conversation = await ConversationDAO.create(db, title)
            return conversation.id, conversation

    async def get_by_id(
        self,
        db: AsyncSession,
        conversation_id: int
    ) -> Optional[Conversation]:
        """
        获取会话

        Args:
            db: 数据库会话
            conversation_id: 会话ID

        Returns:
            会话对象，不存在返回None
        """
        return await ConversationDAO.get_by_id(db, conversation_id)

    async def list_all(
        self,
        db: AsyncSession,
        limit: int = 50
    ) -> List[Conversation]:
        """
        获取所有会话

        Args:
            db: 数据库会话
            limit: 返回数量限制

        Returns:
            会话列表
        """
        return await ConversationDAO.list_all(db, limit)

    async def rename(
        self,
        db: AsyncSession,
        conversation_id: int,
        new_title: str
    ) -> Optional[Conversation]:
        """
        重命名会话

        Args:
            db: 数据库会话
            conversation_id: 会话ID
            new_title: 新标题

        Returns:
            更新后的会话对象，不存在返回None
        """
        return await ConversationDAO.update_title(db, conversation_id, new_title)

    async def delete(
        self,
        db: AsyncSession,
        conversation_id: int
    ) -> bool:
        """
        删除会话

        Args:
            db: 数据库会话
            conversation_id: 会话ID

        Returns:
            是否删除成功
        """
        return await ConversationDAO.delete(db, conversation_id)

    async def exists(
        self,
        db: AsyncSession,
        conversation_id: int
    ) -> bool:
        """
        检查会话是否存在

        Args:
            db: 数据库会话
            conversation_id: 会话ID

        Returns:
            是否存在
        """
        return await ConversationDAO.exists(db, conversation_id)
