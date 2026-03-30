"""
内置工具模块

提供开箱即用的工具实现
"""
from app.tools.builtin.time_tool import get_current_time_tool
from app.tools.builtin.web_search_tool import get_web_search_tool
from app.tools.builtin.web_fetch_tool import get_web_fetch_tool
from app.tools.builtin.exec_tool import get_exec_tool
from app.tools.builtin.process_tool import get_process_tool

__all__ = [
    "get_current_time_tool",
    "get_web_search_tool",
    "get_web_fetch_tool",
    "get_exec_tool",
    "get_process_tool",
    "register_all_builtin_tools",
]


def register_all_builtin_tools(registry) -> None:
    """
    注册所有内置工具到注册表
    
    Args:
        registry: 工具注册表实例
    """
    from app.tools.base import ToolDefinition
    
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
