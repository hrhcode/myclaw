"""
工具调用数据访问层
提供工具调用记录(ToolCall)实体的数据库操作
"""
import logging
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import ToolCall

logger = logging.getLogger(__name__)


class ToolCallDAO:
    """
    工具调用数据访问对象
    封装工具调用记录相关的数据库操作
    """

    @staticmethod
    async def create(
        db: AsyncSession,
        conversation_id: int,
        tool_name: str,
        tool_call_id: str,
        arguments: str,
        message_id: Optional[int] = None,
        result: Optional[str] = None,
        status: str = "pending",
        error: Optional[str] = None,
        execution_time_ms: Optional[int] = None
    ) -> ToolCall:
        """
        创建工具调用记录

        Args:
            db: 数据库会话
            conversation_id: 会话ID
            tool_name: 工具名称
            tool_call_id: 工具调用ID
            arguments: 参数JSON
            message_id: 消息ID
            result: 结果JSON
            status: 状态
            error: 错误信息
            execution_time_ms: 执行时间(毫秒)

        Returns:
            新创建的工具调用记录对象
        """
        logger.debug(f"[DAO-ToolCall] 创建工具调用记录，工具: {tool_name}")
        tool_call = ToolCall(
            conversation_id=conversation_id,
            message_id=message_id,
            tool_name=tool_name,
            tool_call_id=tool_call_id,
            arguments=arguments,
            result=result,
            status=status,
            error=error,
            execution_time_ms=execution_time_ms,
            completed_at=datetime.now() if status in ["success", "failed"] else None
        )
        db.add(tool_call)
        await db.commit()
        await db.refresh(tool_call)
        logger.info(f"[DAO-ToolCall] 工具调用记录已创建，ID: {tool_call.id}")
        return tool_call

    @staticmethod
    async def get_by_id(db: AsyncSession, tool_call_id: int) -> Optional[ToolCall]:
        """
        根据ID获取工具调用记录

        Args:
            db: 数据库会话
            tool_call_id: 工具调用记录ID

        Returns:
            工具调用记录对象，不存在返回None
        """
        result = await db.execute(
            select(ToolCall).where(ToolCall.id == tool_call_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_tool_call_id(db: AsyncSession, tool_call_id: str) -> Optional[ToolCall]:
        """
        根据工具调用ID获取记录

        Args:
            db: 数据库会话
            tool_call_id: 工具调用ID

        Returns:
            工具调用记录对象，不存在返回None
        """
        result = await db.execute(
            select(ToolCall).where(ToolCall.tool_call_id == tool_call_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_result(
        db: AsyncSession,
        tool_call_id: int,
        result: str,
        status: str,
        error: Optional[str] = None,
        execution_time_ms: Optional[int] = None
    ) -> Optional[ToolCall]:
        """
        更新工具调用结果

        Args:
            db: 数据库会话
            tool_call_id: 工具调用记录ID
            result: 结果JSON
            status: 状态
            error: 错误信息
            execution_time_ms: 执行时间(毫秒)

        Returns:
            更新后的工具调用记录对象
        """
        tool_call = await ToolCallDAO.get_by_id(db, tool_call_id)
        if not tool_call:
            logger.warning(f"[DAO-ToolCall] 更新失败，记录不存在，ID: {tool_call_id}")
            return None

        tool_call.result = result
        tool_call.status = status
        tool_call.error = error
        tool_call.execution_time_ms = execution_time_ms
        tool_call.completed_at = datetime.now() if status in ["success", "failed"] else None

        await db.commit()
        await db.refresh(tool_call)
        logger.info(f"[DAO-ToolCall] 工具调用记录已更新，ID: {tool_call_id}")
        return tool_call

    @staticmethod
    async def list_by_conversation(
        db: AsyncSession,
        conversation_id: int,
        limit: int = 100
    ) -> List[ToolCall]:
        """
        获取会话的工具调用记录

        Args:
            db: 数据库会话
            conversation_id: 会话ID
            limit: 返回数量限制

        Returns:
            工具调用记录列表
        """
        result = await db.execute(
            select(ToolCall)
            .where(ToolCall.conversation_id == conversation_id)
            .order_by(ToolCall.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def list_by_message(
        db: AsyncSession,
        message_id: int
    ) -> List[ToolCall]:
        """
        获取消息的工具调用记录

        Args:
            db: 数据库会话
            message_id: 消息ID

        Returns:
            工具调用记录列表
        """
        result = await db.execute(
            select(ToolCall)
            .where(ToolCall.message_id == message_id)
            .order_by(ToolCall.created_at)
        )
        return list(result.scalars().all())

    @staticmethod
    async def list_by_status(
        db: AsyncSession,
        status: str,
        limit: int = 100
    ) -> List[ToolCall]:
        """
        按状态获取工具调用记录

        Args:
            db: 数据库会话
            status: 状态
            limit: 返回数量限制

        Returns:
            工具调用记录列表
        """
        result = await db.execute(
            select(ToolCall)
            .where(ToolCall.status == status)
            .order_by(ToolCall.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def count_by_conversation(db: AsyncSession, conversation_id: int) -> int:
        """
        统计会话的工具调用次数

        Args:
            db: 数据库会话
            conversation_id: 会话ID

        Returns:
            工具调用次数
        """
        from sqlalchemy import func
        result = await db.execute(
            select(func.count(ToolCall.id))
            .where(ToolCall.conversation_id == conversation_id)
        )
        return result.scalar() or 0
