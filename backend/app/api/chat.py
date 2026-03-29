from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.models import Conversation, Message, ToolCall
from app.schemas.schemas import ChatRequest, MemorySearchResult
from app.services.llm_service import get_llm_service
from app.common.config import get_config_value
from app.common.constants import API_KEY_KEY, LLM_MODEL_KEY
from app.services.vector_search_service import index_message_embedding, hybrid_memory_search
from app.tools import tool_registry, tool_executor, tools_to_zhipu_schemas
from app.tools.builtin import get_current_time_tool
from app.common.utils.logging import log_search_start, log_search_result
from app.common.constants import LOG_SEPARATOR
from typing import List, Dict, Any
import logging
import asyncio
import json
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)


def register_builtin_tools():
    """
    注册内置工具到工具注册表
    """
    if not tool_registry.get_tool("get_current_time"):
        tool_registry.register(get_current_time_tool())
        logger.info("[工具注册] 已注册内置工具: get_current_time")


register_builtin_tools()


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


async def save_tool_call(
    db: AsyncSession,
    conversation_id: int,
    message_id: int,
    tool_name: str,
    tool_call_id: str,
    arguments: str,
    result: str,
    status: str,
    error: str = None,
    execution_time_ms: int = None
) -> ToolCall:
    """
    保存工具调用记录
    
    Args:
        db: 数据库会话
        conversation_id: 会话ID
        message_id: 消息ID
        tool_name: 工具名称
        tool_call_id: 工具调用ID
        arguments: 参数JSON
        result: 结果JSON
        status: 状态
        error: 错误信息
        execution_time_ms: 执行时间(毫秒)
        
    Returns:
        保存的工具调用对象
    """
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
    
    logger.info(f"[工具调用记录] 已保存 - 工具: {tool_name}, 状态: {status}")
    return tool_call


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


