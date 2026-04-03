"""
工具管理 API

提供工具列表查询、配置管理等功能
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.models import Config
from app.schemas.schemas import ToolInfo, ToolListResponse, ToolConfigRequest, ToolConfigResponse
from app.tools import tool_registry
from app.common.config import get_config_value, set_config_value
from app.common.constants import TOOL_ENABLED_PREFIX
from typing import List
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/tools", response_model=ToolListResponse)
async def list_tools():
    """
    获取所有工具列表
    
    Returns:
        工具列表
    """
    tools = tool_registry.list_tools()
    
    tool_infos = [
        ToolInfo(
            name=tool.name,
            description=tool.description,
            enabled=tool.enabled,
            parameters=tool.parameters
        )
        for tool in tools
    ]
    
    return ToolListResponse(
        tools=tool_infos,
        total=len(tool_infos)
    )


@router.get("/tools/config", response_model=ToolConfigResponse)
async def get_tool_config(db: AsyncSession = Depends(get_db)):
    """
    获取工具配置
    
    Returns:
        当前工具配置
    """
    profile = await get_config_value(db, "tool_profile")
    allow = await get_config_value(db, "tool_allow")
    deny = await get_config_value(db, "tool_deny")
    max_iterations = await get_config_value(db, "tool_max_iterations")
    timeout_seconds = await get_config_value(db, "tool_timeout_seconds")
    
    allow_list = [x.strip() for x in (allow or "").split(",") if x.strip()]
    deny_list = [x.strip() for x in (deny or "").split(",") if x.strip()]
    
    return ToolConfigResponse(
        profile=profile or "full",
        allow=allow_list,
        deny=deny_list,
        max_iterations=int(max_iterations) if max_iterations else 30,
        timeout_seconds=int(timeout_seconds) if timeout_seconds else 30
    )


@router.put("/tools/config")
async def update_tool_config(
    request: ToolConfigRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    更新工具配置
    
    Args:
        request: 工具配置请求
        
    Returns:
        更新后的配置
    """
    await set_config_value(db, "tool_profile", request.profile or "full")
    await set_config_value(db, "tool_allow", ",".join(request.allow or []))
    await set_config_value(db, "tool_deny", ",".join(request.deny or []))
    await set_config_value(db, "tool_max_iterations", str(request.max_iterations or 30))
    await set_config_value(db, "tool_timeout_seconds", str(request.timeout_seconds or 30))
    
    logger.info(f"[工具配置] 已更新配置: profile={request.profile}, allow={request.allow}, deny={request.deny}")
    
    return {"success": True, "message": "工具配置已更新"}


@router.put("/tools/{tool_name}/toggle")
async def toggle_tool(
    tool_name: str,
    enabled: bool,
    db: AsyncSession = Depends(get_db)
):
    """
    切换工具启用状态
    
    Args:
        tool_name: 工具名称
        enabled: 是否启用
        
    Returns:
        操作结果
    """
    tool = tool_registry.get_tool(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"工具 '{tool_name}' 不存在")
    
    # 持久化工具启用状态到数据库
    config_key = f"{TOOL_ENABLED_PREFIX}{tool_name}"
    await set_config_value(db, config_key, str(enabled).lower())
    
    # 更新内存中的工具状态
    tool.enabled = enabled
    logger.info(f"[工具状态] 工具 '{tool_name}' 已{'启用' if enabled else '禁用'}")
    
    return {"success": True, "message": f"工具 '{tool_name}' 已{'启用' if enabled else '禁用'}"}
