"""QQ 官方机器人 API 客户端。

对接 QQ 官方机器人 API（api.sgroup.qq.com），支持：
- AppId + AppSecret → access_token 自动获取和刷新
- WebSocket 事件监听（频道消息、私信）
- REST API 发送消息（频道、私信）
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Awaitable, Callable, Dict, Optional

import aiohttp

logger = logging.getLogger(__name__)

# QQ 官方 API 常量
_TOKEN_URL = "https://bots.qq.com/app/getAppAccessToken"
_API_BASE = "https://api.sgroup.qq.com"
_GATEWAY_URL = f"{_API_BASE}/gateway/bot"

# WebSocket OpCode
OP_HEARTBEAT = 1
OP_IDENTIFY = 2
OP_DISPATCH = 0
OP_HELLO = 10
OP_HEARTBEAT_ACK = 11
OP_RECONNECT = 7
OP_INVALID_SESSION = 9

# 消息长度限制
MAX_MSG_LENGTH = 2000


class QQOfficialClient:
    """QQ 官方机器人 API 客户端。"""

    def __init__(
        self,
        app_id: str,
        app_secret: str,
        on_message: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
    ) -> None:
        self._app_id = app_id
        self._app_secret = app_secret
        self._on_message = on_message

        # Token 状态
        self._access_token: str = ""
        self._token_expires_at: float = 0

        # WebSocket 状态
        self._ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._running = False
        self._listen_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None

        # Bot 信息
        self._bot_id: Optional[str] = None

        # WebSocket 会话信息（用于断线恢复）
        self._session_id: Optional[str] = None
        self._last_seq: int = 0
        self._gateway_url: Optional[str] = None

    @property
    def bot_id(self) -> Optional[str]:
        return self._bot_id

    # ── Token 管理 ──────────────────────────────────────────

    async def _ensure_token(self) -> str:
        """确保 access_token 有效，过期前自动刷新。"""
        now = time.time()
        # 提前 5 分钟刷新
        if self._access_token and now < self._token_expires_at - 300:
            return self._access_token
        await self._refresh_token()
        return self._access_token

    async def _refresh_token(self) -> None:
        """用 AppId + AppSecret 获取新的 access_token。"""
        payload = {
            "appId": self._app_id,
            "clientSecret": self._app_secret,
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    _TOKEN_URL,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        raise RuntimeError(
                            f"获取 access_token 失败: HTTP {resp.status} - {text}"
                        )
                    data = await resp.json()
                    self._access_token = data.get("access_token", "")
                    expires_in = int(data.get("expires_in", 7200))
                    self._token_expires_at = time.time() + expires_in
                    logger.info(
                        "QQ access_token 已刷新，有效期 %d 秒", expires_in
                    )
        except Exception:
            logger.exception("获取 QQ access_token 失败")
            raise

    def _auth_headers(self) -> Dict[str, str]:
        """构建 REST API 鉴权请求头。"""
        return {
            "Authorization": f"QQBot {self._access_token}",
            "Content-Type": "application/json",
        }

    # ── 生命周期 ────────────────────────────────────────────

    async def start(self) -> None:
        """启动客户端：获取 token → 连接 WebSocket → 鉴权 → 开始监听。"""
        self._running = True
        await self._ensure_token()

        # 获取 WebSocket 网关地址
        await self._fetch_gateway()

        self._session = aiohttp.ClientSession()
        await self._connect()
        await self._identify()
        self._listen_task = asyncio.create_task(self._listen_loop())
        logger.info("QQOfficialClient 已启动")

    async def stop(self) -> None:
        """停止客户端，断开连接并清理资源。"""
        self._running = False
        for task in (self._listen_task, self._heartbeat_task):
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        if self._ws and not self._ws.closed:
            await self._ws.close()
        if self._session and not self._session.closed:
            await self._session.close()
        self._listen_task = None
        self._heartbeat_task = None
        self._ws = None
        self._session = None
        logger.info("QQOfficialClient 已停止")

    async def health_check(self) -> bool:
        return self._ws is not None and not self._ws.closed

    # ── WebSocket 连接 ──────────────────────────────────────

    async def _fetch_gateway(self) -> None:
        """从 API 获取 WebSocket 网关地址。"""
        token = await self._ensure_token()
        headers = self._auth_headers()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    _GATEWAY_URL,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        raise RuntimeError(
                            f"获取 gateway 失败: HTTP {resp.status} - {text}"
                        )
                    data = await resp.json()
                    self._gateway_url = data.get("url", "")
                    logger.info("获取到 WebSocket 网关: %s", self._gateway_url)
        except Exception:
            logger.exception("获取 WebSocket 网关地址失败")
            raise

    async def _connect(self) -> None:
        """连接 WebSocket 并发送 IDENTIFY。"""
        if not self._gateway_url:
            await self._fetch_gateway()

        # gateway URL 需要拼接参数
        ws_url = self._gateway_url
        if "?" not in ws_url:
            token = await self._ensure_token()
            ws_url += f"?access_token={token}"

        try:
            self._ws = await self._session.ws_connect(
                ws_url,
                timeout=aiohttp.ClientTimeout(total=30),
            )
            logger.info("WebSocket 已连接: %s", ws_url)
        except Exception as exc:
            logger.error("WebSocket 连接失败: %s", exc)
            raise

    async def _identify(self) -> None:
        """发送鉴权帧。"""
        token = await self._ensure_token()
        intents = (1 << 30)   # PUBLIC_GUILD_MESSAGES - 频道 @ 消息
        intents |= (1 << 12)  # DIRECT_MESSAGE - 频道私信
        intents |= (1 << 0)   # GUILDS - 频道事件
        intents |= (1 << 25)  # GROUP_AND_C2C_EVENT - QQ群聊/单聊事件

        identify = {
            "op": OP_IDENTIFY,
            "d": {
                "token": f"QQBot {token}",
                "intents": intents,
                "shard": [0, 1],
                "properties": {},
            },
        }
        await self._ws.send_json(identify)
        logger.info("已发送 IDENTIFY 鉴权帧，intents=%d", intents)

    async def _resume(self) -> None:
        """发送恢复帧（断线重连）。"""
        token = await self._ensure_token()
        resume = {
            "op": 6,  # OP_RESUME
            "d": {
                "token": f"QQBot {token}",
                "session_id": self._session_id,
                "seq": self._last_seq,
            },
        }
        await self._ws.send_json(resume)
        logger.info("已发送 RESUME 恢复帧")

    async def _start_heartbeat(self, interval: float) -> None:
        """启动定时心跳。"""
        try:
            while self._running and self._ws and not self._ws.closed:
                await asyncio.sleep(interval)
                if self._ws and not self._ws.closed:
                    heartbeat = {"op": OP_HEARTBEAT, "d": self._last_seq}
                    await self._ws.send_json(heartbeat)
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.debug("心跳发送异常", exc_info=True)

    # ── WebSocket 监听循环 ──────────────────────────────────

    async def _listen_loop(self) -> None:
        """WebSocket 消息监听循环，支持自动重连。"""
        reconnect_delay = 1
        max_delay = 60
        can_resume = False

        while self._running:
            try:
                if self._ws is None or self._ws.closed:
                    if can_resume and self._session_id:
                        await self._connect()
                        await self._resume()
                    else:
                        await self._connect()
                        await self._identify()
                    reconnect_delay = 1

                async for msg in self._ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        try:
                            data = json.loads(msg.data)
                            result = await self._handle_event(data)
                            # 处理重连/无效会话的标记
                            if result == "reconnect":
                                can_resume = True
                                break
                            elif result == "invalid_session":
                                can_resume = False
                                break
                        except Exception:
                            logger.exception("处理 WebSocket 事件异常")
                    elif msg.type in (
                        aiohttp.WSMsgType.CLOSED,
                        aiohttp.WSMsgType.ERROR,
                    ):
                        logger.warning("WebSocket 连接关闭/错误，准备重连")
                        break

            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("WebSocket 监听异常")

            # 停止心跳任务
            if self._heartbeat_task:
                self._heartbeat_task.cancel()
                self._heartbeat_task = None

            if self._running:
                logger.info("%d 秒后重连...", reconnect_delay)
                await asyncio.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 2, max_delay)

    async def _handle_event(self, data: Dict[str, Any]) -> Optional[str]:
        """处理 WebSocket 事件。返回特殊指令字符串或 None。"""
        op = data.get("op")

        if op == OP_HELLO:
            # 收到 HELLO，启动心跳
            d = data.get("d", {})
            heartbeat_interval = d.get("heartbeat_interval", 30000) / 1000
            self._heartbeat_task = asyncio.create_task(
                self._start_heartbeat(heartbeat_interval)
            )
            return None

        if op == OP_HEARTBEAT_ACK:
            return None

        if op == OP_RECONNECT:
            logger.info("收到服务器重连指令")
            return "reconnect"

        if op == OP_INVALID_SESSION:
            logger.warning("会话无效，需要重新鉴权")
            return "invalid_session"

        if op == OP_DISPATCH:
            event_type = data.get("t", "")
            event_data = data.get("d", {})
            seq = data.get("s", 0)
            if seq > 0:
                self._last_seq = seq

            # READY 事件
            if event_type == "READY":
                user = event_data.get("user", {})
                self._bot_id = user.get("id", "")
                self._session_id = event_data.get("session_id", "")
                logger.info("WebSocket 鉴权成功，bot_id=%s", self._bot_id)
                return None

            # 消息事件（频道和QQ群聊/单聊）
            if event_type in (
                "AT_MESSAGE_CREATE",        # 频道 @ 消息
                "DIRECT_MESSAGE_CREATE",    # 频道私信
                "C2C_MESSAGE_CREATE",       # QQ 单聊消息
                "GROUP_AT_MESSAGE_CREATE",  # QQ 群聊 @ 消息
            ):
                if self._on_message:
                    # 注入事件类型到数据中
                    event_data["_event_type"] = event_type
                    await self._on_message(event_data)

            return None

        return None

    # ── REST API 发送消息 ───────────────────────────────────

    async def _api_request(
        self, method: str, path: str, payload: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """发送 REST API 请求。"""
        token = await self._ensure_token()
        headers = self._auth_headers()
        url = f"{_API_BASE}{path}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method,
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    text = await resp.text()
                    if resp.status >= 400:
                        logger.error(
                            "API 请求失败: %s %s → HTTP %d %s",
                            method, path, resp.status, text,
                        )
                        return None
                    return json.loads(text) if text else None
        except Exception:
            logger.exception("API 请求异常: %s %s", method, path)
            return None

    async def send_channel_message(
        self,
        channel_id: str,
        content: str,
        msg_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """在子频道中发送消息。"""
        payload: Dict[str, Any] = {"content": content}
        if msg_id:
            payload["msg_id"] = msg_id
        return await self._api_request(
            "POST", f"/channels/{channel_id}/messages", payload
        )

    async def create_direct_message_session(
        self,
        source_guild_id: str,
        user_id: str,
    ) -> Optional[Dict[str, Any]]:
        """创建私信会话，返回包含 guild_id 的响应。"""
        payload = {
            "recipient_id": user_id,
            "source_guild_id": source_guild_id,
        }
        return await self._api_request("POST", "/users/@me/dms", payload)

    async def send_direct_message(
        self,
        guild_id: str,
        content: str,
        msg_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """在私信频道中发送消息。"""
        payload: Dict[str, Any] = {"content": content}
        if msg_id:
            payload["msg_id"] = msg_id
        return await self._api_request(
            "POST", f"/dms/{guild_id}/messages", payload
        )

    async def send_c2c_message(
        self,
        openid: str,
        content: str,
        msg_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """发送 QQ 单聊消息。

        Args:
            openid: 用户的 openid（来自 C2C_MESSAGE_CREATE 事件的 author.user_openid）
            content: 消息内容
            msg_id: 被动回复时，用户消息的 ID

        Returns:
            API 响应，包含 id 和 timestamp
        """
        payload: Dict[str, Any] = {
            "content": content,
            "msg_type": 0,  # 文本消息
        }
        if msg_id:
            payload["msg_id"] = msg_id
        return await self._api_request(
            "POST", f"/v2/users/{openid}/messages", payload
        )

    async def send_group_message(
        self,
        group_openid: str,
        content: str,
        msg_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """发送 QQ 群聊消息。

        Args:
            group_openid: 群的 openid（来自 GROUP_AT_MESSAGE_CREATE 事件的 group_openid）
            content: 消息内容
            msg_id: 被动回复时，用户消息的 ID

        Returns:
            API 响应，包含 id 和 timestamp
        """
        payload: Dict[str, Any] = {
            "content": content,
            "msg_type": 0,  # 文本消息
        }
        if msg_id:
            payload["msg_id"] = msg_id
        return await self._api_request(
            "POST", f"/v2/groups/{group_openid}/messages", payload
        )