async def process_tool_calls(
    db: AsyncSession,
    conversation_id: int,
    message_id: int,
    tool_calls: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    处理工具调用列表
    
    Args:
        db: 数据库会话
        conversation_id: 会话ID
        message_id: 消息ID
        tool_calls: 工具调用列表
        
    Returns:
        工具结果消息列表
    """
    tool_results = []
    
    for call in tool_calls:
        tool_call_id = call.get("id", "")
        tool_name = call.get("name", "")
        arguments_str = call.get("arguments", "{}")
        
        try:
            arguments = json.loads(arguments_str) if isinstance(arguments_str, str) else arguments_str
        except json.JSONDecodeError:
            arguments = {}
        
        logger.info(f"[工具调用] 执行工具: {tool_name}, 参数: {arguments}")
        
        result = await tool_executor.execute_tool(tool_name, arguments, message_id)
        
        result_json = json.dumps(result.to_dict(), ensure_ascii=False)
        
        await save_tool_call(
            db=db,
            conversation_id=conversation_id,
            message_id=message_id,
            tool_name=tool_name,
            tool_call_id=tool_call_id,
            arguments=arguments_str,
            result=result_json,
            status="success" if result.success else "failed",
            error=result.error,
            execution_time_ms=result.execution_time_ms
        )
        
        tool_results.append({
            "tool_call_id": tool_call_id,
            "role": "tool",
            "content": result_json
        })
    
    return tool_results


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """
    发送聊天消息并获取AI流式回复（支持工具调用）
    """
    from fastapi.responses import StreamingResponse

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

    tool_enabled = await get_config_value(db, "tool_enabled")
    tool_max_iterations = await get_config_value(db, "tool_max_iterations")
    tool_timeout = await get_config_value(db, "tool_timeout_seconds")
    
    use_tools = tool_enabled == "true" if tool_enabled else True
    max_iterations = int(tool_max_iterations) if tool_max_iterations else 5
    timeout_seconds = int(tool_timeout) if tool_timeout else 30
    
    tool_executor.timeout_seconds = timeout_seconds

    conversation_id, conversation = await get_or_create_conversation(
        db, request.message, request.conversation_id
    )

    await save_message(db, conversation_id, "user", request.message)
    
    logger.info(LOG_SEPARATOR)
    logger.info("[记忆搜索】开始混合记忆搜索...")
    
    memory_top_k = await get_config_value(db, "memory_top_k")
    memory_min_score = await get_config_value(db, "memory_min_score")
    memory_use_hybrid = await get_config_value(db, "memory_use_hybrid")
    memory_vector_weight = await get_config_value(db, "memory_vector_weight")
    memory_text_weight = await get_config_value(db, "memory_text_weight")
    memory_enable_mmr = await get_config_value(db, "memory_enable_mmr")
    memory_mmr_lambda = await get_config_value(db, "memory_mmr_lambda")
    memory_enable_temporal_decay = await get_config_value(db, "memory_enable_temporal_decay")
    memory_half_life_days = await get_config_value(db, "memory_half_life_days")
    
    message_history = await get_conversation_history(db, conversation_id)
    
    memory_results = await hybrid_memory_search(
        db=db,
        query=request.message,
        conversation_id=conversation_id,
        top_k=int(memory_top_k) if memory_top_k else 5,
        min_score=float(memory_min_score) if memory_min_score else 0.5,
        include_messages=True,
        include_long_term=True,
        use_hybrid=(memory_use_hybrid == "true") if memory_use_hybrid else True,
        vector_weight=float(memory_vector_weight) if memory_vector_weight else 0.7,
        text_weight=float(memory_text_weight) if memory_text_weight else 0.3,
        enable_mmr=(memory_enable_mmr == "true") if memory_enable_mmr else True,
        mmr_lambda=float(memory_mmr_lambda) if memory_mmr_lambda else 0.7,
        enable_temporal_decay=(memory_enable_temporal_decay == "true") if memory_enable_temporal_decay else True,
        half_life_days=int(memory_half_life_days) if memory_half_life_days else 30
    )
    
    logger.info(f"[记忆搜索] 搜索完成，找到 {len(memory_results)} 条相关记忆")
    
    memory_context = build_memory_context(memory_results)

    async def generate():
        """生成流式响应"""
        full_content = ""
        tool_calls_info = []

        try:
            logger.info(LOG_SEPARATOR)
            logger.info(f"[LLM调用] 开始调用AI模型生成回复")
            logger.info(f"  ├─ 模型: {model or '默认'}")
            logger.info(f"  ├─ 历史消息数: {len(message_history)}")
            logger.info(f"  ├─ 记忆上下文: {'已注入' if memory_context else '无'}")
            logger.info(f"  └─ 工具调用: {'启用' if use_tools else '禁用'}")
            
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

            tools = None
            if use_tools:
                tools = tools_to_zhipu_schemas(tool_registry.list_enabled_tools())
                logger.info(f"[工具调用] 已加载 {len(tools)} 个工具")

            iteration = 0
            while iteration < max_iterations:
                iteration += 1
                logger.info(f"[LLM调用] 第 {iteration} 次调用")
                
                has_tool_calls = False
                current_tool_calls = []
                
                async for chunk in llm.chat_stream_with_tools(messages=full_messages, tools=tools, model=model, thinking=True):
                    chunk_type = chunk.get("type")
                    
                    if chunk_type == "content":
                        content = chunk.get("content", "")
                        if content:
                            full_content += content
                            response_data = {
                                "type": "content",
                                "content": content,
                                "conversation_id": conversation_id
                            }
                            yield f"data: {json.dumps(response_data)}\n\n"
                    
                    elif chunk_type == "reasoning":
                        reasoning = chunk.get("content", "")
                        if reasoning:
                            response_data = {
                                "type": "reasoning",
                                "content": reasoning
                            }
                            yield f"data: {json.dumps(response_data)}\n\n"
                    
                    elif chunk_type == "tool_calls":
                        current_tool_calls = chunk.get("tool_calls", [])
                        if current_tool_calls:
                            has_tool_calls = True
                            tool_calls_info.extend(current_tool_calls)
                            
                            for tc in current_tool_calls:
                                response_data = {
                                    "type": "tool_call",
                                    "tool_name": tc.get("name"),
                                    "tool_call_id": tc.get("id"),
                                    "arguments": tc.get("arguments")
                                }
                                yield f"data: {json.dumps(response_data)}\n\n"
                
                if has_tool_calls and current_tool_calls:
                    logger.info(f"[工具调用] 检测到 {len(current_tool_calls)} 个工具调用")
                    
                    assistant_message = {
                        "role": "assistant",
                        "content": full_content or None,
                        "tool_calls": [
                            {
                                "id": tc.get("id"),
                                "type": "function",
                                "function": {
                                    "name": tc.get("name"),
                                    "arguments": tc.get("arguments")
                                }
                            }
                            for tc in current_tool_calls
                        ]
                    }
                    full_messages.append(assistant_message)
                    
                    tool_results = await process_tool_calls(
                        db=db,
                        conversation_id=conversation_id,
                        message_id=None,
                        tool_calls=current_tool_calls
                    )
                    
                    for tr in tool_results:
                        response_data = {
                            "type": "tool_result",
                            "tool_call_id": tr.get("tool_call_id"),
                            "content": tr.get("content")
                        }
                        yield f"data: {json.dumps(response_data)}\n\n"
                        
                        full_messages.append({
                            "role": "tool",
                            "tool_call_id": tr.get("tool_call_id"),
                            "content": tr.get("content")
                        })
                    
                    full_content = ""
                else:
                    break

            logger.info(f"[LLM调用] 回复生成完成，长度: {len(full_content)} 字符")
            await save_message(db, conversation_id, "assistant", full_content)
            logger.info(f"[聊天完成] 会话ID: {conversation_id}")
            logger.info(LOG_SEPARATOR)
            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"[LLM调用] 失败: {str(e)}")
            error_data = {
                "type": "error",
                "error": str(e),
                "status": 500
            }
            yield f"data: {json.dumps(error_data)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/plain")
