"""
MyClaw 主入口
FastAPI 应用启动和路由配置，集成 Gateway 架构
"""

import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, AsyncGenerator, Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, StreamingResponse
from pydantic import BaseModel, Field

from app.agent import get_agent, get_session_manager
from app.channels.qq import QQChannel
from app.channels.web import get_web_channel
from app.channels.wechat import WechatChannel
from app.config import get_config, get_config_path, reload_config, save_config
from app.gateway import get_gateway

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ChatMessage(BaseModel):
    """聊天消息模型"""

    role: str
    content: str


class ChatRequest(BaseModel):
    """聊天请求模型"""

    messages: list[ChatMessage]
    model: Optional[str] = None
    stream: bool = False
    session_id: Optional[str] = None


class ChatChoice(BaseModel):
    """聊天选择模型"""

    index: int = 0
    message: ChatMessage
    finish_reason: str = "stop"


class ChatResponse(BaseModel):
    """聊天响应模型"""

    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[ChatChoice]


class SessionInfo(BaseModel):
    """会话信息模型"""

    id: str
    channel: str
    message_count: int
    created_at: str
    updated_at: str


class SessionListResponse(BaseModel):
    """会话列表响应模型"""

    sessions: list[SessionInfo]
    total: int


class ToolCallInfo(BaseModel):
    """工具调用信息模型"""

    id: str
    type: str = "function"
    function: dict[str, Any] = Field(default_factory=dict)
    duration_ms: Optional[int] = None


class MessageInfo(BaseModel):
    """消息信息模型"""

    id: int
    role: str
    content: str
    timestamp: str
    tool_calls: Optional[list[ToolCallInfo]] = None
    tool_call_id: Optional[str] = None


class MessageListResponse(BaseModel):
    """消息列表响应模型"""

    session_id: str
    messages: list[MessageInfo]
    total: int


class SessionCreateRequest(BaseModel):
    """创建会话请求模型"""

    session_id: Optional[str] = None
    channel: str = "web"


class SessionCreateResponse(BaseModel):
    """创建会话响应模型"""

    session_id: str
    created: bool


