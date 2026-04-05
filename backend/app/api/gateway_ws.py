from __future__ import annotations

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.channels.ws_handler import get_gateway_ws_handler

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/gateway/ws")
async def gateway_ws(websocket: WebSocket):
    """WebSocket 端点 — 实时推送通道消息事件。"""
    handler = get_gateway_ws_handler()

    await websocket.accept()
    handler.add_connection(websocket)

    logger.info(
        "Gateway WS client connected, total: %d", handler.connection_count
    )

    try:
        while True:
            data = await websocket.receive_text()
            # 支持心跳 ping
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_text(
                        json.dumps({"type": "pong"}, ensure_ascii=False)
                    )
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        handler.remove_connection(websocket)
        logger.info(
            "Gateway WS client disconnected, total: %d",
            handler.connection_count,
        )
    except Exception:
        handler.remove_connection(websocket)
        logger.exception("Gateway WS connection error")
