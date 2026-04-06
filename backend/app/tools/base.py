"""
工具系统基础模块
定义工具系统的核心类型和接口
"""
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Dict, Awaitable
from abc import ABC, abstractmethod
import asyncio
import logging

logger = logging.getLogger(__name__)


@dataclass
class ToolParameter:
    """
    工具参数定义
    
    Attributes:
        name: 参数名称
        type: 参数类型 (string, number, boolean, array, object)
        description: 参数描述
        required: 是否必需
        enum: 枇举可选值列表
        default: 默认值
    """
    name: str
    type: str
    description: str = ""
    required: bool = False
    enum: Optional[list[str]] = None
    default: Any = None


    items: Optional[list["ToolParameter"]] = None

    def to_json_schema(self) -> Dict[str, Any]:
        """
        转换为 JSON Schema 格式
        
        Returns:
            JSON Schema 字典
        """
        schema: Dict[str, Any] = {
            "type": self.type,
            "description": self.description,
        }

        if self.enum:
            schema["enum"] = self.enum
        if self.default is not None:
            schema["default"] = self.default
        if self.items:
            schema["items"] = {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string"},
                        "description": {"type": "string"},
                    }
                }
            }

        return schema


@dataclass
class ToolDefinition:
    """
    工具定义
    
    Attributes:
        name: 工具名称（唯一标识符）
        description: 工具描述
        parameters: 参数 Schema（JSON Schema 格式）
        execute: 执行函数（异步）
        enabled: 是否启用
    """
    name: str
    description: str
    parameters: Dict[str, Any]
    execute: Callable[[str, Any], Awaitable[Any]]
    enabled: bool = True

    def to_tool_schema(self) -> Dict[str, Any]:
        """
        转换为 OpenAI 兼容的工具定义格式

        Returns:
            工具 Schema 字典
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    # 向后兼容别名
    to_zhipu_tool_schema = to_tool_schema


@dataclass
class ToolResult:
    """
    工具执行结果
    
    Attributes:
        success: 是否成功
        content: 返回内容
        error: 错误信息
        execution_time_ms: 执行时间（毫秒）
    """
    success: bool
    content: Any
    error: Optional[str] = None
    execution_time_ms: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            字典格式的结果
        """
        return {
            "success": self.success,
            "content": self.content,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms
        }


class BaseTool(ABC):
    """
    工具基类
    
    所有工具都应继承此类并实现 execute 方法
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述"""
        pass

    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """参数 Schema"""
        pass

    @property
    def enabled(self) -> bool:
        """是否启用"""
        return True

    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """
        执行工具
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            工具执行结果
        """
        pass

    def to_tool_schema(self) -> Dict[str, Any]:
        """
        转换为 OpenAI 兼容的工具定义格式

        Returns:
            工具 Schema 字典
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    # 向后兼容别名
    to_zhipu_tool_schema = to_tool_schema


def create_tool(
    name: str,
    description: str,
    parameters: Dict[str, Any],
    execute: Callable[[str, Any], Awaitable[Any]],
    enabled: bool = True
) -> ToolDefinition:
    """
    创建工具定义的便捷函数
    
    Args:
        name: 工具名称
        description: 工具描述
        parameters: 参数 Schema
        execute: 执行函数
        enabled: 是否启用
        
    Returns:
        工具定义实例
    """
    return ToolDefinition(
        name=name,
        description=description,
        parameters=parameters,
        execute=execute,
        enabled=enabled
    )
