from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Conversation, Message
from app.schemas import ChatRequest, MemorySearchResult
from app.llm_service import get_llm_service
from app.api.config import get_config_value, API_KEY_KEY, LLM_MODEL_KEY
from app.vector_search_service import index_message_embedding, hybrid_memory_search
from typing import List
import logging
import asyncio

router = APIRouter()
logger = logging.getLogger(__name__)


def build_memory_context(memory_results: List[MemorySearchResult]) -> str:
    """
    将记忆搜索结果格式化为上下文提示

    Args:
        memory_results: 记忆搜索结果列表

    Returns:
        格式化的记忆上下文字符串
    """
    if not memory_results:
        return ""

    lines = ["## 相关记忆"]
    for result in memory_results:
        source_label = "消息" if result.source == "message" else "长期记忆"
        lines.append(f"- [{source_label}] {result.content} (相关度: {result.score:.2f})")
    lines.append("")

    return "\n".join(lines)


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


async def save_message(db: AsyncSession, conversation_id: int, role: str, content: str, generate_embedding: bool = True) -> Message:
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
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    
    if generate_embedding:
        try:
            asyncio.create_task(index_message_embedding(message.id))
        except Exception as e:
            logger.warning(f"创建向量嵌入任务失败: {str(e)}")
    
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

    api_key = await get_config_value(db, API_KEY_KEY)
    if not api_key:
        logger.error("API Key未配置")
        raise HTTPException(status_code=500, detail="智谱AI API Key未配置，请先在设置中配置")

    model = await get_config_value(db, LLM_MODEL_KEY)

    conversation_id, conversation = await get_or_create_conversation(
        db, request.message, request.conversation_id
    )

    await save_message(db, conversation_id, "user", request.message)
    
    message_history = await get_conversation_history(db, conversation_id)
    
    memory_results = await hybrid_memory_search(
        db=db,
        query=request.message,
        conversation_id=conversation_id,
        top_k=5,
        min_score=0.5,
        include_messages=True,
        include_long_term=True,
        use_hybrid=True,
        vector_weight=0.7,
        text_weight=0.3,
        enable_mmr=True,
        mmr_lambda=0.7,
        enable_temporal_decay=True,
        half_life_days=30
    )
    
    memory_context = build_memory_context(memory_results)
    
    if memory_results:
        logger.info(f"检索到 {len(memory_results)} 条相关记忆")

    async def generate():
        """生成流式响应"""
        full_content = ""

        try:
            logger.info(f"调用智谱AI模型(流式): conversation_id={conversation_id}, model={model}")
            llm = get_llm_service(api_key)

            if memory_context:
                full_messages = [
                    {"role": "system", "content": memory_context},
                    *message_history
                ]
                logger.info(f"使用带记忆上下文的消息历史 (历史 {len(message_history)} 条)")
            else:
                full_messages = message_history

            async for content in llm.chat_stream(messages=full_messages, model=model, thinking=True):
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