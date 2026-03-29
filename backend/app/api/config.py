"""
配置管理API
提供配置项查询和管理的HTTP接口
业务逻辑已委托给DAO层，API层仅处理HTTP请求/响应
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.dao.config_dao import ConfigDAO
from app.schemas.schemas import ConfigCreate, ConfigUpdate, ConfigResponse
from app.common.constants import (
    API_KEY_KEY,
    LLM_MODEL_KEY,
    LLM_PROVIDER_KEY,
    OPENROUTER_API_KEY_KEY,
    EMBEDDING_PROVIDER_KEY,
    EMBEDDING_MODEL_KEY,
    PROVIDERS,
    EMBEDDING_PROVIDERS,
)
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/config/providers")
async def get_providers():
    """
    获取所有LLM提供商列表
    """
    logger.info("获取LLM提供商列表")
    return [
        {"id": provider_id, "name": provider_info["name"]}
        for provider_id, provider_info in PROVIDERS.items()
    ]


@router.get("/config/providers/{provider}/models")
async def get_provider_models(provider: str):
    """
    获取指定提供商的模型列表
    """
    logger.info(f"获取提供商模型列表: {provider}")

    if provider not in PROVIDERS:
        raise HTTPException(status_code=404, detail=f"提供商 '{provider}' 不存在")

    return PROVIDERS[provider]["models"]


@router.get("/config/embedding-providers")
async def get_embedding_providers():
    """
    获取所有 Embedding 提供商列表
    """
    logger.info("获取 Embedding 提供商列表")
    return [
        {"id": provider_id, "name": provider_info["name"]}
        for provider_id, provider_info in EMBEDDING_PROVIDERS.items()
    ]


@router.get("/config/embedding-providers/{provider}/models")
async def get_embedding_provider_models(provider: str):
    """
    获取指定 Embedding 提供商的模型列表
    """
    logger.info(f"获取 Embedding 提供商模型列表: {provider}")

    if provider not in EMBEDDING_PROVIDERS:
        raise HTTPException(status_code=404, detail=f"Embedding 提供商 '{provider}' 不存在")

    return EMBEDDING_PROVIDERS[provider]["models"]


@router.get("/config/{key}", response_model=str)
async def get_config(key: str, db: AsyncSession = Depends(get_db)):
    """
    获取指定配置项的值
    """
    logger.info(f"获取配置: {key}")
    value = await ConfigDAO.get_value(db, key)
    if value is None:
        raise HTTPException(status_code=404, detail=f"配置项 '{key}' 不存在")
    return value


@router.put("/config/{key}", response_model=ConfigResponse)
async def update_config(
    key: str,
    config_update: ConfigUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    更新或创建配置项
    """
    logger.info(f"更新配置: {key}")
    config = await ConfigDAO.upsert(db, key, config_update.value, config_update.description)
    return config


@router.post("/config", response_model=ConfigResponse)
async def create_config(
    config_create: ConfigCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建新的配置项
    """
    logger.info(f"创建配置: {config_create.key}")
    existing = await ConfigDAO.exists(db, config_create.key)
    if existing:
        raise HTTPException(status_code=400, detail=f"配置项 '{config_create.key}' 已存在")

    config = await ConfigDAO.create(db, config_create.key, config_create.value, config_create.description)
    return config


@router.get("/config", response_model=list[ConfigResponse])
async def list_configs(db: AsyncSession = Depends(get_db)):
    """
    获取所有配置项
    """
    logger.info("获取所有配置")
    configs = await ConfigDAO.list_all(db)
    return configs


@router.delete("/config/{key}")
async def delete_config(key: str, db: AsyncSession = Depends(get_db)):
    """
    删除配置项
    """
    logger.info(f"删除配置: {key}")
    success = await ConfigDAO.delete(db, key)
    if not success:
        raise HTTPException(status_code=404, detail=f"配置项 '{key}' 不存在")
    return {"message": f"配置项 '{key}' 已删除"}
