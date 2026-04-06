"""
LLM Provider 抽象基类

定义统一的 LLM 调用接口，各 provider 实现此接口。
"""
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional


class BaseLLMProvider(ABC):
    """LLM Provider 抽象基类"""

    def __init__(self, api_key: str, model: str = "glm-4-flash"):
        self.api_key = api_key
        self.model = model

    @abstractmethod
    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        thinking: bool = True,
    ) -> AsyncIterator[str]:
        """
        流式聊天对话

        Args:
            messages: 消息历史列表
            model: 模型名称
            thinking: 是否启用思考模式

        Yields:
            AI 回复的每个文本片段
        """
        ...

    @abstractmethod
    async def chat_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        model: Optional[str] = None,
        thinking: bool = True,
    ) -> Dict[str, Any]:
        """
        带工具调用的聊天（非流式）

        Args:
            messages: 消息历史列表
            tools: 工具定义列表
            model: 模型名称
            thinking: 是否启用思考模式

        Returns:
            {"content": str|None, "tool_calls": [{"id": str, "name": str, "arguments": str}]}
        """
        ...

    @abstractmethod
    async def chat_stream_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        model: Optional[str] = None,
        thinking: bool = True,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        带工具调用的流式聊天

        Args:
            messages: 消息历史列表
            tools: 工具定义列表
            model: 模型名称
            thinking: 是否启用思考模式

        Yields:
            {"type": "reasoning"|"content"|"tool_calls", ...}
        """
        ...
