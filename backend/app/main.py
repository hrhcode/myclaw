"""
MyClaw 主入口
FastAPI 应用启动和路由配置
"""

import logging
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.agent import get_agent, get_session_manager
from app.config import get_config

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


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    应用生命周期管理
    
    Args:
        app: FastAPI 应用实例
    """
    config = get_config()
    
    session_manager = get_session_manager()
    await session_manager.init_db()
    
    logger.info(f"MyClaw 启动中...")
    logger.info(f"服务地址: http://{config.server.host}:{config.server.port}")
    logger.info(f"LLM 提供商: {config.llm.provider}")
    logger.info(f"LLM 模型: {config.llm.model}")
    logger.info(f"微信通道: {'启用' if config.wechat.enabled else '禁用'}")
    logger.info(f"记忆系统: {'启用' if config.memory.enabled else '禁用'}")

    yield

    logger.info("MyClaw 关闭中...")


app = FastAPI(
    title="MyClaw",
    description="极简 AI 助手 - 面向个人用户的微信 AI 机器人",
    version="0.1.0",
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
    return {"status": "ok", "service": "myclaw", "version": "0.1.0"}


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
    }


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
