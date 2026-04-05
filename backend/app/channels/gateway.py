from __future__ import annotations

import logging
from typing import Any, Callable, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.channels.base import BaseChannel, IncomingMessage, OutgoingMessage
from app.dao.channel_dao import ChannelChatDAO, ChannelDAO
from app.services.conversation_service import ConversationService

logger = logging.getLogger(__name__)


class Gateway:
    """封装消息分发路由逻辑，从 ChannelManager 中解耦。

    职责：
    1. 外部消息 → ChannelChat 映射（get_or_create）
    2. 三级 conversation_id 回退解析
    3. 调用 Agent Loop
    4. 更新 conversation_id 映射
    5. 回复消息
    6. WebSocket 广播事件
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        agent_dispatch: Optional[Callable] = None,
    ) -> None:
        self._session_factory = session_factory
        self._agent_dispatch = agent_dispatch
        self._conversation_service = ConversationService()

    def set_agent_dispatch(self, dispatch: Callable) -> None:
        """设置 Agent 消息分发函数（由 main.py 注入 dispatch_message）。"""
        self._agent_dispatch = dispatch

    @staticmethod
    async def _broadcast(event: Dict[str, Any]) -> None:
        """广播事件到所有 WebSocket 客户端。故障不影响消息处理。"""
        try:
            from app.channels.ws_handler import get_gateway_ws_handler

            handler = get_gateway_ws_handler()
            await handler.broadcast(event)
        except Exception:
            logger.debug("Gateway WS broadcast failed", exc_info=True)

    async def dispatch(
        self, channel: BaseChannel, msg: IncomingMessage
    ) -> None:
        """核心消息分发：外部消息 → Agent Loop → 回复。

        Conversation 解析逻辑：
        1) ChannelChat 已绑定 conversation_id → 直接使用
        2) Channel 绑定了 conversation_id → 使用并同步到 ChannelChat
        3) 都没有 → 使用默认 session 创建新 conversation
        """
        if not self._agent_dispatch:
            logger.warning("Agent dispatch not set, ignoring message")
            return

        try:
            # 提取 Channel 级别绑定的 conversation_id
            channel_conversation_id: Optional[int] = getattr(
                channel, "conversation_id", None
            )

            session_id: Optional[int] = None
            conversation_id: Optional[int] = None
            channel_chat_id: Optional[int] = None

            # 第一个 session：获取/创建映射，解析 conversation_id
            async with self._session_factory() as db:
                chat = await ChannelChatDAO.get_or_create(
                    db, msg.channel_id, msg.chat_id, msg.chat_type
                )
                channel_chat_id = chat.id

                # 三级 conversation 解析：
                # 1) ChannelChat 级别绑定
                # 2) Channel 级别绑定（渠道专用会话）
                # 3) 立即创建新会话（确保 incoming 广播携带有效 conversation_id）
                conversation_id = chat.conversation_id
                if conversation_id is None and channel_conversation_id is not None:
                    conversation_id = channel_conversation_id
                    chat.conversation_id = conversation_id

                if conversation_id is None:
                    conversation_id, _conv = await self._conversation_service.get_or_create(
                        db, msg.text, conversation_id=None
                    )
                    chat.conversation_id = conversation_id

                # 更新外部用户信息
                chat.external_user_id = msg.user_id
                chat.external_user_name = msg.user_name

            # 广播 incoming 事件
            await self._broadcast({
                "type": "incoming",
                "conversation_id": conversation_id,
                "channel_id": msg.channel_id,
                "channel_type": msg.channel_type,
                "chat_id": msg.chat_id,
                "chat_type": msg.chat_type,
                "user_id": msg.user_id,
                "user_name": msg.user_name,
                "text": msg.text,
            })

            # 第二个 session：调用 Agent Loop
            async with self._session_factory() as db:
                result = await self._agent_dispatch(
                    db,
                    session_id,
                    msg.text,
                    conversation_id=conversation_id,
                )

                # 更新 conversation_id 映射
                new_conversation_id = result.get("conversation_id")
                if (
                    new_conversation_id
                    and new_conversation_id != conversation_id
                ):
                    fresh_chat = await ChannelChatDAO.get_by_id(
                        db, channel_chat_id
                    )
                    if fresh_chat:
                        await ChannelChatDAO.update_conversation(
                            db, fresh_chat, new_conversation_id
                        )

                # 提取回复文本
                reply_text = result.get("content", "")

            # 发送回复
            if reply_text:
                outbound = OutgoingMessage(
                    text=reply_text, reply_to=msg.message_id
                )
                await channel.send_message(msg.chat_id, outbound)

                # 广播 reply 事件（使用最终的 conversation_id）
                await self._broadcast({
                    "type": "reply",
                    "conversation_id": new_conversation_id or conversation_id,
                    "channel_id": msg.channel_id,
                    "channel_type": msg.channel_type,
                    "chat_id": msg.chat_id,
                    "chat_type": msg.chat_type,
                    "text": reply_text,
                })

        except Exception:
            logger.exception(
                "Error dispatching incoming message from channel %d",
                msg.channel_id,
            )
