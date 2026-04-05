from __future__ import annotations

import logging
from typing import Any, Dict

from app.channels.base import BaseChannel, IncomingMessage, OutgoingMessage
from app.channels.qq.message_builder import split_long_text
from app.channels.qq.message_parser import parse_official_message, should_respond
from app.channels.qq.qq_official_client import QQOfficialClient

logger = logging.getLogger(__name__)


class QQChannel(BaseChannel):
    """QQ 通道实现，基于 QQ 官方机器人 API。"""

    def __init__(self, channel_id: int, config: Dict[str, Any]) -> None:
        super().__init__(channel_id, config)
        self._client: QQOfficialClient | None = None

    @property
    def _app_id(self) -> str:
        return self.config.get("app_id", "")

    @property
    def _app_secret(self) -> str:
        return self.config.get("app_secret", "")

    @property
    def _trigger_mode(self) -> str:
        return self.config.get("trigger_mode", "at_or_mention")

    @property
    def _private_enabled(self) -> bool:
        return self.config.get("private_enabled", True)

    async def start(self) -> None:
        if not self._app_id or not self._app_secret:
            raise ValueError("QQ 通道需要配置 app_id 和 app_secret")

        self._client = QQOfficialClient(
            app_id=self._app_id,
            app_secret=self._app_secret,
            on_message=self._on_qq_message,
        )
        await self._client.start()
        logger.info("QQChannel %d started, app_id=%s", self.channel_id, self._app_id)

    async def stop(self) -> None:
        if self._client:
            await self._client.stop()
            self._client = None
        logger.info("QQChannel %d stopped", self.channel_id)

    async def send_message(self, chat_id: str, message: OutgoingMessage) -> None:
        if not self._client:
            return

        chat_type, id1, id2 = self._parse_chat_id(chat_id)

        # 长文本分片发送
        chunks = split_long_text(message.text)
        for chunk in chunks:
            if chat_type == "channel":
                # 频道消息
                await self._client.send_channel_message(
                    channel_id=id1,
                    content=chunk,
                    msg_id=message.reply_to,
                )
            elif chat_type == "direct":
                # 频道私信
                guild_id = id1
                if not guild_id and id2:
                    logger.warning("发送私信缺少 guild_id，user_id=%s", id2)
                    return
                await self._client.send_direct_message(
                    guild_id=guild_id,
                    content=chunk,
                    msg_id=message.reply_to,
                )
            elif chat_type == "c2c":
                # QQ 单聊
                await self._client.send_c2c_message(
                    openid=id1,
                    content=chunk,
                    msg_id=message.reply_to,
                )
            elif chat_type == "group":
                # QQ 群聊
                await self._client.send_group_message(
                    group_openid=id1,
                    content=chunk,
                    msg_id=message.reply_to,
                )

    async def health_check(self) -> bool:
        if self._client:
            return await self._client.health_check()
        return False

    async def _on_qq_message(self, event_data: Dict[str, Any]) -> None:
        """处理 QQ 官方消息事件。"""
        event_type = event_data.get("_event_type", "")
        author = event_data.get("author", {})
        message_id = event_data.get("id", "")
        bot_id = self._client.bot_id if self._client else None

        # 根据事件类型解析用户标识
        if event_type == "C2C_MESSAGE_CREATE":
            # QQ 单聊：使用 user_openid
            user_id = author.get("user_openid", "")
            user_name = user_id  # 单聊没有用户名，使用 openid
        elif event_type == "GROUP_AT_MESSAGE_CREATE":
            # QQ 群聊：使用 member_openid
            user_id = author.get("member_openid", "")
            user_name = user_id
        else:
            # 频道场景：使用 id
            user_id = author.get("id", "")
            user_name = author.get("username") or author.get("id") or user_id

        # 解析消息
        parsed = parse_official_message(event_data, bot_id)

        # 判断是否响应
        if not should_respond(
            parsed,
            event_type,
            self._trigger_mode,
            self._private_enabled,
        ):
            return

        # 空消息不响应
        if not parsed.text.strip() and not parsed.images:
            return

        # 构造 chat_id
        if event_type == "AT_MESSAGE_CREATE":
            # 频道 @ 消息
            channel_id = event_data.get("channel_id", "")
            guild_id = event_data.get("guild_id", "")
            chat_id = f"channel:{channel_id}"
            chat_type = "group"
        elif event_type == "DIRECT_MESSAGE_CREATE":
            # 频道私信
            guild_id = event_data.get("guild_id", "")
            chat_id = f"direct:{guild_id}:{user_id}"
            chat_type = "private"
        elif event_type == "C2C_MESSAGE_CREATE":
            # QQ 单聊
            chat_id = f"c2c:{user_id}"
            chat_type = "private"
        elif event_type == "GROUP_AT_MESSAGE_CREATE":
            # QQ 群聊
            group_openid = event_data.get("group_openid", "")
            chat_id = f"group:{group_openid}"
            chat_type = "group"
        else:
            return

        msg = IncomingMessage(
            channel_type="qq",
            channel_id=self.channel_id,
            chat_type=chat_type,
            chat_id=chat_id,
            user_id=user_id,
            user_name=user_name,
            text=parsed.text,
            message_id=message_id,
            is_at=parsed.is_at,
            images=parsed.images,
            raw=event_data,
        )

        await self._emit_message(msg)

    @staticmethod
    def _parse_chat_id(chat_id: str) -> tuple[str, str, str]:
        """从 chat_id 解析类型和实际 ID。

        返回 (chat_type, id1, id2):
        - channel:{channel_id} → ("channel", channel_id, "")
        - direct:{guild_id}:{user_id} → ("direct", guild_id, user_id)
        - c2c:{user_openid} → ("c2c", user_openid, "")
        - group:{group_openid} → ("group", group_openid, "")
        """
        if chat_id.startswith("channel:"):
            return "channel", chat_id[8:], ""
        elif chat_id.startswith("direct:"):
            parts = chat_id[7:].split(":", 1)
            if len(parts) == 2:
                return "direct", parts[0], parts[1]
            return "direct", parts[0], ""
        elif chat_id.startswith("c2c:"):
            return "c2c", chat_id[4:], ""
        elif chat_id.startswith("group:"):
            return "group", chat_id[6:], ""
        return "direct", chat_id, ""
