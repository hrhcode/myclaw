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
from app.schemas.schemas import ConfigCreate, ConfigUpdate, ConfigResponse, WebSearchConfig, WebSearchConfigResponse, BrowserConfig, BrowserConfigResponse
from app.common.constants import (
    API_KEY_KEY,
    LLM_MODEL_KEY,
    LLM_PROVIDER_KEY,
    OPENROUTER_API_KEY_KEY,
    EMBEDDING_PROVIDER_KEY,
    EMBEDDING_MODEL_KEY,
    PROVIDERS,
    EMBEDDING_PROVIDERS,
    WEB_SEARCH_PROVIDER_KEY,
    TAVILY_API_KEY_KEY,
    WEB_SEARCH_MAX_RESULTS_KEY,
    WEB_SEARCH_DEPTH_KEY,
    WEB_SEARCH_INCLUDE_ANSWER_KEY,
    WEB_SEARCH_TIMEOUT_KEY,
    WEB_SEARCH_CACHE_TTL_KEY,
    BROWSER_DEFAULT_TYPE_KEY,
    BROWSER_HEADLESS_KEY,
    BROWSER_VIEWPORT_WIDTH_KEY,
    BROWSER_VIEWPORT_HEIGHT_KEY,
    BROWSER_TIMEOUT_MS_KEY,
    BROWSER_SSRF_ALLOW_PRIVATE_KEY,
    BROWSER_SSRF_WHITELIST_KEY,
    BROWSER_MAX_INSTANCES_KEY,
    BROWSER_IDLE_TIMEOUT_MS_KEY,
    BROWSER_USE_SYSTEM_BROWSER_KEY,
    BROWSER_SYSTEM_BROWSER_CHANNEL_KEY,
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


@router.get("/config/web-search", response_model=WebSearchConfigResponse)
async def get_web_search_config(db: AsyncSession = Depends(get_db)):
    """
    获取网络搜索配置
    """
    logger.info("获取网络搜索配置")

    provider = await ConfigDAO.get_value(db, WEB_SEARCH_PROVIDER_KEY)
    tavily_key = await ConfigDAO.get_value(db, TAVILY_API_KEY_KEY)
    max_results_str = await ConfigDAO.get_value(db, WEB_SEARCH_MAX_RESULTS_KEY)
    search_depth = await ConfigDAO.get_value(db, WEB_SEARCH_DEPTH_KEY)
    include_answer_str = await ConfigDAO.get_value(db, WEB_SEARCH_INCLUDE_ANSWER_KEY)
    timeout_str = await ConfigDAO.get_value(db, WEB_SEARCH_TIMEOUT_KEY)
    cache_ttl_str = await ConfigDAO.get_value(db, WEB_SEARCH_CACHE_TTL_KEY)

    return WebSearchConfigResponse(
        provider=provider or "tavily",
        tavily_api_key=tavily_key,
        max_results=int(max_results_str) if max_results_str else 5,
        search_depth=search_depth or "basic",
        include_answer=include_answer_str.lower() == "true" if include_answer_str else True,
        timeout_seconds=int(timeout_str) if timeout_str else 30,
        cache_ttl_minutes=int(cache_ttl_str) if cache_ttl_str else 15
    )


@router.put("/config/web-search")
async def update_web_search_config(
    config: WebSearchConfig,
    db: AsyncSession = Depends(get_db)
):
    """
    更新网络搜索配置
    """
    logger.info("更新网络搜索配置")

    await ConfigDAO.upsert(db, WEB_SEARCH_PROVIDER_KEY, config.provider, "搜索引擎提供商")
    if config.tavily_api_key:
        await ConfigDAO.upsert(db, TAVILY_API_KEY_KEY, config.tavily_api_key, "Tavily API Key")
    await ConfigDAO.upsert(db, WEB_SEARCH_MAX_RESULTS_KEY, str(config.max_results), "最大搜索结果数")
    await ConfigDAO.upsert(db, WEB_SEARCH_DEPTH_KEY, config.search_depth, "搜索深度")
    await ConfigDAO.upsert(db, WEB_SEARCH_INCLUDE_ANSWER_KEY, str(config.include_answer).lower(), "是否包含AI答案")
    await ConfigDAO.upsert(db, WEB_SEARCH_TIMEOUT_KEY, str(config.timeout_seconds), "搜索超时时间")
    await ConfigDAO.upsert(db, WEB_SEARCH_CACHE_TTL_KEY, str(config.cache_ttl_minutes), "缓存过期时间")
    return {"message": "网络搜索配置已更新"}


@router.get("/config/browser", response_model=BrowserConfigResponse)
async def get_browser_config(db: AsyncSession = Depends(get_db)):
    """
    获取浏览器配置
    """
    logger.info("获取浏览器配置")
    
    default_type = await ConfigDAO.get_value(db, BROWSER_DEFAULT_TYPE_KEY)
    headless_str = await ConfigDAO.get_value(db, BROWSER_HEADLESS_KEY)
    viewport_width_str = await ConfigDAO.get_value(db, BROWSER_VIEWPORT_WIDTH_KEY)
    viewport_height_str = await ConfigDAO.get_value(db, BROWSER_VIEWPORT_HEIGHT_KEY)
    timeout_ms_str = await ConfigDAO.get_value(db, BROWSER_TIMEOUT_MS_KEY)
    ssrf_allow_private_str = await ConfigDAO.get_value(db, BROWSER_SSRF_ALLOW_PRIVATE_KEY)
    ssrf_whitelist = await ConfigDAO.get_value(db, BROWSER_SSRF_WHITELIST_KEY)
    max_instances_str = await ConfigDAO.get_value(db, BROWSER_MAX_INSTANCES_KEY)
    idle_timeout_ms_str = await ConfigDAO.get_value(db, BROWSER_IDLE_TIMEOUT_MS_KEY)
    use_system_browser_str = await ConfigDAO.get_value(db, "browser_use_system_browser")
    system_browser_channel = await ConfigDAO.get_value(db, "browser_system_browser_channel")
    
    return BrowserConfigResponse(
        default_type=default_type or "chromium",
        headless=headless_str.lower() == "true" if headless_str else False,
        viewport_width=int(viewport_width_str) if viewport_width_str else 1280,
        viewport_height=int(viewport_height_str) if viewport_height_str else 720,
        timeout_ms=int(timeout_ms_str) if timeout_ms_str else 30000,
        ssrf_allow_private=ssrf_allow_private_str.lower() == "true" if ssrf_allow_private_str else False,
        ssrf_whitelist=ssrf_whitelist or "",
        max_instances=int(max_instances_str) if max_instances_str else 1,
        idle_timeout_ms=int(idle_timeout_ms_str) if idle_timeout_ms_str else 300000,
        use_system_browser=use_system_browser_str.lower() == "true" if use_system_browser_str else True,
        system_browser_channel=system_browser_channel or "chrome"
    )


@router.put("/config/browser")
async def update_browser_config(
    config: BrowserConfig,
    db: AsyncSession = Depends(get_db)
):
    """
    更新浏览器配置
    """
    logger.info("更新浏览器配置")
    
    await ConfigDAO.upsert(db, BROWSER_DEFAULT_TYPE_KEY, config.default_type, "默认浏览器类型")
    await ConfigDAO.upsert(db, BROWSER_HEADLESS_KEY, str(config.headless).lower(), "是否无头模式")
    await ConfigDAO.upsert(db, BROWSER_VIEWPORT_WIDTH_KEY, str(config.viewport_width), "视口宽度")
    await ConfigDAO.upsert(db, BROWSER_VIEWPORT_HEIGHT_KEY, str(config.viewport_height), "视口高度")
    await ConfigDAO.upsert(db, BROWSER_TIMEOUT_MS_KEY, str(config.timeout_ms), "超时时间（毫秒）")
    await ConfigDAO.upsert(db, BROWSER_SSRF_ALLOW_PRIVATE_KEY, str(config.ssrf_allow_private).lower(), "是否允许访问内网")
    await ConfigDAO.upsert(db, BROWSER_SSRF_WHITELIST_KEY, config.ssrf_whitelist, "URL 白名单")
    await ConfigDAO.upsert(db, BROWSER_MAX_INSTANCES_KEY, str(config.max_instances), "最大浏览器实例数")
    await ConfigDAO.upsert(db, BROWSER_IDLE_TIMEOUT_MS_KEY, str(config.idle_timeout_ms), "空闲超时时间（毫秒）")
    await ConfigDAO.upsert(db, "browser_use_system_browser", str(config.use_system_browser).lower(), "是否使用系统浏览器")
    await ConfigDAO.upsert(db, "browser_system_browser_channel", config.system_browser_channel, "系统浏览器 channel")

    return {"message": "浏览器配置已更新"}


@router.get("/config", response_model=list[ConfigResponse])
async def list_configs(db: AsyncSession = Depends(get_db)):
    """
    获取所有配置项
    """
    logger.info("获取所有配置")
    configs = await ConfigDAO.list_all(db)
    return configs


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
