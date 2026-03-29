"""
配置管理模块
提供配置的读取和写入功能
"""
import logging
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import Config

logger = logging.getLogger(__name__)


async def get_config_value(db: AsyncSession, key: str) -> Optional[str]:
    """
    获取配置值
    
    Args:
        db: 数据库会话
        key: 配置键
        
    Returns:
        配置值，不存在返回 None
    """
    result = await db.execute(select(Config).where(Config.key == key))
    config = result.scalar_one_or_none()
    return config.value if config else None


async def set_config_value(
    db: AsyncSession,
    key: str,
    value: str,
    description: Optional[str] = None
) -> Config:
    """
    设置配置值
    
    Args:
        db: 数据库会话
        key: 配置键
        value: 配置值
        description: 配置描述（可选）
        
    Returns:
        配置对象
    """
    result = await db.execute(select(Config).where(Config.key == key))
    config = result.scalar_one_or_none()

    if config:
        config.value = value
        if description is not None:
            config.description = description
    else:
        config = Config(key=key, value=value, description=description)
        db.add(config)

    await db.commit()
    await db.refresh(config)
    return config
