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
            db, conversation_id, role, content
        )

        if generate_embedding:
            try:
                asyncio.create_task(index_message_embedding(message.id))
                logger.info(f"[MessageService] 已创建异步嵌入任务，消息ID: {message.id}")
            except Exception as e:
                logger.warning(f"[MessageService] 创建向量嵌入任务失败: {str(e)}")

        return message

    async def save_tool_call(
        self,
        db: AsyncSession,
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
        tool_results = []

        for call in tool_calls:
            tool_call_id = call.get("id", "")
            tool_name = call.get("name", "")
            arguments_str = call.get("arguments", "{}")

            try:
                arguments = json.loads(arguments_str) if isinstance(arguments_str, str) else arguments_str
            except json.JSONDecodeError:
                arguments = {}

            logger.info(f"[MessageService] 执行工具: {tool_name}, 参数: {arguments}")

            result = await tool_executor.execute_tool(tool_name, arguments, message_id)

            result_json = json.dumps(result.to_dict(), ensure_ascii=False)

            await self.save_tool_call(
                db=db,
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

            tool_results.append({
                "tool_call_id": tool_call_id,
                "role": "tool",
                "content": result_json
            })

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
