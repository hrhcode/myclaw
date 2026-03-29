"""
工具注册表

负责工具的注册、查询和管理
"""
import logging
from typing import Dict, List, Optional, Any
from app.tools.base import ToolDefinition

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    工具注册表
    
    负责工具的注册、查询和管理
    """
    
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
    
    def register(self, tool: ToolDefinition) -> None:
        """
        注册工具
        
        Args:
            tool: 工具定义
        """
        if tool.name in self._tools:
            logger.warning(f"工具 '{tool.name}' 已存在，将被覆盖")
        
        self._tools[tool.name] = tool
        logger.info(f"注册工具: {tool.name}")
    
    def unregister(self, name: str) -> None:
        """
        注销工具
        
        Args:
            name: 工具名称
        """
        if name in self._tools:
            del self._tools[name]
            logger.info(f"注销工具: {name}")
    
    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """
        获取工具定义
        
        Args:
            name: 工具名称
            
        Returns:
            工具定义，如果存在
        """
        return self._tools.get(name)
    
    def list_tools(self) -> List[ToolDefinition]:
        """
        列出所有工具
        
        Returns:
            工具定义列表
        """
        return list(self._tools.values())
    
    def list_enabled_tools(self) -> List[ToolDefinition]:
        """
        列出所有启用的工具
        
        Returns:
            启用的工具定义列表
        """
        return [tool for tool in self._tools.values() if tool.enabled]
    
    def filter_tools(
        self,
        allow: Optional[List[str]] = None,
        deny: Optional[List[str]] = None
    ) -> List[ToolDefinition]:
        """
        根据权限过滤工具列表
        
        Args:
            allow: 允许的工具列表（None 表示允许所有）
            deny: 禁止的工具列表（None 表示不禁止任何）
            
        Returns:
            过滤后的工具列表
        """
        if deny is None:
            deny = []
        
        if allow is None:
            return self.list_enabled_tools()
        
        allowed_set = set(allow) if allow else set()
        denied_set = set(deny) if deny else set()
        
        result = []
        for tool in self._tools.values():
            if tool.name in denied_set:
                continue
            if tool.name in allowed_set or not allowed_set:
                result.append(tool)
        
        return result
    
    def get_tools_schemas(self) -> List[Dict[str, Any]]:
        """
        获取所有工具的智谱 Schema 格式
        
        Returns:
            智谱工具 Schema 列表
        """
        from app.tools.schemas import tools_to_zhipu_schemas
        return tools_to_zhipu_schemas(self.list_enabled_tools())


tool_registry = ToolRegistry()
