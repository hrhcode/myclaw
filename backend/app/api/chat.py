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

LOG_SEPARATOR = "─" * 60


def build_memory_context(memory_results: List[MemorySearchResult]) -> str:
    """
    将记忆搜索结果格式化为上下文提示

    Args:
        memory_results: 记忆搜索结果列表

    Returns:
        格式化的记忆上下文字符串
    """
    if not memory_results:
        logger.debug("[记忆上下文] 无相关记忆，跳过上下文构建")
        return ""

    logger.info(f"[记忆上下文] 构建记忆上下文，共 {len(memory_results)} 条结果")
    
    lines = ["## 相关记忆"]
    for i, result in enumerate(memory_results, 1):
        source_label = "消息" if result.source == "message" else "长期记忆"
        lines.append(f"- [{source_label}] {result.content} (相关度: {result.score:.2f})")
        logger.debug(f"[记忆上下文] #{i}: [{source_label}] {result.content[:50]}... (分数: {result.score:.3f})")
    
    lines.append("")
    
    context = "\n".join(lines)
    logger.debug(f"[记忆上下文] 上下文长度: {len(context)} 字符")
    return context


async def get_or_create_conversation(db: AsyncSession, message: str, conversation_id: int | None = None) -> tuple[int, Conversation]:
    """
    获取或创建会话

    Returns:
        tuple: (conversation_id, conversation对象)
    """
    if not conversation_id:
        logger.info(f"[会话管理] 创建新会话，标题: {message[:20]}...")
        new_conversation = Conversation(
            title=message[:20] + "..." if len(message) > 20 else message
        )
        db.add(new_conversation)
        await db.commit()
        await db.refresh(new_conversation)
        logger.info(f"[会话管理] 新会话已创建，ID: {new_conversation.id}")
        return new_conversation.id, new_conversation
    else:
        logger.debug(f"[会话管理] 获取现有会话，ID: {conversation_id}")
        conversation = await db.get(Conversation, conversation_id)
        if not conversation:
            logger.error(f"[会话管理] 会话不存在，ID: {conversation_id}")
            raise HTTPException(status_code=404, detail="会话不存在")
        logger.debug(f"[会话管理] 会话已找到，标题: {conversation.title}")
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
    logger.debug(f"[消息存储] 保存消息 - 会话ID: {conversation_id}, 角色: {role}, 内容长度: {len(content)}")
    
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    
    logger.info(f"[消息存储] 消息已保存，ID: {message.id}, 角色: {role}")
    
    if generate_embedding:
        try:
            asyncio.create_task(index_message_embedding(message.id))
            logger.info(f"[向量嵌入] 已创建异步嵌入任务，消息ID: {message.id}")
        except Exception as e:
            logger.warning(f"[向量嵌入] 创建向量嵌入任务失败: {str(e)}")
    
    return message


async def get_conversation_history(db: AsyncSession, conversation_id: int) -> list[dict]:
    """获取会话历史"""
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()
    history = [{"role": msg.role, "content": msg.content} for msg in messages]
    logger.debug(f"[会话历史] 获取会话 {conversation_id} 的历史消息，共 {len(history)} 条")
    return history


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """
    发送聊天消息并获取AI流式回复（唯一聊天接口）
    """
    from fastapi.responses import StreamingResponse
    import json

    logger.info(LOG_SEPARATOR)
    logger.info(f"[聊天请求] 收到新消息")
    logger.info(f"  ├─ 会话ID: {request.conversation_id or '新会话'}")
    logger.info(f"  ├─ 消息长度: {len(request.message)} 字符")
    logger.info(f"  └─ 消息预览: {request.message[:50]}{'...' if len(request.message) > 50 else ''}")

    api_key = await get_config_value(db, API_KEY_KEY)
    if not api_key:
        logger.error("[配置错误] API Key未配置")
        raise HTTPException(status_code=500, detail="智谱AI API Key未配置，请先在设置中配置")

    model = await get_config_value(db, LLM_MODEL_KEY)
    logger.debug(f"[配置] 使用模型: {model or '默认模型'}")

    conversation_id, conversation = await get_or_create_conversation(
        db, request.message, request.conversation_id
    )

    await save_message(db, conversation_id, "user", request.message)
    
    logger.info(LOG_SEPARATOR)
    logger.info("[记忆搜索] 开始混合记忆搜索...")
    
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
    
    logger.info(f"[记忆搜索] 搜索完成，找到 {len(memory_results)} 条相关记忆")
    
    memory_context = build_memory_context(memory_results)

    async def generate():
        """生成流式响应"""
        full_content = ""

        try:
            logger.info(LOG_SEPARATOR)
            logger.info(f"[LLM调用] 开始调用AI模型生成回复")
            logger.info(f"  ├─ 模型: {model or '默认'}")
            logger.info(f"  ├─ 历史消息数: {len(message_history)}")
            logger.info(f"  └─ 记忆上下文: {'已注入' if memory_context else '无'}")
            
            llm = get_llm_service(api_key)

            if memory_context:
                full_messages = [
                    {"role": "system", "content": memory_context},
                    *message_history
                ]
                logger.debug(f"[LLM调用] 消息结构: 1条系统提示 + {len(message_history)}条历史")
            else:
                full_messages = message_history
                logger.debug(f"[LLM调用] 消息结构: {len(message_history)}条历史")

            async for content in llm.chat_stream(messages=full_messages, model=model, thinking=True):
                if content:
                    full_content += content
                    response_data = {
                        "content": content,
                        "conversation_id": conversation_id
                    }
                    yield f"data: {json.dumps(response_data)}\n\n"

            logger.info(f"[LLM调用] 回复生成完成，长度: {len(full_content)} 字符")
            await save_message(db, conversation_id, "assistant", full_content)
            logger.info(f"[聊天完成] 会话ID: {conversation_id}")
            logger.info(LOG_SEPARATOR)
            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"[LLM调用] 失败: {str(e)}")
            error_data = {
                "error": str(e),
                "status": 500
            }
            yield f"data: {json.dumps(error_data)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/plain")