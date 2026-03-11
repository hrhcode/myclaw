"""
LLM 客户端模块
封装智谱 AI API 调用，支持流式输出和工具调用
"""

import json
import logging
from typing import Any, AsyncGenerator, Optional

from zhipuai import ZhipuAI

from app.config import get_config

logger = logging.getLogger(__name__)


class LLMClient:
    """
    LLM 客户端类
    封装智谱 AI API 调用
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        初始化 LLM 客户端
        
        Args:
            api_key: 智谱 AI API Key，默认从配置读取
            model: 模型名称，默认从配置读取
        """
        config = get_config()
        self.api_key = api_key or config.llm.api_key
        self.model = model or config.llm.model
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

    def chat(
        self,
        messages: list[dict[str, str]],
        tools: Optional[list[dict[str, Any]]] = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        同步聊天接口
        
        Args:
            messages: 消息列表
            tools: 工具定义列表
            **kwargs: 其他参数
            
        Returns:
            响应结果
        """
        client = self._ensure_client()
        
        params = {
            "model": self.model,
            "messages": messages,
            **kwargs,
        }
        
        if tools:
            params["tools"] = tools

        response = client.chat.completions.create(**params)
        return self._parse_response(response)

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        tools: Optional[list[dict[str, Any]]] = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """
        流式聊天接口
        
        Args:
            messages: 消息列表
            tools: 工具定义列表
            **kwargs: 其他参数
            
        Yields:
            流式输出的文本块
        """
        client = self._ensure_client()
        
        params = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            **kwargs,
        }
        
        if tools:
            params["tools"] = tools

        response = client.chat.completions.create(**params)
        
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def chat_with_tools(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]],
        **kwargs,
    ) -> dict[str, Any]:
        """
        带工具调用的聊天接口
        
        Args:
            messages: 消息列表
            tools: 工具定义列表
            **kwargs: 其他参数
            
        Returns:
            响应结果，包含可能的工具调用
        """
        return self.chat(messages, tools=tools, **kwargs)

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

    async def get_embedding(self, text: str) -> list[float]:
        """
        获取文本的向量嵌入
        
        Args:
            text: 输入文本
            
        Returns:
            嵌入向量
        """
        client = self._ensure_client()
        config = get_config()
        
        response = client.embeddings.create(
            model=config.memory.embedding_model,
            input=text,
        )
        
        return response.data[0].embedding


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
