"""
MyClaw 主入口
FastAPI 应用启动和路由配置
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    应用生命周期管理
    
    Args:
        app: FastAPI 应用实例
    """
    config = get_config()
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
