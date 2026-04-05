from __future__ import annotations

import asyncio
import os
import sys

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import agent_runs, automations, chat, config, history, logs, mcp, memory, rules, skills, tools
from app.common.logging_config import get_logger, setup_logging
from app.common.security import require_api_auth
from app.core.bootstrap import ensure_default_session, ensure_runtime_schema
from app.core.database import AsyncSessionLocal, Base, engine
from app.dao.conversation_dao import ConversationDAO
from app.services.log_service import cleanup_log_handlers, setup_log_handlers
from app.tools import tool_registry
from app.tools.builtin import register_all_builtin_tools

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

setup_logging()
logger = get_logger(__name__)

DEFAULT_CONVERSATION_TITLE = "main"

app = FastAPI(title="MyClaw API", version="1.0.0")


def _parse_cors_origins() -> list[str]:
    raw = os.getenv("MYCLAW_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    origins = [item.strip() for item in raw.split(",") if item.strip()]
    return origins or ["http://localhost:5173", "http://127.0.0.1:5173"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_cors_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

protected = [Depends(require_api_auth)]
app.include_router(chat.router, prefix="/api", tags=["chat"], dependencies=protected)
app.include_router(history.router, prefix="/api", tags=["history"], dependencies=protected)
app.include_router(config.router, prefix="/api", tags=["config"], dependencies=protected)
app.include_router(memory.router, prefix="/api", tags=["memory"], dependencies=protected)
app.include_router(rules.router, prefix="/api", tags=["rules"], dependencies=protected)
app.include_router(logs.router, prefix="/api", tags=["logs"], dependencies=protected)
app.include_router(tools.router, prefix="/api", tags=["tools"], dependencies=protected)
app.include_router(skills.router, prefix="/api", tags=["skills"], dependencies=protected)
app.include_router(automations.router, prefix="/api", tags=["automations"], dependencies=protected)
app.include_router(mcp.router, prefix="/api", tags=["mcp"], dependencies=protected)
app.include_router(agent_runs.router, prefix="/api", tags=["agent-runs"], dependencies=protected)


async def ensure_default_conversation() -> None:
    async with AsyncSessionLocal() as db:
        default_session = await ensure_default_session(db)
        conversations = await ConversationDAO.list_all(db, limit=1)
        if conversations:
            return
        logger.info("[startup] creating default conversation for main session")
        await ConversationDAO.create(
            db,
            DEFAULT_CONVERSATION_TITLE,
            session_id=default_session.id,
        )


@app.on_event("startup")
async def startup_event() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await ensure_runtime_schema(engine)
    await setup_log_handlers()
    await ensure_default_conversation()

    async with AsyncSessionLocal() as db:
        await register_all_builtin_tools(tool_registry, db)
        await mcp.mcp_service.sync_runtime_tools(db)

    await automations.automation_service.start(
        AsyncSessionLocal,
        chat.agent_loop_controller.dispatch_message_for_automation,
    )

    logger.info("registered %s builtin tools", len(tool_registry.list_tools()))
    logger.info("MyClaw backend started")
    logger.info("CORS origins: %s", ", ".join(_parse_cors_origins()))
    logger.info("Docs: http://127.0.0.1:8000/docs")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await automations.automation_service.stop()
    await cleanup_log_handlers()


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "message": "MyClaw API is running.",
        "docs": "/docs",
    }
