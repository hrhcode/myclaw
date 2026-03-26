from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Config
from app.schemas import ConfigCreate, ConfigUpdate, ConfigResponse
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

API_KEY_KEY = "zhipu_api_key"
LLM_MODEL_KEY = "llm_model"
LLM_PROVIDER_KEY = "llm_provider"

PROVIDERS = {
    "zhipu": {
        "name": "智谱AI",
        "models": [
            {"id": "glm-4-flash", "name": "GLM-4-Flash (快速响应)"},
            {"id": "glm-4", "name": "GLM-4 (高性能)"},
            {"id": "glm-4-plus", "name": "GLM-4-Plus (旗舰)"},
        ]
    }
}


async def get_config_value(db: AsyncSession, key: str) -> str | None:
    """获取配置值"""
    result = await db.execute(select(Config).where(Config.key == key))
    config = result.scalar_one_or_none()
    return config.value if config else None


async def set_config_value(db: AsyncSession, key: str, value: str, description: str | None = None) -> Config:
    """设置配置值"""
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


@router.get("/config/{key}", response_model=str)
async def get_config(key: str, db: AsyncSession = Depends(get_db)):
    """
    获取指定配置项的值
    """
    logger.info(f"获取配置: {key}")
    value = await get_config_value(db, key)
    if value is None:
        raise HTTPException(status_code=404, detail=f"配置项 '{key}' 不存在")
    return value


@router.put("/config/{key}", response_model=ConfigResponse)
async def update_config(key: str, config_update: ConfigUpdate, db: AsyncSession = Depends(get_db)):
    """
    更新或创建配置项
    """
    logger.info(f"更新配置: {key}")
    config = await set_config_value(db, key, config_update.value, config_update.description)
    return config


@router.post("/config", response_model=ConfigResponse)
async def create_config(config_create: ConfigCreate, db: AsyncSession = Depends(get_db)):
    """
    创建新的配置项
    """
    logger.info(f"创建配置: {config_create.key}")
    existing = await get_config_value(db, config_create.key)
    if existing is not None:
        raise HTTPException(status_code=400, detail=f"配置项 '{config_create.key}' 已存在")

    config = await set_config_value(db, config_create.key, config_create.value, config_create.description)
    return config


@router.get("/config", response_model=list[ConfigResponse])
async def list_configs(db: AsyncSession = Depends(get_db)):
    """
    获取所有配置项
    """
    logger.info("获取所有配置")
    result = await db.execute(select(Config).order_by(Config.key))
    configs = result.scalars().all()
    return configs


@router.delete("/config/{key}")
async def delete_config(key: str, db: AsyncSession = Depends(get_db)):
    """
    删除配置项
    """
    logger.info(f"删除配置: {key}")
    result = await db.execute(select(Config).where(Config.key == key))
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail=f"配置项 '{key}' 不存在")

    await db.delete(config)
    await db.commit()
    return {"message": f"配置项 '{key}' 已删除"}