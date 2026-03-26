from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List
from app.database import get_db
from app.models import Conversation, Message
from app.schemas import ConversationResponse, MessageResponse, ConversationCreate

router = APIRouter()

# 获取所有会话
@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(db: AsyncSession = Depends(get_db)):
    """
    获取所有会话列表
    """
    result = await db.execute(
        select(Conversation).order_by(Conversation.updated_at.desc())
    )
    conversations = result.scalars().all()
    return conversations

# 创建新会话
@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(conversation: ConversationCreate, db: AsyncSession = Depends(get_db)):
    """
    创建新会话
    """
    new_conversation = Conversation(title=conversation.title)
    db.add(new_conversation)
    await db.commit()
    await db.refresh(new_conversation)
    return new_conversation

# 删除会话
@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: int, db: AsyncSession = Depends(get_db)):
    """
    删除指定会话及其所有消息
    """
    conversation = await db.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    await db.execute(
        delete(Message).where(Message.conversation_id == conversation_id)
    )
    await db.delete(conversation)
    await db.commit()
    return {"message": "会话已删除"}

# 获取会话的所有消息
@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(conversation_id: int, db: AsyncSession = Depends(get_db)):
    """
    获取指定会话的所有消息
    """
    conversation = await db.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()
    return messages
