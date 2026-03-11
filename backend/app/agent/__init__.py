"""
Agent 核心模块
提供 LLM 调用、工具执行、会话管理等核心功能
"""

import json
import logging
from typing import Any, AsyncGenerator, Optional

from app.agent.llm import LLMClient, get_llm_client
from app.agent.session import SessionManager, get_session_manager
from app.agent.tools import ToolRegistry, get_tool_registry

logger = logging.getLogger(__name__)


class Agent:
    """
    Agent 运行时类
    整合 LLM、工具和会话管理，提供完整的对话处理能力
    """

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        session_manager: Optional[SessionManager] = None,
        tool_registry: Optional[ToolRegistry] = None,
        system_prompt: Optional[str] = None,
    ):
        """
        初始化 Agent
        
        Args:
            llm_client: LLM 客户端
            session_manager: 会话管理器
            tool_registry: 工具注册表
            system_prompt: 系统提示词
        """
        self.llm = llm_client or get_llm_client()
        self.sessions = session_manager or get_session_manager()
        self.tools = tool_registry or get_tool_registry()
        self.system_prompt = system_prompt or self._default_system_prompt()

    def _default_system_prompt(self) -> str:
        """
        默认系统提示词
        
        Returns:
            系统提示词字符串
        """
        return """你是 MyClaw，一个友好、智能的 AI 助手。

你的特点：
- 回答简洁明了，避免冗长
- 善于使用工具获取最新信息
- 对技术问题给出实用的解决方案
- 保持友好和专业的态度

当需要搜索信息或获取网页内容时，请使用提供的工具。"""

    async def process_message(
        self,
        session_id: str,
        user_message: str,
        channel: str = "web",
    ) -> str:
        """
        处理用户消息
        
        Args:
            session_id: 会话 ID
            user_message: 用户消息
            channel: 通道来源
            
        Returns:
            AI 回复
        """
        await self._ensure_session(session_id, channel)
        
        await self.sessions.add_message(session_id, "user", user_message)
        
        messages = await self._build_messages(session_id)
        
        max_iterations = 5
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            response = self.llm.chat_with_tools(
                messages=messages,
                tools=self.tools.get_openai_tools(),
            )
            
            if "tool_calls" not in response:
                assistant_message = response["content"]
                await self.sessions.add_message(session_id, "assistant", assistant_message)
                return assistant_message
            
            await self.sessions.add_message(
                session_id,
                "assistant",
                response["content"] or "",
                tool_calls=response["tool_calls"],
            )
            
            messages.append({
                "role": "assistant",
                "content": response["content"] or "",
                "tool_calls": response["tool_calls"],
            })
            
            for tool_call in response["tool_calls"]:
                func_name = tool_call["function"]["name"]
                func_args = json.loads(tool_call["function"]["arguments"])
                
                logger.info(f"执行工具: {func_name}({func_args})")
                result = await self.tools.execute(func_name, func_args)
                
                await self.sessions.add_message(
                    session_id,
                    "tool",
                    result,
                    tool_call_id=tool_call["id"],
                )
                
                messages.append({
                    "role": "tool",
                    "content": result,
                    "tool_call_id": tool_call["id"],
                })
        
        return "抱歉，处理过程中遇到了一些问题，请稍后再试。"

    async def process_message_stream(
        self,
        session_id: str,
        user_message: str,
        channel: str = "web",
    ) -> AsyncGenerator[str, None]:
        """
        流式处理用户消息
        
        Args:
            session_id: 会话 ID
            user_message: 用户消息
            channel: 通道来源
            
        Yields:
            流式输出的文本块
        """
        await self._ensure_session(session_id, channel)
        
        await self.sessions.add_message(session_id, "user", user_message)
        
        messages = await self._build_messages(session_id)
        
        response = self.llm.chat_with_tools(
            messages=messages,
            tools=self.tools.get_openai_tools(),
        )
        
        if "tool_calls" in response:
            await self.sessions.add_message(
                session_id,
                "assistant",
                response["content"] or "",
                tool_calls=response["tool_calls"],
            )
            
            messages.append({
                "role": "assistant",
                "content": response["content"] or "",
                "tool_calls": response["tool_calls"],
            })
            
            for tool_call in response["tool_calls"]:
                func_name = tool_call["function"]["name"]
                func_args = json.loads(tool_call["function"]["arguments"])
                
                logger.info(f"执行工具: {func_name}({func_args})")
                result = await self.tools.execute(func_name, func_args)
                
                await self.sessions.add_message(
                    session_id,
                    "tool",
                    result,
                    tool_call_id=tool_call["id"],
                )
                
                messages.append({
                    "role": "tool",
                    "content": result,
                    "tool_call_id": tool_call["id"],
                })
            
            messages = await self._build_messages(session_id)
            response = self.llm.chat(messages=messages)
        
        assistant_message = response["content"]
        await self.sessions.add_message(session_id, "assistant", assistant_message)
        
        chunk_size = 10
        for i in range(0, len(assistant_message), chunk_size):
            yield assistant_message[i:i + chunk_size]

    async def _ensure_session(self, session_id: str, channel: str) -> None:
        """
        确保会话存在
        
        Args:
            session_id: 会话 ID
            channel: 通道来源
        """
        session = await self.sessions.get_session(session_id)
        if not session:
            await self.sessions.create_session(session_id, channel)

    async def _build_messages(self, session_id: str) -> list[dict[str, Any]]:
        """
        构建发送给 LLM 的消息列表
        
        Args:
            session_id: 会话 ID
            
        Returns:
            消息列表
        """
        history = await self.sessions.get_messages_for_llm(session_id)
        
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(history)
        
        return messages


_agent: Optional[Agent] = None


def get_agent() -> Agent:
    """
    获取全局 Agent 实例（单例模式）
    
    Returns:
        Agent 实例
    """
    global _agent
    if _agent is None:
        _agent = Agent()
    return _agent


__all__ = [
    "Agent",
    "get_agent",
    "LLMClient",
    "get_llm_client",
    "SessionManager",
    "get_session_manager",
    "ToolRegistry",
    "get_tool_registry",
]
