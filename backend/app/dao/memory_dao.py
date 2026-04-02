"""
长期记忆数据访问层
提供长期记忆(LongTermMemory)实体的数据库操作
"""
import logging
from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import LongTermMemory

logger = logging.getLogger(__name__)


class MemoryDAO:
    """
    长期记忆数据访问对象
    封装长期记忆相关的数据库操作
    """

    @staticmethod
    async def create(
        db: AsyncSession,
        content: str,
        session_id: Optional[int] = None,
        key: Optional[str] = None,
        importance: float = 0.5,
        source: Optional[str] = None
    ) -> LongTermMemory:
        """
        创建长期记忆

        Args:
            db: 数据库会话
            content: 记忆内容
            key: 记忆键名
            importance: 重要性 (0.0-1.0)
            source: 来源

        Returns:
            新创建的长期记忆对象
        """
        logger.debug(f"[DAO-Memory] 创建长期记忆，key: {key or '无'}")
        memory = LongTermMemory(
            session_id=session_id,
            key=key,
            content=content,
            importance=importance,
            source=source
        )
        db.add(memory)
        await db.commit()
        await db.refresh(memory)
        logger.info(f"[DAO-Memory] 长期记忆已创建，ID: {memory.id}")
        return memory

    @staticmethod
    async def get_by_id(db: AsyncSession, memory_id: int) -> Optional[LongTermMemory]:
        """
        根据ID获取长期记忆

        Args:
            db: 数据库会话
            memory_id: 记忆ID

        Returns:
            长期记忆对象，不存在返回None
        """
        result = await db.execute(
            select(LongTermMemory).where(LongTermMemory.id == memory_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_all(db: AsyncSession, limit: int = 50) -> List[LongTermMemory]:
        """
        获取所有长期记忆

        Args:
            db: 数据库会话
            limit: 返回数量限制

        Returns:
            长期记忆列表（按重要性和更新时间排序）
        """
        result = await db.execute(
            select(LongTermMemory)
            .order_by(LongTermMemory.importance.desc(), LongTermMemory.updated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def update(
        db: AsyncSession,
        memory_id: int,
        content: Optional[str] = None,
        key: Optional[str] = None,
        importance: Optional[float] = None,
        source: Optional[str] = None
    ) -> Optional[LongTermMemory]:
        """
        更新长期记忆

        Args:
            db: 数据库会话
            memory_id: 记忆ID
            content: 记忆内容
            key: 记忆键名
            importance: 重要性
            source: 来源

        Returns:
            更新后的长期记忆对象，不存在返回None
        """
        memory = await MemoryDAO.get_by_id(db, memory_id)
        if not memory:
            logger.warning(f"[DAO-Memory] 更新失败，记忆不存在，ID: {memory_id}")
            return None

        if content is not None:
            memory.content = content
        if key is not None:
            memory.key = key
        if importance is not None:
            memory.importance = importance
        if source is not None:
            memory.source = source

        await db.commit()
        await db.refresh(memory)
        logger.info(f"[DAO-Memory] 长期记忆已更新，ID: {memory_id}")
        return memory

    @staticmethod
    async def delete(db: AsyncSession, memory_id: int) -> bool:
        """
        删除长期记忆

        Args:
            db: 数据库会话
            memory_id: 记忆ID

        Returns:
            是否删除成功
        """
        memory = await MemoryDAO.get_by_id(db, memory_id)
        if not memory:
            logger.warning(f"[DAO-Memory] 删除失败，记忆不存在，ID: {memory_id}")
            return False

        await db.delete(memory)
        await db.commit()
        logger.info(f"[DAO-Memory] 长期记忆已删除，ID: {memory_id}")
        return True

    @staticmethod
    async def get_by_content_hash(db: AsyncSession, content_hash: str) -> Optional[LongTermMemory]:
        """
        根据内容哈希获取长期记忆

        Args:
            db: 数据库会话
            content_hash: 内容哈希

        Returns:
            长期记忆对象，不存在返回None
        """
        result = await db.execute(
            select(LongTermMemory).where(LongTermMemory.content_hash == content_hash)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def count(db: AsyncSession) -> int:
        """
        统计长期记忆数量

        Args:
            db: 数据库会话

        Returns:
            长期记忆数量
        """
        from sqlalchemy import func
        result = await db.execute(
            select(func.count(LongTermMemory.id))
        )
        return result.scalar() or 0

    @staticmethod
    async def list_by_importance(
        db: AsyncSession,
        min_importance: float = 0.0,
        limit: int = 50
    ) -> List[LongTermMemory]:
        """
        按重要性筛选长期记忆

        Args:
            db: 数据库会话
            min_importance: 最小重要性
            limit: 返回数量限制

        Returns:
            长期记忆列表
        """
        result = await db.execute(
            select(LongTermMemory)
            .where(LongTermMemory.importance >= min_importance)
            .order_by(LongTermMemory.importance.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
