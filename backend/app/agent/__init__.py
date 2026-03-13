"""
Agent 模块
提供智能体功能，包括 LLM 调用、工具执行、记忆管理等
"""

import json
import logging
import time
from typing import Any, AsyncGenerator, Optional

from app.agent.llm import LLMClient, get_llm_client
from app.agent.session import SessionManager, get_session_manager
from app.agent.tools import ToolRegistry, get_tool_registry
from app.config import get_config

logger = logging.getLogger(__name__)


class Agent:
    """
    智能体类
    整合 LLM、工具、记忆等功能，提供完整的对话处理能力
    """

    def __init__(
        self,
        llm: Optional[LLMClient] = None,
        sessions: Optional[SessionManager] = None,
        tools: Optional[ToolRegistry] = None,
    ):
        """
        初始化 Agent

        Args:
            llm: LLM 客户端实例
            sessions: 会话管理器实例
            tools: 工具注册表实例
        """
        config = get_config()
        self.llm = llm or get_llm_client()
        self.sessions = sessions or get_session_manager()
        self.tools = tools or get_tool_registry()
        self.system_prompt = config.agent.system_prompt

    async def process_message(
        self,
        session_id: str,
        user_message: str,
        channel: str = "web",
        enable_thinking: bool = False,
        model: Optional[str] = None,
    ) -> str:
        """
        处理用户消息（非流式）

        Args:
            session_id: 会话 ID
            user_message: 用户消息
            channel: 通道来源
            enable_thinking: 是否启用深度思考功能
            model: 模型名称

        Returns:
            助手回复内容
        """
        await self._ensure_session(session_id, channel)

        await self.sessions.add_message(session_id, "user", user_message)

        messages = await self._build_messages(session_id, user_message)

        max_iterations = 5
        iteration = 0
        assistant_message = ""
        all_tool_calls = []
        all_tool_results = []

        while iteration < max_iterations:
            iteration += 1

            response = self.llm.chat_with_tools(
                messages=messages,
                tools=self.tools.get_openai_tools(),
                enable_thinking=enable_thinking,
                model=model,
            )

            if "tool_calls" not in response:
                assistant_message = response["content"]
                await self.sessions.add_message(
                    session_id,
                    "assistant",
                    assistant_message,
                    tool_calls=all_tool_calls if all_tool_calls else None,
                )
                return assistant_message

            tool_calls = response["tool_calls"]
            all_tool_calls.extend(tool_calls)

            for tool_call in tool_calls:
                func_name = tool_call["function"]["name"]
                func_args = json.loads(tool_call["function"]["arguments"])

                logger.info(f"执行工具: {func_name}({func_args})")
                result = await self.tools.execute(func_name, func_args)
                logger.info(f"工具执行成功: {func_name}")

                all_tool_results.append({
                    "tool_call_id": tool_call["id"],
                    "result": result,
                })

                await self.sessions.add_message(
                    session_id,
                    "tool",
                    result,
                    tool_call_id=tool_call["id"],
                    generate_embedding=False,
                )

                messages.append({
                    "role": "tool",
                    "content": result,
                    "tool_call_id": tool_call["id"],
                })

        assistant_message = response.get("content", "")
        await self.sessions.add_message(
            session_id,
            "assistant",
            assistant_message,
            tool_calls=all_tool_calls if all_tool_calls else None,
        )
        return assistant_message

    async def process_message_stream(
        self,
        session_id: str,
        user_message: str,
        channel: str = "web",
        enable_thinking: bool = False,
        model: Optional[str] = None,
    ) -> AsyncGenerator[dict | str, None]:
        """
        流式处理用户消息

        Args:
            session_id: 会话 ID
            user_message: 用户消息
            channel: 通道来源
            enable_thinking: 是否启用深度思考功能
            model: 模型名称

        Yields:
            流式输出的文本块或工具调用事件
        """
        await self._ensure_session(session_id, channel)

        await self.sessions.add_message(session_id, "user", user_message)

        messages = await self._build_messages(session_id, user_message)

        max_iterations = 5
        iteration = 0
        assistant_message = ""
        all_tool_calls = []

        while iteration < max_iterations:
            iteration += 1

            has_tool_calls = False
            tool_calls_list = []

            async for chunk in self.llm.chat_stream(
                messages=messages,
                tools=self.tools.get_openai_tools(),
                enable_thinking=enable_thinking,
                model=model,
            ):
                if isinstance(chunk, dict):
                    if "tool_calls" in chunk:
                        has_tool_calls = True
                        for tc in chunk["tool_calls"]:
                            existing_tc = next(
                                (t for t in tool_calls_list if t["id"] == tc["id"]),
                                None
                            )
                            if existing_tc:
                                if tc["function"].get("arguments"):
                                    existing_tc["function"]["arguments"] += tc["function"]["arguments"]
                            else:
                                tool_calls_list.append({
                                    "id": tc["id"],
                                    "type": tc["type"],
                                    "function": {
                                        "name": tc["function"]["name"],
                                        "arguments": tc["function"].get("arguments", ""),
                                    },
                                })
                    elif "thoughts" in chunk:
                        yield {"thoughts": chunk["thoughts"]}
                else:
                    if chunk:
                        assistant_message += chunk
                        yield chunk

            if not has_tool_calls:
                await self.sessions.add_message(
                    session_id,
                    "assistant",
                    assistant_message,
                    tool_calls=all_tool_calls if all_tool_calls else None,
                )
                return

            all_tool_calls.extend(tool_calls_list)

            messages.append({
                "role": "assistant",
                "content": assistant_message,
                "tool_calls": tool_calls_list,
            })

            for tool_call in tool_calls_list:
                func_name = tool_call["function"]["name"]
                func_args = json.loads(tool_call["function"]["arguments"])

                start_time = time.time()
                yield {
                    "type": "tool_call",
                    "tool_call": {
                        "id": tool_call["id"],
                        "name": func_name,
                        "arguments": func_args,
                        "status": "running",
                    }
                }

                logger.info(f"执行工具: {func_name}({func_args})")
                result = await self.tools.execute(func_name, func_args)
                duration_ms = int((time.time() - start_time) * 1000)
                logger.info(f"工具执行成功: {func_name}, 耗时: {duration_ms}ms")

                tool_call["duration_ms"] = duration_ms

                yield {
                    "type": "tool_result",
                    "tool_call": {
                        "id": tool_call["id"],
                        "name": func_name,
                        "status": "success",
                        "result": result,
                        "duration_ms": duration_ms,
                    }
                }

                await self.sessions.add_message(
                    session_id,
                    "tool",
                    result,
                    tool_call_id=tool_call["id"],
                    generate_embedding=False,
                )

                messages.append({
                    "role": "tool",
                    "content": result,
                    "tool_call_id": tool_call["id"],
                })

            assistant_message = ""

        if assistant_message:
            await self.sessions.add_message(
                session_id,
                "assistant",
                assistant_message,
                tool_calls=all_tool_calls if all_tool_calls else None,
            )

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

    async def _build_messages(self, session_id: str, current_query: str) -> list[dict[str, Any]]:
        """
        构建发送给 LLM 的消息列表

        Args:
            session_id: 会话 ID
            current_query: 当前用户查询

        Returns:
            消息列表
        """
        history = await self.sessions.get_messages_for_llm(session_id)

        messages = [{"role": "system", "content": self.system_prompt}]

        config = get_config()
        if config.memory.enabled and current_query:
            try:
                related_memories = await self.sessions.search_memories(
                    current_query, session_id=None, limit=3
                )
                if related_memories:
                    memory_context = "相关历史记忆：\n"
                    for mem in related_memories:
                        role_label = "用户" if mem["role"] == "user" else "AI"
                        memory_context += f"- {role_label}: {mem['content'][:100]}...\n"
                    messages.append({
                        "role": "system",
                        "content": memory_context,
                    })
            except Exception as e:
                logger.warning(f"搜索记忆失败: {e}")

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
