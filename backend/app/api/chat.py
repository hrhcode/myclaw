"""
聊天API
提供聊天功能的HTTP接口
业务逻辑已委托给Service层，API层仅处理HTTP请求/响应
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.schemas import ChatRequest
from app.services.llm_service import get_llm_service
from app.services.conversation_service import ConversationService
from app.services.message_service import MessageService
from app.common.config import get_config_value
from app.common.constants import API_KEY_KEY, LLM_MODEL_KEY
from app.services.vector_search_service import hybrid_memory_search
from app.tools import tool_registry, tool_executor, tools_to_zhipu_schemas
from app.tools.builtin import get_current_time_tool
from app.common.constants import LOG_SEPARATOR
from app.dao.tool_call_dao import ToolCallDAO
from typing import List
import logging
import json

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


def build_memory_context(memory_results: List) -> str:
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


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """
    发送聊天消息并获取AI流式回复（支持工具调用）

    业务逻辑说明：
    1. 配置验证（API Key、模型参数）
    2. 会话获取/创建
    3. 消息保存
    4. 记忆搜索
    5. LLM流式对话（可能包含工具调用）
    """
    conversation_service = ConversationService()
    message_service = MessageService()

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

    try:
        conversation_id, conversation = await conversation_service.get_or_create(
            db, request.message, request.conversation_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    await message_service.save(db, conversation_id, "user", request.message)

    logger.info(LOG_SEPARATOR)
    logger.info("[记忆搜索] 开始混合记忆搜索...")

    memory_top_k = await get_config_value(db, "memory_top_k")
    memory_min_score = await get_config_value(db, "memory_min_score")
    memory_use_hybrid = await get_config_value(db, "memory_use_hybrid")
    memory_vector_weight = await get_config_value(db, "memory_vector_weight")
    memory_text_weight = await get_config_value(db, "memory_text_weight")
    memory_enable_mmr = await get_config_value(db, "memory_enable_mmr")
    memory_mmr_lambda = await get_config_value(db, "memory_mmr_lambda")
    memory_enable_temporal_decay = await get_config_value(db, "memory_enable_temporal_decay")
    memory_half_life_days = await get_config_value(db, "memory_half_life_days")

    message_history = await message_service.get_history(db, conversation_id)

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

                    tool_results = await message_service.process_tool_calls(
                        db=db,
                        conversation_id=conversation_id,
                        message_id=None,
                        tool_calls=current_tool_calls,
                        tool_executor=tool_executor
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
            assistant_message = await message_service.save(db, conversation_id, "assistant", full_content)
            if tool_calls_info:
                logger.info(f"[工具调用] 关联 {len(tool_calls_info)} 个工具调用记录到消息ID: {assistant_message.id}")
                for tc in tool_calls_info:
                    tool_call_id = tc.get("id", "")
                    await ToolCallDAO.update_message_id(db, tool_call_id, assistant_message.id)
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

    from fastapi.responses import StreamingResponse
    return StreamingResponse(generate(), media_type="text/plain")