_gateway_instance = None
_wechat_channel: Optional[WechatChannel] = None
_qq_channel: Optional[QQChannel] = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    应用生命周期管理
    
    Args:
        app: FastAPI 应用实例
    """
    global _gateway_instance, _wechat_channel, _qq_channel
    
    config = get_config()
    
    session_manager = get_session_manager()
    await session_manager.init_db()
    
    logger.info(f"MyClaw 启动中...")
    logger.info(f"服务地址: http://{config.server.host}:{config.server.port}")
    logger.info(f"LLM 提供商: {config.llm.provider}")
    logger.info(f"LLM 模型: {config.llm.model}")
    
    if config.gateway.enabled:
        gateway = get_gateway()
        _gateway_instance = gateway
        
        agent = get_agent()
        gateway.set_agent(agent)
        gateway.set_session_manager(session_manager)
        
        if config.channels.web.enabled:
            web_channel = get_web_channel()
            await gateway.register_channel(web_channel)
            logger.info("Web 通道已注册")
        
        if config.channels.qq.enabled:
            _qq_channel = QQChannel(
                api_url=config.channels.qq.api_url,
                access_token=config.channels.qq.access_token,
            )
            await gateway.register_channel(_qq_channel)
            logger.info("QQ 通道已注册")
        
        await gateway.start()
        logger.info("Gateway 已启动")
    
    logger.info(f"记忆系统: {'启用' if config.memory.enabled else '禁用'}")
    
    yield
    
    if _gateway_instance:
        await _gateway_instance.stop()
        logger.info("Gateway 已停止")
    
    logger.info("MyClaw 关闭中...")


app = FastAPI(
    title="MyClaw",
    description="极简 AI 助手 - 面向个人用户的 AI 机器人",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict:
    """
    健康检查接口
    
    Returns:
        健康状态信息
    """
    return {"status": "ok", "service": "myclaw", "version": "0.2.0"}


@app.get("/")
async def root() -> dict:
    """
    根路径
    
    Returns:
        欢迎信息
    """
    return {
        "message": "Welcome to MyClaw",
        "docs": "/docs",
        "health": "/health",
        "gateway": "/api/gateway/status",
    }


@app.get("/api/gateway/status")
async def get_gateway_status() -> dict:
    """
    获取 Gateway 状态
    
    Returns:
        Gateway 状态信息
    """
    if not _gateway_instance:
        return {"running": False, "error": "Gateway 未启用"}
    
    return _gateway_instance.status.to_dict()


@app.get("/api/gateway/info")
async def get_gateway_info() -> dict:
    """
    获取 Gateway 详细信息
    
    Returns:
        Gateway 详细信息
    """
    if not _gateway_instance:
        return {"error": "Gateway 未启用"}
    
    status = _gateway_instance.status
    return {
        "version": "0.2.0",
        "uptime_seconds": status.uptime_seconds,
        "started_at": status.started_at.isoformat() if status.started_at else None,
        "channels": list(status.channels.keys()),
        "sessions_count": status.sessions_count,
    }


@app.get("/api/channels")
async def list_channels() -> dict:
    """
    获取所有通道列表
    
    Returns:
        通道列表
    """
    if not _gateway_instance:
        return {"channels": [], "error": "Gateway 未启用"}
    
    channels = _gateway_instance.get_all_channels_status()
    return {
        "channels": [
            {
                "name": name,
                "status": status.to_dict(),
            }
            for name, status in channels.items()
        ]
    }


@app.get("/api/channels/{channel_name}")
async def get_channel_status(channel_name: str) -> dict:
    """
    获取指定通道状态
    
    Args:
        channel_name: 通道名称
        
    Returns:
        通道状态
    """
    if not _gateway_instance:
        raise HTTPException(status_code=503, detail="Gateway 未启用")
    
    status = _gateway_instance.get_channel_status(channel_name)
    if not status:
        raise HTTPException(status_code=404, detail="通道不存在")
    
    return status.to_dict()


@app.post("/api/channels/{channel_name}/start")
async def start_channel(channel_name: str) -> dict:
    """
    启动指定通道
    
    Args:
        channel_name: 通道名称
        
    Returns:
        操作结果
    """
    if not _gateway_instance:
        raise HTTPException(status_code=503, detail="Gateway 未启用")
    
    if channel_name not in _gateway_instance.channels:
        raise HTTPException(status_code=404, detail="通道不存在")
    
    channel = _gateway_instance.channels[channel_name]
    await channel.start()
    return {"status": "ok", "message": f"通道 {channel_name} 已启动"}


@app.post("/api/channels/{channel_name}/stop")
async def stop_channel(channel_name: str) -> dict:
    """
    停止指定通道
    
    Args:
        channel_name: 通道名称
        
    Returns:
        操作结果
    """
    if not _gateway_instance:
        raise HTTPException(status_code=503, detail="Gateway 未启用")
    
    if channel_name not in _gateway_instance.channels:
        raise HTTPException(status_code=404, detail="通道不存在")
    
    channel = _gateway_instance.channels[channel_name]
    await channel.stop()
    return {"status": "ok", "message": f"通道 {channel_name} 已停止"}


class ChannelConfigUpdate(BaseModel):
    """通道配置更新模型"""
    enabled: Optional[bool] = None
    api_url: Optional[str] = None
    access_token: Optional[str] = None
    corp_id: Optional[str] = None
    agent_id: Optional[str] = None
    secret: Optional[str] = None
    token: Optional[str] = None
    encoding_aes_key: Optional[str] = None


@app.put("/api/channels/{channel_name}/config")
async def update_channel_config(channel_name: str, config_update: ChannelConfigUpdate) -> dict:
    """
    更新通道配置
    
    Args:
        channel_name: 通道名称
        config_update: 配置更新
        
    Returns:
        操作结果
    """
    config = get_config()
    
    if channel_name == "web":
        if config_update.enabled is not None:
            config.channels.web.enabled = config_update.enabled
    elif channel_name == "qq":
        if config_update.enabled is not None:
            config.channels.qq.enabled = config_update.enabled
        if config_update.api_url is not None:
            config.channels.qq.api_url = config_update.api_url
        if config_update.access_token is not None:
            config.channels.qq.access_token = config_update.access_token
    elif channel_name == "wechat":
        if config_update.enabled is not None:
            config.channels.wechat.enabled = config_update.enabled
        if config_update.corp_id is not None:
            config.channels.wechat.corp_id = config_update.corp_id
        if config_update.agent_id is not None:
            config.channels.wechat.agent_id = config_update.agent_id
        if config_update.secret is not None:
            config.channels.wechat.secret = config_update.secret
        if config_update.token is not None:
            config.channels.wechat.token = config_update.token
        if config_update.encoding_aes_key is not None:
            config.channels.wechat.encoding_aes_key = config_update.encoding_aes_key
    else:
        raise HTTPException(status_code=404, detail="通道不存在")
    
    save_config(config)
    
    return {"status": "ok", "message": f"通道 {channel_name} 配置已更新"}


@app.get("/api/config")
async def get_app_config() -> dict:
    """
    获取应用配置
    
    Returns:
        应用配置
    """
    config = get_config()
    return config.model_dump()


class ConfigUpdateRequest(BaseModel):
    """配置更新请求模型"""
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    llm_api_key: Optional[str] = None
    memory_enabled: Optional[bool] = None
    embedding_provider: Optional[str] = None
    embedding_api_key: Optional[str] = None
    embedding_base_url: Optional[str] = None
    vector_weight: Optional[float] = None
    fts_weight: Optional[float] = None
    min_score: Optional[float] = None
    system_prompt: Optional[str] = None


@app.put("/api/config")
async def update_app_config(request: ConfigUpdateRequest) -> dict:
    """
    更新应用配置
    
    Args:
        request: 配置更新请求
        
    Returns:
        操作结果
    """
    config = get_config()
    
    if request.llm_provider is not None:
        config.llm.provider = request.llm_provider
    if request.llm_model is not None:
        config.llm.model = request.llm_model
    if request.llm_api_key is not None:
        config.llm.api_key = request.llm_api_key
    if request.memory_enabled is not None:
        config.memory.enabled = request.memory_enabled
    if request.embedding_provider is not None:
        config.memory.embedding.provider = request.embedding_provider
    if request.embedding_api_key is not None:
        config.memory.embedding.api_key = request.embedding_api_key
    if request.embedding_base_url is not None:
        config.memory.embedding.base_url = request.embedding_base_url
    if request.vector_weight is not None:
        config.memory.hybrid_search.vector_weight = request.vector_weight
    if request.fts_weight is not None:
        config.memory.hybrid_search.fts_weight = request.fts_weight
    if request.min_score is not None:
        config.memory.hybrid_search.min_score = request.min_score
    if request.system_prompt is not None:
        config.agent.system_prompt = request.system_prompt
    
    save_config(config)
    
    return {"status": "ok", "message": "配置已更新"}


@app.post("/api/config/reload")
async def reload_app_config() -> dict:
    """
    重新加载配置
    
    Returns:
        操作结果
    """
    reload_config()
    return {"status": "ok", "message": "配置已重新加载"}


@app.get("/api/tools")
async def list_tools() -> dict:
    """
    获取工具列表
    
    Returns:
        工具列表
    """
    from app.agent.tools import get_tool_registry
    
    registry = get_tool_registry()
    tools = registry.list_tools()
    
    return {
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
                "enabled": registry.is_enabled(tool.name),
            }
            for tool in tools
        ]
    }


class ToolEnabledRequest(BaseModel):
    """工具启用请求模型"""
    enabled: bool


@app.put("/api/tools/{tool_name}/enabled")
async def set_tool_enabled(tool_name: str, request: ToolEnabledRequest) -> dict:
    """
    设置工具启用状态
    
    Args:
        tool_name: 工具名称
        request: 启用请求
        
    Returns:
        操作结果
    """
    from app.agent.tools import get_tool_registry
    
    registry = get_tool_registry()
    
    if not registry.get(tool_name):
        raise HTTPException(status_code=404, detail="工具不存在")
    
    registry.set_enabled(tool_name, request.enabled)
    
    return {"status": "ok", "message": f"工具 {tool_name} 已{'启用' if request.enabled else '禁用'}"}


@app.get("/api/memories")
async def list_memories(
    query: str = Query(default="", description="搜索关键词"),
    session_id: str = Query(default="", description="会话ID过滤"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict:
    """
    获取记忆列表
    
    Args:
        query: 搜索关键词
        session_id: 会话ID过滤
        limit: 返回数量限制
        offset: 偏移量
        
    Returns:
        记忆列表
    """
    from app.storage.database import get_database
    
    db = get_database()
    
    if query:
        memories = await db.search_memories(query, session_id=session_id or None, limit=limit)
    else:
        memories = await db.list_all_messages(limit=limit, offset=offset, session_id=session_id or None)
    
    total = await db.count_all_messages()
    
    return {
        "memories": memories,
        "total": total,
    }


@app.get("/api/memories/stats")
async def get_memory_stats() -> dict:
    """
    获取记忆统计
    
    Returns:
        记忆统计信息
    """
    from app.storage.database import get_database
    
    db = get_database()
    
    total_messages = await db.count_all_messages()
    total_sessions = await db.count_sessions()
    
    return {
        "total_messages": total_messages,
        "total_sessions": total_sessions,
    }


@app.delete("/api/memories/{message_id}")
async def delete_memory(message_id: int) -> dict:
    """
    删除单条记忆
    
    Args:
        message_id: 消息ID
        
    Returns:
        操作结果
    """
    from app.storage.database import get_database
    
    db = get_database()
    deleted = await db.delete_message(message_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="消息不存在")
    
    return {"status": "ok", "message": "记忆已删除"}


@app.delete("/api/memories")
async def clear_all_memories() -> dict:
    """
    清空所有记忆
    
    Returns:
        操作结果
    """
    from app.storage.database import get_database
    
    db = get_database()
    await db.clear_all_messages()
    
    return {"status": "ok", "message": "所有记忆已清空"}


@app.get("/api/sessions")
async def list_sessions_api(
    channel: str = Query(default="", description="通道过滤"),
    limit: int = Query(default=50, ge=1, le=100),
) -> dict:
    """
    获取会话列表
    
    Args:
        channel: 通道过滤
        limit: 返回数量限制
        
    Returns:
        会话列表
    """
    from app.storage.database import get_database
    
    db = get_database()
    sessions = await db.list_sessions(limit=limit)
    total = await db.count_sessions()
    
    result_sessions = []
    for s in sessions:
        if channel and s.get("channel") != channel:
            continue
        result_sessions.append({
            "id": s["id"],
            "channel": s.get("channel") or "web",
            "message_count": s.get("message_count") or 0,
            "created_at": s.get("created_at") or "",
            "updated_at": s.get("updated_at") or "",
        })
    
    return {
        "sessions": result_sessions,
        "total": total,
    }


@app.get("/api/sessions/{session_id}")
async def get_session_api(session_id: str) -> dict:
    """
    获取会话详情
    
    Args:
        session_id: 会话 ID
        
    Returns:
        会话详情
    """
    session_manager = get_session_manager()
    session = await session_manager.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    return session


@app.delete("/api/sessions/{session_id}")
async def delete_session_api(session_id: str) -> dict:
    """
    删除会话
    
    Args:
        session_id: 会话 ID
        
    Returns:
        删除结果
    """
    session_manager = get_session_manager()
    
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    await session_manager.clear_session(session_id)
    return {"status": "ok", "message": "会话已删除"}


@app.get("/v1/sessions", response_model=SessionListResponse)
async def list_sessions(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> SessionListResponse:
    """
    获取会话列表 (兼容旧 API)
    
    Args:
        limit: 返回数量限制
        offset: 偏移量
        
    Returns:
        会话列表
    """
    from app.storage.database import get_database
    
    db = get_database()
    sessions = await db.list_sessions(limit=limit, offset=offset)
    total = await db.count_sessions()
    
    return SessionListResponse(
        sessions=[
            SessionInfo(
                id=s["id"],
                channel=s["channel"] or "web",
                message_count=s["message_count"] or 0,
                created_at=s["created_at"] or "",
                updated_at=s["updated_at"] or "",
            )
            for s in sessions
        ],
        total=total,
    )


@app.post("/v1/sessions", response_model=SessionCreateResponse)
async def create_session(request: SessionCreateRequest) -> SessionCreateResponse:
    """
    创建新会话
    
    Args:
        request: 创建会话请求
        
    Returns:
        创建会话响应
    """
    session_id = request.session_id or str(uuid.uuid4())
    session_manager = get_session_manager()
    
    existing = await session_manager.get_session(session_id)
    if existing:
        return SessionCreateResponse(session_id=session_id, created=False)
    
    await session_manager.create_session(session_id, request.channel)
    return SessionCreateResponse(session_id=session_id, created=True)


@app.get("/v1/sessions/{session_id}/messages", response_model=MessageListResponse)
async def get_session_messages(
    session_id: str,
    limit: int = Query(default=50, ge=1, le=200),
) -> MessageListResponse:
    """
    获取会话的历史消息
    
    Args:
        session_id: 会话 ID
        limit: 返回数量限制
        
    Returns:
        消息列表
    """
    session_manager = get_session_manager()
    
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    messages = await session_manager.get_messages(session_id, limit=limit)
    
    return MessageListResponse(
        session_id=session_id,
        messages=[
            MessageInfo(
                id=m["id"],
                role=m["role"],
                content=m["content"],
                timestamp=m["timestamp"] or "",
                tool_calls=[
                    ToolCallInfo(
                        id=tc["id"],
                        type=tc.get("type", "function"),
                        function=tc.get("function", {}),
                        duration_ms=tc.get("duration_ms"),
                    )
                    for tc in m["tool_calls"]
                ] if m["tool_calls"] else None,
                tool_call_id=m.get("tool_call_id"),
            )
            for m in messages
        ],
        total=len(messages),
    )


@app.delete("/v1/sessions/{session_id}")
async def delete_session(session_id: str) -> dict:
    """
    删除会话
    
    Args:
        session_id: 会话 ID
        
    Returns:
        删除结果
    """
    session_manager = get_session_manager()
    
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    await session_manager.clear_session(session_id)
    return {"status": "ok", "message": "会话已删除"}


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest) -> ChatResponse:
    """
    OpenAI 兼容的聊天接口
    
    Args:
        request: 聊天请求
        
    Returns:
        聊天响应
    """
    import time
    
    config = get_config()
    agent = get_agent()
    
    session_id = request.session_id or str(uuid.uuid4())
    
    if not request.messages:
        raise HTTPException(status_code=400, detail="消息列表不能为空")
    
    last_message = request.messages[-1]
    
    if request.stream:
        return StreamingResponse(
            _stream_response(session_id, last_message.content, config.llm.model),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    
    response_text = await agent.process_message(session_id, last_message.content)
    
    return ChatResponse(
        id=f"chatcmpl-{uuid.uuid4().hex[:8]}",
        created=int(time.time()),
        model=request.model or config.llm.model,
        choices=[
            ChatChoice(
                message=ChatMessage(role="assistant", content=response_text),
            )
        ],
    )


async def _stream_response(
    session_id: str,
    message: str,
    model: str,
) -> AsyncGenerator[str, None]:
    """
    流式响应生成器
    
    Args:
        session_id: 会话 ID
        message: 用户消息
        model: 模型名称
        
    Yields:
        SSE 格式的流式数据
    """
    import json
    import time
    
    agent = get_agent()
    
    async for chunk in agent.process_message_stream(session_id, message):
        if isinstance(chunk, dict):
            if chunk.get("type") == "tool_call":
                data = {
                    "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": model,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {
                                "tool_calls": [chunk["tool_call"]]
                            },
                            "finish_reason": None,
                        }
                    ],
                }
                yield f"data: {json.dumps(data)}\n\n"
            elif chunk.get("type") == "tool_result":
                data = {
                    "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": model,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {
                                "tool_calls": [chunk["tool_call"]]
                            },
                            "finish_reason": None,
                        }
                    ],
                }
                yield f"data: {json.dumps(data)}\n\n"
        else:
            data = {
                "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": chunk},
                        "finish_reason": None,
                    }
                ],
            }
            yield f"data: {json.dumps(data)}\n\n"
    
    final_data = {
        "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "delta": {},
                "finish_reason": "stop",
            }
        ],
    }
    yield f"data: {json.dumps(final_data)}\n\n"
    yield "data: [DONE]\n\n"


def get_wechat_channel() -> WechatChannel:
    """
    获取微信通道实例
    
    Returns:
        WechatChannel 实例
    """
    global _wechat_channel
    if _wechat_channel is None:
        _wechat_channel = WechatChannel()
    return _wechat_channel


@app.get("/wechat/callback")
async def wechat_verify(
    msg_signature: str = Query(..., alias="msg_signature"),
    timestamp: str = Query(...),
    nonce: str = Query(...),
    echostr: str = Query(...),
) -> PlainTextResponse:
    """
    微信回调 URL 验证
    
    Args:
        msg_signature: 签名
        timestamp: 时间戳
        nonce: 随机数
        echostr: 随机字符串
        
    Returns:
        echostr 原样返回
    """
    config = get_config()
    if not config.channels.wechat.enabled:
        raise HTTPException(status_code=403, detail="微信通道未启用")
    
    channel = get_wechat_channel()
    
    if channel.verify_signature(msg_signature, timestamp, nonce, echostr):
        logger.info("微信回调验证成功")
        return PlainTextResponse(content=echostr)
    else:
        logger.warning("微信回调验证失败")
        raise HTTPException(status_code=403, detail="签名验证失败")


@app.post("/wechat/callback")
async def wechat_message(
    request: Request,
    msg_signature: str = Query(..., alias="msg_signature"),
    timestamp: str = Query(...),
    nonce: str = Query(...),
) -> PlainTextResponse:
    """
    微信消息回调处理
    
    Args:
        request: 请求对象
        msg_signature: 签名
        timestamp: 时间戳
        nonce: 随机数
        
    Returns:
        处理结果
    """
    config = get_config()
    if not config.channels.wechat.enabled:
        raise HTTPException(status_code=403, detail="微信通道未启用")
    
    channel = get_wechat_channel()
    
    body = await request.body()
    xml_content = body.decode("utf-8")
    
    if not channel.verify_signature(msg_signature, timestamp, nonce):
        logger.warning("微信消息签名验证失败")
        raise HTTPException(status_code=403, detail="签名验证失败")
    
    try:
        message = channel.parse_message(xml_content)
        
        msg_type = message.get("MsgType", "")
        if msg_type != "text":
            return PlainTextResponse(content="success")
        
        content = message.get("Content", "")
        from_user = message.get("FromUserName", "")
        
        logger.info(f"收到微信消息: from={from_user}, content={content[:50]}...")
        
        session_id = channel.get_session_id(from_user)
        agent = get_agent()
        
        response_text = await agent.process_message(session_id, content, channel="wechat")
        
        await channel.send_message(from_user, response_text)
        
        return PlainTextResponse(content="success")
        
    except Exception as e:
        logger.error(f"处理微信消息失败: {e}")
        return PlainTextResponse(content="success")


def main() -> None:
    """
    启动服务器
    """
    import uvicorn

    config = get_config()
    uvicorn.run(
        "app.main:app",
        host=config.server.host,
        port=config.server.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
