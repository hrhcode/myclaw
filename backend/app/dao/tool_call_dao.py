"""
工具调用数据访问层
提供工具调用记录(ToolCall)实体的数据库操作
"""
import logging
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.dao._utils import commit_or_flush
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
        session_id: Optional[int],
        conversation_id: int,
        tool_name: str,
        tool_call_id: str,
        arguments: str,
        message_id: Optional[int] = None,
        result: Optional[str] = None,
        status: str = "pending",
        error: Optional[str] = None,
        execution_time_ms: Optional[int] = None,
        *,
        commit: bool = True,
    ) -> ToolCall:
        logger.debug(f"[DAO-ToolCall] 创建工具调用记录，工具: {tool_name}")
        tool_call = ToolCall(
            session_id=session_id,
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
        await commit_or_flush(db, commit)
        await db.refresh(tool_call)
        logger.info(f"[DAO-ToolCall] 工具调用记录已创建，ID: {tool_call.id}")
        return tool_call

    @staticmethod
    async def get_by_id(db: AsyncSession, tool_call_id: int) -> Optional[ToolCall]:
        result = await db.execute(
            select(ToolCall).where(ToolCall.id == tool_call_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_tool_call_id(db: AsyncSession, tool_call_id: str) -> Optional[ToolCall]:
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
        execution_time_ms: Optional[int] = None,
        *,
        commit: bool = True,
    ) -> Optional[ToolCall]:
        tool_call = await ToolCallDAO.get_by_id(db, tool_call_id)
        if not tool_call:
            logger.warning(f"[DAO-ToolCall] 更新失败，记录不存在，ID: {tool_call_id}")
            return None

        tool_call.result = result
        tool_call.status = status
        tool_call.error = error
        tool_call.execution_time_ms = execution_time_ms
        tool_call.completed_at = datetime.now() if status in ["success", "failed"] else None

        await commit_or_flush(db, commit)
        await db.refresh(tool_call)
        logger.info(f"[DAO-ToolCall] 工具调用记录已更新，ID: {tool_call_id}")
        return tool_call

    @staticmethod
    async def list_by_conversation(
        db: AsyncSession,
        conversation_id: int,
        limit: int = 100
    ) -> List[ToolCall]:
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
        result = await db.execute(
            select(ToolCall)
            .where(ToolCall.message_id == message_id)
            .order_by(ToolCall.created_at)
        )
        return list(result.scalars().all())

    @staticmethod
    async def list_by_message_ids(
        db: AsyncSession,
        message_ids: List[int],
    ) -> List[ToolCall]:
        if not message_ids:
            return []
        result = await db.execute(
            select(ToolCall)
            .where(ToolCall.message_id.in_(message_ids))
            .order_by(ToolCall.message_id, ToolCall.created_at)
        )
        return list(result.scalars().all())

    @staticmethod
    async def list_by_status(
        db: AsyncSession,
        status: str,
        limit: int = 100
    ) -> List[ToolCall]:
        result = await db.execute(
            select(ToolCall)
            .where(ToolCall.status == status)
            .order_by(ToolCall.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def count_by_conversation(db: AsyncSession, conversation_id: int) -> int:
        from sqlalchemy import func
        result = await db.execute(
            select(func.count(ToolCall.id))
            .where(ToolCall.conversation_id == conversation_id)
        )
        return result.scalar() or 0

    @staticmethod
    async def update_message_id(
        db: AsyncSession,
        tool_call_id: str,
        message_id: int,
        *,
        commit: bool = True,
    ) -> Optional[ToolCall]:
        tool_call = await ToolCallDAO.get_by_tool_call_id(db, tool_call_id)
        if not tool_call:
            logger.warning(f"[DAO-ToolCall] 更新消息ID失败，记录不存在，tool_call_id: {tool_call_id}")
            return None

        tool_call.message_id = message_id
        await commit_or_flush(db, commit)
        await db.refresh(tool_call)
        logger.info(f"[DAO-ToolCall] 工具调用记录已关联消息，tool_call_id: {tool_call_id}, message_id: {message_id}")
        return tool_call
