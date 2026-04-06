"""
配置数据访问层
提供配置(Config)实体的数据库操作
"""
import logging
from typing import Iterable, List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.dao._utils import commit_or_flush
from app.models.models import Config

logger = logging.getLogger(__name__)


class ConfigDAO:
    """
    配置数据访问对象
    封装配置相关的数据库操作
    """

    @staticmethod
    async def get_by_key(db: AsyncSession, key: str) -> Optional[Config]:
        result = await db.execute(
            select(Config).where(Config.key == key)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_value(db: AsyncSession, key: str) -> Optional[str]:
        config = await ConfigDAO.get_by_key(db, key)
        return config.value if config else None

    @staticmethod
    async def create(
        db: AsyncSession,
        key: str,
        value: str,
        description: Optional[str] = None,
        *,
        commit: bool = True,
    ) -> Config:
        logger.debug(f"[DAO-Config] 创建配置，key: {key}")
        config = Config(key=key, value=value, description=description)
        db.add(config)
        await commit_or_flush(db, commit)
        await db.refresh(config)
        logger.info(f"[DAO-Config] 配置已创建，key: {key}")
        return config

    @staticmethod
    async def upsert(
        db: AsyncSession,
        key: str,
        value: str,
        description: Optional[str] = None,
        *,
        commit: bool = True,
    ) -> Config:
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

        await commit_or_flush(db, commit)
        await db.refresh(config)
        logger.info(f"[DAO-Config] 配置已保存，key: {key}")
        return config

    @staticmethod
    async def upsert_many(
        db: AsyncSession,
        items: Iterable[tuple[str, str, Optional[str]]],
        *,
        commit: bool = True,
    ) -> List[Config]:
        entries = [(key, value, description) for key, value, description in items]
        if not entries:
            return []

        keys = [key for key, _, _ in entries]
        result = await db.execute(select(Config).where(Config.key.in_(keys)))
        existing_map = {item.key: item for item in result.scalars().all()}

        saved: List[Config] = []
        for key, value, description in entries:
            config = existing_map.get(key)
            if config:
                config.value = value
                if description is not None:
                    config.description = description
            else:
                config = Config(key=key, value=value, description=description)
                db.add(config)
            saved.append(config)

        await commit_or_flush(db, commit)
        for config in saved:
            await db.refresh(config)
        return saved

    @staticmethod
    async def update(
        db: AsyncSession,
        key: str,
        value: str,
        description: Optional[str] = None,
        *,
        commit: bool = True,
    ) -> Optional[Config]:
        config = await ConfigDAO.get_by_key(db, key)
        if not config:
            logger.warning(f"[DAO-Config] 更新失败，配置不存在，key: {key}")
            return None

        config.value = value
        if description is not None:
            config.description = description

        await commit_or_flush(db, commit)
        await db.refresh(config)
        logger.info(f"[DAO-Config] 配置已更新，key: {key}")
        return config

    @staticmethod
    async def delete(db: AsyncSession, key: str, *, commit: bool = True) -> bool:
        config = await ConfigDAO.get_by_key(db, key)
        if not config:
            logger.warning(f"[DAO-Config] 删除失败，配置不存在，key: {key}")
            return False

        await db.delete(config)
        await commit_or_flush(db, commit)
        logger.info(f"[DAO-Config] 配置已删除，key: {key}")
        return True

    @staticmethod
    async def list_all(db: AsyncSession) -> List[Config]:
        result = await db.execute(
            select(Config).order_by(Config.key)
        )
        return list(result.scalars().all())

    @staticmethod
    async def exists(db: AsyncSession, key: str) -> bool:
        config = await ConfigDAO.get_by_key(db, key)
        return config is not None
