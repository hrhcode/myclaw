from __future__ import annotations

import json
import logging
from typing import Any, Dict, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class GatewayWSHandler:
    """管理 Gateway WebSocket 连接池和事件广播。"""

    def __init__(self) -> None:
        self._connections: Set[WebSocket] = set()

    @property
    def connection_count(self) -> int:
        return len(self._connections)

    def add_connection(self, ws: WebSocket) -> None:
        self._connections.add(ws)

    def remove_connection(self, ws: WebSocket) -> None:
        self._connections.discard(ws)

    async def broadcast(self, event: Dict[str, Any]) -> None:
        """向所有已连接客户端广播事件。单个连接失败不影响其他连接。"""
        if not self._connections:
            return

        payload = json.dumps(event, ensure_ascii=False)
        dead: list[WebSocket] = []

        for ws in self._connections:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)

        for ws in dead:
            self._connections.discard(ws)


# 模块级单例
_ws_handler: GatewayWSHandler | None = None


def get_gateway_ws_handler() -> GatewayWSHandler:
    global _ws_handler
    if _ws_handler is None:
        _ws_handler = GatewayWSHandler()
    return _ws_handler
