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
from app.schemas.schemas import ConversationResponse, MessageResponse, ConversationCreate, ConversationUpdate
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
    """
    logger.info(f"删除会话: conversation_id={conversation_id}")

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
    获取指定会话的所有消息
    """
    conversation = await ConversationDAO.get_by_id(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="会话不存在")

    messages = await MessageDAO.get_conversation_history(db, conversation_id)
    return messages
