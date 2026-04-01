"""
聊天 API
提供聊天功能的 HTTP 接口。
"""
import json
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent_loop import AgentLoopController
from app.core.database import get_db
from app.schemas.schemas import ChatRequest
from app.tools import tool_registry
from app.tools.builtin import get_current_time_tool

router = APIRouter()
logger = logging.getLogger(__name__)
agent_loop_controller = AgentLoopController()


def register_builtin_tools() -> None:
    """注册最基础的内置工具。"""
    if not tool_registry.get_tool("get_current_time"):
        tool_registry.register(get_current_time_tool())
        logger.info("[工具注册] 已注册内置工具 get_current_time")


register_builtin_tools()


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """发送聊天消息并获取 AI 流式回复。"""

    async def generate():
        try:
            async for event in agent_loop_controller.run_stream(request, db):
                if event.get("type") == "done":
                    continue
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except ValueError as e:
            error_data = {"type": "error", "error": str(e), "status": 404}
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except RuntimeError as e:
            error_data = {"type": "error", "error": str(e), "status": 500}
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.exception("[chat_stream] 生成流式回复失败")
            error_data = {"type": "error", "error": str(e), "status": 500}
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/plain")
