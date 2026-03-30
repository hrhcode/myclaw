from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import chat, history, config, memory, logs, tools
from app.core.database import engine, Base, AsyncSessionLocal
from app.services.log_service import setup_log_handlers
from app.common.logging_config import setup_logging, get_logger
from app.tools import tool_registry
from app.tools.builtin import register_all_builtin_tools
from app.dao.conversation_dao import ConversationDAO
import logging

setup_logging()
logger = get_logger(__name__)

DEFAULT_CONVERSATION_TITLE = "main"

app = FastAPI(title="AI对话助手API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api", tags=["聊天"])
app.include_router(history.router, prefix="/api", tags=["历史记录"])
app.include_router(config.router, prefix="/api", tags=["配置管理"])
app.include_router(memory.router, prefix="/api", tags=["记忆搜索"])
app.include_router(logs.router, prefix="/api", tags=["日志"])
app.include_router(tools.router, prefix="/api", tags=["工具管理"])


async def ensure_default_conversation():
    """
    确保至少存在一个默认会话
    如果没有任何会话，则创建名为"main"的默认会话
    """
    async with AsyncSessionLocal() as db:
        conversations = await ConversationDAO.list_all(db, limit=1)
        if not conversations:
            logger.info("[初始化] 未发现任何会话，创建默认会话 'main'")
            await ConversationDAO.create(db, DEFAULT_CONVERSATION_TITLE)
            logger.info("[初始化] 默认会话 'main' 创建成功")
        else:
            logger.debug(f"[初始化] 已存在 {len(conversations)} 个会话，无需创建默认会话")


@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await setup_log_handlers()

    await ensure_default_conversation()

    register_all_builtin_tools(tool_registry)
    logger.info(f"已注册 {len(tool_registry.list_tools())} 个内置工具")

    logger.info("=" * 50)
    logger.info("MyClaw AI对话助手 后端服务启动")
    logger.info("=" * 50)
    logger.info(f"数据库: SQLite (async)")
    logger.info(f"API路由:")
    logger.info(f"  - /api/chat/stream (聊天)")
    logger.info(f"  - /api/conversations (会话管理)")
    logger.info(f"  - /api/config (配置管理)")
    logger.info(f"  - /api/memory (记忆搜索)")
    logger.info(f"  - /api/logs (日志)")
    logger.info(f"  - /api/tools (工具管理)")
    logger.info(f"  - /api/logs/stream (日志WebSocket)")
    logger.info(f"  - /api/logs/history (历史日志)")
    logger.info(f"  - /api/logs/stats (日志统计)")
    logger.info(f"CORS: 已启用 (允许所有来源)")
    logger.info(f"API文档: http://127.0.0.1:8000/docs")
    logger.info("=" * 50)

@app.get("/")
async def root():
    return {"message": "MyClaw AI对话助手API服务已启动", "docs": "/docs"}
