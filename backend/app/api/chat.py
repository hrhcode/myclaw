from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Conversation, Message
from app.schemas import ChatRequest, ChatResponse, MessageCreate, ConversationCreate
from app.services.chat_service import ChatService
import httpx

router = APIRouter()

# 调用智谱AI GLM-4.7-Flash模型
async def call_glm_model(api_key: str, messages: list) -> str:
    """
    调用智谱AI GLM-4.7-Flash模型获取回复
    """
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": "glm-4.7-flash",
        "messages": messages,
        "thinking": {
            "type": "enabled"
        },
        "stream": False
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="调用AI模型失败")
        
        result = response.json()
        return result["choices"][0]["message"]["content"]

# 发送聊天消息（非流式）
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """
    发送聊天消息并获取AI回复
    """
    # 如果没有提供会话ID，创建新会话
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

    # 保存用户消息
    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=request.message
    )
    db.add(user_message)
    await db.commit()
    await db.refresh(user_message)

    # 获取会话历史
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()

    # 构建消息历史
    message_history = [
        {"role": msg.role, "content": msg.content}
        for msg in messages
    ]

    # 调用AI模型获取回复
    try:
        ai_content = await call_glm_model(request.api_key, message_history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # 保存AI回复
    ai_message = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=ai_content
    )
    db.add(ai_message)
    await db.commit()
    await db.refresh(ai_message)

    # 更新会话时间
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

    # 如果没有提供会话ID，创建新会话
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

    # 保存用户消息
    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=request.message
    )
    db.add(user_message)
    await db.commit()
    await db.refresh(user_message)

    # 获取会话历史
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()

    # 构建消息历史
    message_history = [
        {"role": msg.role, "content": msg.content}
        for msg in messages
    ]

    async def generate():
        """生成流式响应"""
        full_content = ""
        url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {request.api_key}"
        }
        
        payload = {
            "model": "glm-4.7-flash",
            "messages": message_history,
            "thinking": {
                "type": "enabled"
            },
            "stream": True
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as response:
                if response.status_code != 200:
                    error_data = {
                        "error": "调用AI模型失败",
                        "status": response.status_code
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
                    yield "data: [DONE]\n\n"
                    return

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            # 保存完整的AI回复
                            ai_message = Message(
                                conversation_id=conversation_id,
                                role="assistant",
                                content=full_content
                            )
                            db.add(ai_message)
                            await db.commit()
                            yield "data: [DONE]\n\n"
                            break

                        try:
                            chunk = json.loads(data)
                            if "choices" in chunk and len(chunk["choices"]) > 0:
                                delta = chunk["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    full_content += content
                                    response_data = {
                                        "content": content,
                                        "conversation_id": conversation_id
                                    }
                                    yield f"data: {json.dumps(response_data)}\n\n"
                        except json.JSONDecodeError:
                            continue

    return StreamingResponse(generate(), media_type="text/plain")
