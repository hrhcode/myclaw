from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Conversation, Message
from app.schemas import ChatRequest, ChatResponse, MessageResponse
from app.llm_service import get_llm_service
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# 发送聊天消息（非流式）
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """
    发送聊天消息并获取AI回复
    """
    logger.info(f"收到聊天请求: conversation_id={request.conversation_id}, message_length={len(request.message)}")

    if not request.conversation_id:
        new_conversation = Conversation(
            title=request.message[:20] + "..." if len(request.message) > 20 else request.message
        )
        db.add(new_conversation)
        await db.commit()
        await db.refresh(new_conversation)
        conversation_id = new_conversation.id
    else:
        conversation_id = request.conversation_id

    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=request.message
    )
    db.add(user_message)
    await db.commit()
    await db.refresh(user_message)

    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()

    message_history = [
        {"role": msg.role, "content": msg.content}
        for msg in messages
    ]

    try:
        logger.info(f"调用智谱AI模型: conversation_id={conversation_id}")
        llm = get_llm_service(request.api_key)
        ai_content = await llm.chat(messages=message_history, thinking=True)
        logger.info(f"AI回复成功: conversation_id={conversation_id}, response_length={len(ai_content)}")
    except Exception as e:
        logger.error(f"AI模型调用失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    ai_message = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=ai_content
    )
    db.add(ai_message)
    await db.commit()
    await db.refresh(ai_message)

    conversation = await db.get(Conversation, conversation_id)
    if conversation:
        await db.refresh(conversation)

    return ChatResponse(
        message=MessageResponse.model_validate(ai_message),
        conversation_id=conversation_id
    )

# 发送聊天消息（流式）
@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """
    发送聊天消息并获取AI流式回复
    """
    from fastapi.responses import StreamingResponse
    import json

    if not request.conversation_id:
        new_conversation = Conversation(
            title=request.message[:20] + "..." if len(request.message) > 20 else request.message
        )
        db.add(new_conversation)
        await db.commit()
        await db.refresh(new_conversation)
        conversation_id = new_conversation.id
    else:
        conversation_id = request.conversation_id

    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=request.message
    )
    db.add(user_message)
    await db.commit()
    await db.refresh(user_message)

    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()

    message_history = [
        {"role": msg.role, "content": msg.content}
        for msg in messages
    ]

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

            ai_message = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=full_content
            )
            db.add(ai_message)
            await db.commit()

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
