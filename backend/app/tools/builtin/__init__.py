"""
内置工具模块

提供开箱即用的工具实现
"""
from app.tools.builtin.time_tool import get_current_time_tool
from app.tools.builtin.web_search_tool import get_web_search_tool
from app.tools.builtin.web_fetch_tool import get_web_fetch_tool
from app.tools.builtin.exec_tool import get_exec_tool
from app.tools.builtin.process_tool import get_process_tool
from app.tools.builtin.browser_tool import get_browser_tools

__all__ = [
    "get_current_time_tool",
    "get_web_search_tool",
    "get_web_fetch_tool",
    "get_exec_tool",
    "get_process_tool",
    "get_browser_tools",
    "register_all_builtin_tools",
]


async def register_all_builtin_tools(registry, db=None) -> None:
    """
    注册所有内置工具到注册表
    
    Args:
        registry: 工具注册表实例
        db: 数据库会话（可选，用于加载工具启用状态和配置）
    """
    from app.tools.base import ToolDefinition
    from app.common.constants import TOOL_ENABLED_PREFIX
    
    tools = [
        get_current_time_tool(),
        get_web_search_tool(),
        get_web_fetch_tool(),
        get_exec_tool(),
        get_process_tool(),
    ]
    
    for tool in tools:
        if isinstance(tool, ToolDefinition):
            registry.register(tool)

    browser_tools = get_browser_tools()
    for tool in browser_tools:
        if isinstance(tool, ToolDefinition):
            if db:
                from app.common.config import get_config_value
                config_key = f"{TOOL_ENABLED_PREFIX}{tool.name}"
                enabled_str = await get_config_value(db, config_key)
                if enabled_str:
                    tool.enabled = enabled_str.lower() == "true"
            
            registry.register(tool)
