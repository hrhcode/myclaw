from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Conversation, Message
from app.schemas import ChatRequest
from app.llm_service import get_llm_service
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


async def get_or_create_conversation(db: AsyncSession, message: str, conversation_id: int | None = None) -> tuple[int, Conversation]:
    """
    获取或创建会话

    Returns:
        tuple: (conversation_id, conversation对象)
    """
    if not conversation_id:
        new_conversation = Conversation(
            title=message[:20] + "..." if len(message) > 20 else message
        )
        db.add(new_conversation)
        await db.commit()
        await db.refresh(new_conversation)
        return new_conversation.id, new_conversation
    else:
        conversation = await db.get(Conversation, conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="会话不存在")
        return conversation_id, conversation


async def save_message(db: AsyncSession, conversation_id: int, role: str, content: str) -> Message:
    """保存消息"""
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


async def get_conversation_history(db: AsyncSession, conversation_id: int) -> list[dict]:
    """获取会话历史"""
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()
    return [{"role": msg.role, "content": msg.content} for msg in messages]


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """
    发送聊天消息并获取AI流式回复（唯一聊天接口）
    """
    from fastapi.responses import StreamingResponse
    import json

    logger.info(f"收到聊天请求: conversation_id={request.conversation_id}, message_length={len(request.message)}")

    conversation_id, conversation = await get_or_create_conversation(
        db, request.message, request.conversation_id
    )

    await save_message(db, conversation_id, "user", request.message)

    message_history = await get_conversation_history(db, conversation_id)

    async def generate():
        """生成流式响应"""
        full_content = ""

        try:
            logger.info(f"调用智谱AI模型(流式): conversation_id={conversation_id}")
            llm = get_llm_service(request.api_key)

            async for content in llm.chat_stream(messages=message_history, thinking=True):
                if content:
                    full_content += content
                    response_data = {
                        "content": content,
                        "conversation_id": conversation_id
                    }
                    yield f"data: {json.dumps(response_data)}\n\n"

            await save_message(db, conversation_id, "assistant", full_content)
            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"流式AI模型调用失败: {str(e)}")
            error_data = {
                "error": str(e),
                "status": 500
            }
            yield f"data: {json.dumps(error_data)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/plain")