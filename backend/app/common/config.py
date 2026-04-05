"""
配置管理模块
提供配置的读取和写入功能，委托给 ConfigDAO 实现
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.dao.config_dao import ConfigDAO
from app.models.models import Config


async def get_config_value(db: AsyncSession, key: str) -> Optional[str]:
    """获取配置值，不存在返回 None"""
    return await ConfigDAO.get_value(db, key)


async def set_config_value(
    db: AsyncSession,
    key: str,
    value: str,
    description: Optional[str] = None
) -> Config:
    """设置配置值（upsert）"""
    return await ConfigDAO.upsert(db, key, value, description)
