"""
历史记录API
提供会话和消息查询的HTTP接口
业务逻辑已委托给DAO层，API层仅处理HTTP请求/响应
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.dao.conversation_dao import ConversationDAO
from app.dao.message_dao import MessageDAO
from app.dao.agent_event_dao import AgentEventDAO
from app.dao.tool_call_dao import ToolCallDAO
from app.schemas.schemas import ConversationResponse, MessageResponse, ConversationCreate, ConversationUpdate, ToolCallInMessage, AgentEventInMessage
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(db: AsyncSession = Depends(get_db)):
    """
    获取所有会话列表
    """
    logger.info("获取所有会话列表")
    conversations = await ConversationDAO.list_all(db)
    logger.info(f"返回 {len(conversations)} 个会话")
    return conversations


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    conversation: ConversationCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建新会话
    """
    new_conversation = await ConversationDAO.create(db, conversation.title)
    return new_conversation


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    删除指定会话及其所有消息
    注意：如果这是最后一个会话，则不允许删除
    """
    logger.info(f"删除会话: conversation_id={conversation_id}")

    all_conversations = await ConversationDAO.list_all(db)
    if len(all_conversations) <= 1:
        logger.warning(f"拒绝删除最后一个会话: conversation_id={conversation_id}")
        raise HTTPException(status_code=400, detail="无法删除最后一个会话，系统至少需要保留一个会话")

    success = await ConversationDAO.delete(db, conversation_id)
    if not success:
        logger.warning(f"会话不存在: conversation_id={conversation_id}")
        raise HTTPException(status_code=404, detail="会话不存在")

    logger.info(f"会话已删除: conversation_id={conversation_id}")
    return {"message": "会话已删除"}


@router.put("/conversations/{conversation_id}", response_model=ConversationResponse)
async def rename_conversation(
    conversation_id: int,
    data: ConversationUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    重命名指定会话
    """
    logger.info(f"重命名会话: conversation_id={conversation_id}, new_title={data.title}")

    conversation = await ConversationDAO.update_title(db, conversation_id, data.title)
    if not conversation:
        logger.warning(f"会话不存在: conversation_id={conversation_id}")
        raise HTTPException(status_code=404, detail="会话不存在")

    logger.info(f"会话已重命名: conversation_id={conversation_id}")
    return conversation


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定会话的所有消息（包含关联的工具调用记录）
    """
    conversation = await ConversationDAO.get_by_id(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="会话不存在")

    messages = await MessageDAO.get_conversation_history(db, conversation_id)

    response_messages = []
    for msg in messages:
        tool_calls = []
        agent_events = []
        if msg.role == "assistant":
            tool_call_records = await ToolCallDAO.list_by_message(db, msg.id)
            tool_calls = [
                ToolCallInMessage(
                    id=tc.id,
                    tool_name=tc.tool_name,
                    tool_call_id=tc.tool_call_id,
                    arguments=tc.arguments,
                    result=tc.result,
                    status=tc.status,
                    error=tc.error,
                    execution_time_ms=tc.execution_time_ms,
                    created_at=tc.created_at,
                    completed_at=tc.completed_at
                )
                for tc in tool_call_records
            ]
            agent_event_records = await AgentEventDAO.list_by_message(db, msg.id)
            agent_events = [
                AgentEventInMessage(
                    id=event.id,
                    run_id=event.run_id,
                    event_type=event.event_type,
                    payload=event.payload,
                    sequence=event.sequence,
                    created_at=event.created_at,
                )
                for event in agent_event_records
            ]

        response_messages.append(MessageResponse(
            id=msg.id,
            conversation_id=msg.conversation_id,
            role=msg.role,
            content=msg.content,
            created_at=msg.created_at,
            tool_calls=tool_calls,
            agent_events=agent_events,
        ))

    return response_messages
