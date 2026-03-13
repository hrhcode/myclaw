"""
LLM 客户端模块
封装智谱 AI API 调用，支持流式输出和工具调用
"""

import asyncio
import logging
from typing import Any, AsyncGenerator, Iterator, Optional

from zhipuai import ZhipuAI

from app.config import get_config

logger = logging.getLogger(__name__)


class LLMClient:
    """
    LLM 客户端类
    封装智谱 AI API 调用
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        enable_thinking: Optional[bool] = None,
    ):
        """
        初始化 LLM 客户端
        
        Args:
            api_key: 智谱 AI API Key，默认从配置读取
            model: 模型名称，默认从配置读取
            enable_thinking: 是否启用深度思考功能，默认从配置读取
        """
        config = get_config()
        self.api_key = api_key or config.llm.api_key
        self.model = model or config.llm.model
        self.enable_thinking = enable_thinking if enable_thinking is not None else False
        self.available_models = config.llm.models
        self.client = ZhipuAI(api_key=self.api_key) if self.api_key else None

    def _ensure_client(self) -> ZhipuAI:
        """
        确保客户端已初始化
        
        Returns:
            ZhipuAI 客户端实例
            
        Raises:
            ValueError: API Key 未配置
        """
        if not self.client:
            raise ValueError("API Key 未配置，请设置 ZHIPU_API_KEY 环境变量")
        return self.client

    def get_available_models(self) -> list[str]:
        """
        获取可用模型列表
        
        Returns:
            可用模型名称列表
        """
        return self.available_models

    def set_model(self, model: str) -> None:
        """
        设置当前模型
        
        Args:
            model: 模型名称
            
        Raises:
            ValueError: 模型不在可用列表中
        """
        if model not in self.available_models:
            raise ValueError(f"模型 '{model}' 不在可用列表中: {self.available_models}")
        self.model = model

    def get_current_model(self) -> str:
        """
        获取当前模型名称
        
        Returns:
            当前模型名称
        """
        return self.model

    def chat(
        self,
        messages: list[dict[str, str]],
        tools: Optional[list[dict[str, Any]]] = None,
        enable_thinking: Optional[bool] = None,
        model: Optional[str] = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        同步聊天接口
        
        Args:
            messages: 消息列表
            tools: 工具定义列表
            enable_thinking: 是否启用深度思考功能，默认使用实例配置
            model: 模型名称，默认使用实例配置
            **kwargs: 其他参数
            
        Returns:
            响应结果
        """
        client = self._ensure_client()
        
        actual_model = model or self.model
        actual_enable_thinking = enable_thinking if enable_thinking is not None else self.enable_thinking
        
        if actual_enable_thinking or 'thinking' in actual_model.lower():
            actual_enable_thinking = True
        
        params = {
            "model": actual_model,
            "messages": messages,
            **kwargs,
        }
        
        if tools:
            params["tools"] = tools

        response = client.chat.completions.create(**params)
        
        parsed_response = self._parse_response(response)
        
        if actual_enable_thinking and 'thoughts' not in parsed_response:
            parsed_response['thinking_enabled'] = True
        
        return parsed_response

    def _stream_sync(
        self,
        messages: list[dict[str, str]],
        tools: Optional[list[dict[str, Any]]] = None,
        enable_thinking: Optional[bool] = None,
        model: Optional[str] = None,
        **kwargs,
    ) -> Iterator[Any]:
        """
        同步流式聊天接口（内部方法）
        
        Args:
            messages: 消息列表
            tools: 工具定义列表
            enable_thinking: 是否启用深度思考功能，默认使用实例配置
            model: 模型名称，默认使用实例配置
            **kwargs: 其他参数
            
        Yields:
            流式输出的文本块或工具调用信息
        """
        client = self._ensure_client()
        
        actual_model = model or self.model
        actual_enable_thinking = enable_thinking if enable_thinking is not None else self.enable_thinking
        
        if actual_enable_thinking or 'thinking' in actual_model.lower():
            actual_enable_thinking = True
        
        params = {
            "model": actual_model,
            "messages": messages,
            "stream": True,
            **kwargs,
        }
        
        if tools:
            params["tools"] = tools

        response = client.chat.completions.create(**params)
        
        for chunk in response:
            if not chunk.choices:
                continue
            
            delta = chunk.choices[0].delta
            
            if delta.content:
                yield delta.content
            
            if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                yield {"thoughts": delta.reasoning_content}
            
            if hasattr(delta, 'tool_calls') and delta.tool_calls:
                for tc in delta.tool_calls:
                    tool_info = {
                        "id": tc.id,
                        "type": getattr(tc, 'type', 'function'),
                        "function": {
                            "name": getattr(tc.function, 'name', '') if hasattr(tc, 'function') else '',
                            "arguments": getattr(tc.function, 'arguments', '') if hasattr(tc, 'function') else '',
                        },
                    }
                    yield {"tool_calls": [tool_info]}

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        tools: Optional[list[dict[str, Any]]] = None,
        enable_thinking: Optional[bool] = None,
        model: Optional[str] = None,
        **kwargs,
    ) -> AsyncGenerator[Any, None]:
        """
        流式聊天接口
        
        Args:
            messages: 消息列表
            tools: 工具定义列表
            enable_thinking: 是否启用深度思考功能，默认使用实例配置
            model: 模型名称，默认使用实例配置
            **kwargs: 其他参数
            
        Yields:
            流式输出的文本块或工具调用信息
        """
        import threading
        
        queue: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_running_loop()
        exception_holder = []
        
        def sync_producer():
            try:
                for chunk in self._stream_sync(messages, tools, enable_thinking, model, **kwargs):
                    loop.call_soon_threadsafe(queue.put_nowait, chunk)
            except Exception as e:
                exception_holder.append(e)
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)
        
        thread = threading.Thread(target=sync_producer, daemon=True)
        thread.start()
        
        try:
            while True:
                chunk = await queue.get()
                if chunk is None:
                    break
                yield chunk
        finally:
            thread.join(timeout=1.0)
            if exception_holder:
                raise exception_holder[0]

    def chat_with_tools(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]],
        enable_thinking: Optional[bool] = None,
        model: Optional[str] = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        带工具调用的聊天接口
        
        Args:
            messages: 消息列表
            tools: 工具定义列表
            enable_thinking: 是否启用深度思考功能，默认使用实例配置
            model: 模型名称，默认使用实例配置
            **kwargs: 其他参数
            
        Returns:
            响应结果，包含可能的工具调用
        """
        return self.chat(messages, tools=tools, enable_thinking=enable_thinking, model=model, **kwargs)

    def _parse_response(self, response: Any) -> dict[str, Any]:
        """
        解析响应结果
        
        Args:
            response: 原始响应
            
        Returns:
            解析后的响应字典
        """
        choice = response.choices[0]
        result = {
            "content": choice.message.content or "",
            "role": choice.message.role,
            "finish_reason": choice.finish_reason,
        }
        
        if hasattr(choice.message, 'reasoning_content') and choice.message.reasoning_content:
            result["thoughts"] = choice.message.reasoning_content
        
        if choice.message.tool_calls:
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in choice.message.tool_calls
            ]
        
        return result


_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """
    获取全局 LLM 客户端实例（单例模式）
    
    Returns:
        LLMClient 实例
    """
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
