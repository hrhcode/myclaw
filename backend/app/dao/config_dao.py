"""
配置数据访问层
提供配置(Config)实体的数据库操作
"""
import logging
from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import Config

logger = logging.getLogger(__name__)


class ConfigDAO:
    """
    配置数据访问对象
    封装配置相关的数据库操作
    """

    @staticmethod
    async def get_by_key(db: AsyncSession, key: str) -> Optional[Config]:
        """
        根据key获取配置

        Args:
            db: 数据库会话
            key: 配置键

        Returns:
            配置对象，不存在返回None
        """
        result = await db.execute(
            select(Config).where(Config.key == key)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_value(db: AsyncSession, key: str) -> Optional[str]:
        """
        获取配置值

        Args:
            db: 数据库会话
            key: 配置键

        Returns:
            配置值，不存在返回None
        """
        config = await ConfigDAO.get_by_key(db, key)
        return config.value if config else None

    @staticmethod
    async def create(
        db: AsyncSession,
        key: str,
        value: str,
        description: Optional[str] = None
    ) -> Config:
        """
        创建新配置

        Args:
            db: 数据库会话
            key: 配置键
            value: 配置值
            description: 配置描述

        Returns:
            新创建的配置对象
        """
        logger.debug(f"[DAO-Config] 创建配置，key: {key}")
        config = Config(key=key, value=value, description=description)
        db.add(config)
        await db.commit()
        await db.refresh(config)
        logger.info(f"[DAO-Config] 配置已创建，key: {key}")
        return config

    @staticmethod
    async def upsert(
        db: AsyncSession,
        key: str,
        value: str,
        description: Optional[str] = None
    ) -> Config:
        """
        更新或创建配置

        Args:
            db: 数据库会话
            key: 配置键
            value: 配置值
            description: 配置描述

        Returns:
            配置对象
        """
        config = await ConfigDAO.get_by_key(db, key)

        if config:
            config.value = value
            if description is not None:
                config.description = description
            logger.debug(f"[DAO-Config] 更新配置，key: {key}")
        else:
            config = Config(key=key, value=value, description=description)
            db.add(config)
            logger.debug(f"[DAO-Config] 创建配置，key: {key}")

        await db.commit()
        await db.refresh(config)
        logger.info(f"[DAO-Config] 配置已保存，key: {key}")
        return config

    @staticmethod
    async def update(
        db: AsyncSession,
        key: str,
        value: str,
        description: Optional[str] = None
    ) -> Optional[Config]:
        """
        更新配置（仅当配置存在时）

        Args:
            db: 数据库会话
            key: 配置键
            value: 配置值
            description: 配置描述

        Returns:
            更新后的配置对象，不存在返回None
        """
        config = await ConfigDAO.get_by_key(db, key)
        if not config:
            logger.warning(f"[DAO-Config] 更新失败，配置不存在，key: {key}")
            return None

        config.value = value
        if description is not None:
            config.description = description

        await db.commit()
        await db.refresh(config)
        logger.info(f"[DAO-Config] 配置已更新，key: {key}")
        return config

    @staticmethod
    async def delete(db: AsyncSession, key: str) -> bool:
        """
        删除配置

        Args:
            db: 数据库会话
            key: 配置键

        Returns:
            是否删除成功
        """
        config = await ConfigDAO.get_by_key(db, key)
        if not config:
            logger.warning(f"[DAO-Config] 删除失败，配置不存在，key: {key}")
            return False

        await db.delete(config)
        await db.commit()
        logger.info(f"[DAO-Config] 配置已删除，key: {key}")
        return True

    @staticmethod
    async def list_all(db: AsyncSession) -> List[Config]:
        """
        获取所有配置

        Args:
            db: 数据库会话

        Returns:
            配置列表
        """
        result = await db.execute(
            select(Config).order_by(Config.key)
        )
        return list(result.scalars().all())

    @staticmethod
    async def exists(db: AsyncSession, key: str) -> bool:
        """
        检查配置是否存在

        Args:
            db: 数据库会话
            key: 配置键

        Returns:
            是否存在
        """
        config = await ConfigDAO.get_by_key(db, key)
        return config is not None
