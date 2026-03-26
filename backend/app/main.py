from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import chat, history, config, memory
from app.database import engine, Base
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("=" * 50)
    logger.info("MyClaw AI对话助手 后端服务启动")
    logger.info("=" * 50)
    logger.info(f"数据库: SQLite (async)")
    logger.info(f"API路由:")
    logger.info(f"  - /api/chat/stream (聊天)")
    logger.info(f"  - /api/conversations (会话管理)")
    logger.info(f"  - /api/config (配置管理)")
    logger.info(f"  - /api/memory (记忆搜索)")
    logger.info(f"CORS: 已启用 (允许所有来源)")
    logger.info(f"API文档: http://127.0.0.1:8000/docs")
    logger.info("=" * 50)

@app.get("/")
async def root():
    return {"message": "MyClaw AI对话助手API服务已启动", "docs": "/docs"}
