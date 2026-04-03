"""
消息服务层
提供消息领域的业务逻辑处理，包括消息存储和向量嵌入
"""
import logging
import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.agent_loop.prompting import build_model_history
from app.models.models import Message, ToolCall
from app.dao.message_dao import MessageDAO
from app.dao.tool_call_dao import ToolCallDAO
from app.services.vector_search_service import index_message_embedding

logger = logging.getLogger(__name__)


class MessageService:
    """
    消息服务
    处理消息相关的业务逻辑
    """

    async def save(
        self,
        db: AsyncSession,
        session_id: Optional[int],
        conversation_id: int,
        role: str,
        content: str,
        generate_embedding: bool = True
    ) -> Message:
        """
        保存消息

        Args:
            db: 数据库会话
            conversation_id: 会话ID
            role: 角色 (user/assistant)
            content: 消息内容
            generate_embedding: 是否生成向量嵌入

        Returns:
            保存的消息对象
        """
        message = await MessageDAO.create(
            db, session_id, conversation_id, role, content
        )

        if generate_embedding:
            try:
                asyncio.create_task(index_message_embedding(message.id))
                logger.debug(f"[MessageService] 已创建异步嵌入任务，消息ID: {message.id}")
            except Exception as e:
                logger.warning(f"[MessageService] 创建向量嵌入任务失败: {str(e)}")

        return message

    async def save_tool_call(
        self,
        db: AsyncSession,
        session_id: Optional[int],
        conversation_id: int,
        message_id: Optional[int],
        tool_name: str,
        tool_call_id: str,
        arguments: str,
        result: str,
        status: str,
        error: Optional[str] = None,
        execution_time_ms: Optional[int] = None
    ) -> ToolCall:
        """
        保存工具调用记录

        Args:
            db: 数据库会话
            conversation_id: 会话ID
            message_id: 消息ID
            tool_name: 工具名称
            tool_call_id: 工具调用ID
            arguments: 参数JSON
            result: 结果JSON
            status: 状态
            error: 错误信息
            execution_time_ms: 执行时间(毫秒)

        Returns:
            保存的工具调用记录对象
        """
        return await ToolCallDAO.create(
            db=db,
            session_id=session_id,
            conversation_id=conversation_id,
            message_id=message_id,
            tool_name=tool_name,
            tool_call_id=tool_call_id,
            arguments=arguments,
            result=result,
            status=status,
            error=error,
            execution_time_ms=execution_time_ms
        )

    async def process_tool_calls(
        self,
        db: AsyncSession,
        session_id: Optional[int],
        conversation_id: int,
        message_id: Optional[int],
        tool_calls: List[Dict[str, Any]],
        tool_executor
    ) -> List[Dict[str, Any]]:
        """
        处理工具调用列表

        Args:
            db: 数据库会话
            conversation_id: 会话ID
            message_id: 消息ID
            tool_calls: 工具调用列表
            tool_executor: 工具执行器

        Returns:
            工具结果消息列表
        """
        from app.common.config import get_config_value
        from app.common.constants import TAVILY_API_KEY_KEY

        logger.info(f"[MessageService] ════════════════════════════════════════════")
        logger.info(f"[MessageService] 开始处理工具调用")
        logger.info(f"[MessageService] 会话ID: {conversation_id}")
        logger.info(f"[MessageService] 工具调用数量: {len(tool_calls)}")
        logger.info(f"[MessageService] ────────────────────────────────────────────")

        tool_results = []

        for i, call in enumerate(tool_calls, 1):
            tool_call_id = call.get("id", "")
            tool_name = call.get("name", "")
            arguments_str = call.get("arguments", "{}")

            logger.info(f"[MessageService] [{i}/{len(tool_calls)}] 工具调用: {tool_name}")
            logger.info(f"[MessageService]   Call ID: {tool_call_id}")

            try:
                arguments = json.loads(arguments_str) if isinstance(arguments_str, str) else arguments_str
            except json.JSONDecodeError:
                logger.error(f"[MessageService]   参数解析失败，使用空参数")
                arguments = {}

            if tool_name == "web_search":
                tavily_key = await get_config_value(db, TAVILY_API_KEY_KEY)
                if tavily_key:
                    arguments["tavily_api_key"] = tavily_key
                    logger.info(f"[MessageService]   ✓ 已获取 Tavily API Key 注入")
                else:
                    logger.warning(f"[MessageService]   ✗ Tavily API Key 未配置")

            if tool_name.startswith("browser_"):
                from app.common.constants import (
                    BROWSER_DEFAULT_TYPE_KEY,
                    BROWSER_HEADLESS_KEY,
                    BROWSER_VIEWPORT_WIDTH_KEY,
                    BROWSER_VIEWPORT_HEIGHT_KEY,
                    BROWSER_TIMEOUT_MS_KEY,
                    BROWSER_SSRF_ALLOW_PRIVATE_KEY,
                    BROWSER_SSRF_WHITELIST_KEY,
                    BROWSER_MAX_INSTANCES_KEY,
                    BROWSER_IDLE_TIMEOUT_MS_KEY,
                    BROWSER_USE_SYSTEM_BROWSER_KEY,
                    BROWSER_SYSTEM_BROWSER_CHANNEL_KEY,
                )

                config = {}
                config["default_type"] = await get_config_value(db, BROWSER_DEFAULT_TYPE_KEY) or "chromium"
                config["headless"] = (await get_config_value(db, BROWSER_HEADLESS_KEY) or "false").lower() == "true"
                config["viewport_width"] = int(await get_config_value(db, BROWSER_VIEWPORT_WIDTH_KEY) or "1280")
                config["viewport_height"] = int(await get_config_value(db, BROWSER_VIEWPORT_HEIGHT_KEY) or "720")
                config["timeout_ms"] = int(await get_config_value(db, BROWSER_TIMEOUT_MS_KEY) or "30000")
                config["ssrf_allow_private"] = (await get_config_value(db, BROWSER_SSRF_ALLOW_PRIVATE_KEY) or "false").lower() == "true"
                config["ssrf_whitelist"] = await get_config_value(db, BROWSER_SSRF_WHITELIST_KEY) or ""
                config["max_instances"] = int(await get_config_value(db, BROWSER_MAX_INSTANCES_KEY) or "1")
                config["idle_timeout_ms"] = int(await get_config_value(db, BROWSER_IDLE_TIMEOUT_MS_KEY) or "300000")
                config["use_system_browser"] = (await get_config_value(db, BROWSER_USE_SYSTEM_BROWSER_KEY) or "true").lower() == "true"
                config["system_browser_channel"] = await get_config_value(db, BROWSER_SYSTEM_BROWSER_CHANNEL_KEY) or "chrome"

                arguments["_config"] = config
                logger.info(f"[MessageService]   ✓ 已获取浏览器配置注入")

            safe_args = {}
            for k, v in arguments.items():
                if k.startswith("_"):
                    continue
                if "key" in k.lower() or "token" in k.lower():
                    safe_args[k] = "***"
                else:
                    safe_args[k] = v
            logger.info(f"[MessageService]   参数: {json.dumps(safe_args, ensure_ascii=False)[:200]}")

            result = await tool_executor.execute_tool(tool_name, arguments, message_id)

            result_json = json.dumps(result.to_dict(), ensure_ascii=False)

            save_result = await self.save_tool_call(
                db=db,
                session_id=session_id,
                conversation_id=conversation_id,
                message_id=message_id,
                tool_name=tool_name,
                tool_call_id=tool_call_id,
                arguments=arguments_str,
                result=result_json,
                status="success" if result.success else "failed",
                error=result.error,
                execution_time_ms=result.execution_time_ms
            )

            logger.info(f"[MessageService]   结果已保存，Record ID: {save_result.id}")
            logger.info(f"[MessageService]   执行状态: {'成功' if result.success else '失败'}")
            if not result.success:
                logger.error(f"[MessageService]   错误信息: {result.error}")

            tool_results.append({
                "tool_call_id": tool_call_id,
                "role": "tool",
                "content": result_json
            })

        logger.info(f"[MessageService] ════════════════════════════════════════════")
        logger.info(f"[MessageService] 工具调用处理完成")
        logger.info(f"[MessageService] 成功: {sum(1 for r in tool_results if json.loads(r['content']).get('success'))}/{len(tool_results)}")
        logger.info(f"[MessageService] ════════════════════════════════════════════")

        return tool_results

    async def get_history(
        self,
        db: AsyncSession,
        conversation_id: int
    ) -> List[Dict[str, str]]:
        """
        获取会话历史

        Args:
            db: 数据库会话
            conversation_id: 会话ID

        Returns:
            历史消息列表
        """
        messages = await MessageDAO.get_conversation_history(db, conversation_id)
        return [{"role": msg.role, "content": msg.content} for msg in messages]

    async def get_model_history(
        self,
        db: AsyncSession,
        conversation_id: int
    ) -> List[Dict[str, str]]:
        """
        获取发给模型的会话历史。

        与普通历史不同，这里会把已持久化的工具调用摘要挂到对应 assistant 消息上，
        让新一轮请求也能继承关键工具轨迹。
        """
        messages = await MessageDAO.get_conversation_history(db, conversation_id)
        assistant_message_ids = [msg.id for msg in messages if msg.role == "assistant"]
        tool_call_records = await ToolCallDAO.list_by_message_ids(db, assistant_message_ids)

        tool_call_map: Dict[int, List[ToolCall]] = {}
        for record in tool_call_records:
            if record.message_id is None:
                continue
            tool_call_map.setdefault(record.message_id, []).append(record)

        return build_model_history(messages, tool_call_map)

    async def get_by_id(
        self,
        db: AsyncSession,
        message_id: int
    ) -> Optional[Message]:
        """
        获取消息

        Args:
            db: 数据库会话
            message_id: 消息ID

        Returns:
            消息对象，不存在返回None
        """
        return await MessageDAO.get_by_id(db, message_id)

    async def get_recent_messages(
        self,
        db: AsyncSession,
        conversation_id: int,
        limit: int = 20
    ) -> List[Message]:
        """
        获取最近的消息

        Args:
            db: 数据库会话
            conversation_id: 会话ID
            limit: 返回消息数量

        Returns:
            最近的消息列表
        """
        return await MessageDAO.get_recent_messages(db, conversation_id, limit)
