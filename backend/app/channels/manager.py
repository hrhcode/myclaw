from __future__ import annotations

import json
import logging
from typing import Callable, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.channels.base import BaseChannel, IncomingMessage, OutgoingMessage
from app.channels.gateway import Gateway
from app.channels.registry import CHANNEL_REGISTRY
from app.dao.channel_dao import ChannelChatDAO, ChannelDAO

logger = logging.getLogger(__name__)


class ChannelManager:
    """管理所有消息通道的生命周期和消息分发。"""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._channels: Dict[int, BaseChannel] = {}  # channel_id -> BaseChannel
        self._gateway = Gateway(session_factory)

    def set_agent_dispatch(self, dispatch: Callable) -> None:
        """设置 Agent 消息分发函数（由 main.py 注入 dispatch_message）。"""
        self._gateway.set_agent_dispatch(dispatch)

    async def start(self) -> None:
        """从数据库加载所有启用的通道并启动。"""
        async with self._session_factory() as db:
            enabled_channels = await ChannelDAO.get_enabled(db)

        for ch_model in enabled_channels:
            await self._start_channel(ch_model)

        logger.info("ChannelManager: started %d channel(s)", len(self._channels))

    async def stop(self) -> None:
        """停止所有运行中的通道。"""
        for channel_id, channel in list(self._channels.items()):
            try:
                await channel.stop()
            except Exception:
                logger.exception("Error stopping channel %d", channel_id)
        self._channels.clear()
        logger.info("ChannelManager: all channels stopped")

    async def start_channel(self, channel_id: int) -> None:
        """启动单个通道。"""
        async with self._session_factory() as db:
            ch_model = await ChannelDAO.get_by_id(db, channel_id)
        if not ch_model:
            raise ValueError(f"Channel not found: {channel_id}")
        await self._stop_channel_if_running(channel_id)
        await self._start_channel(ch_model)

    async def stop_channel(self, channel_id: int) -> None:
        """停止单个通道。"""
        await self._stop_channel_if_running(channel_id)

    async def restart_channel(self, channel_id: int) -> None:
        """重启单个通道。"""
        await self.stop_channel(channel_id)
        await self.start_channel(channel_id)

    def get_channel_status(self, channel_id: int) -> Dict[str, str]:
        """获取通道运行状态。"""
        if channel_id in self._channels:
            return {"status": "running"}
        return {"status": "stopped"}

    async def _start_channel(self, ch_model) -> None:
        if not ch_model.enabled:
            logger.info("Channel %d is disabled, skipping start", ch_model.id)
            return

        channel_type = ch_model.channel_type
        if channel_type not in CHANNEL_REGISTRY:
            logger.error("Unknown channel type: %s", channel_type)
            return

        config = json.loads(ch_model.config) if ch_model.config else {}
        channel_cls = CHANNEL_REGISTRY[channel_type]
        channel = channel_cls(channel_id=ch_model.id, config=config)
        channel.set_on_message_callback(self.dispatch_incoming)

        try:
            await channel.start()
            self._channels[ch_model.id] = channel

            async with self._session_factory() as db:
                fresh_model = await ChannelDAO.get_by_id(db, ch_model.id)
                if fresh_model:
                    await ChannelDAO.update(db, fresh_model, status="running", status_message=None)

            logger.info("Channel %d (%s) started", ch_model.id, channel_type)
        except Exception as exc:
            logger.exception("Failed to start channel %d (%s)", ch_model.id, channel_type)
            async with self._session_factory() as db:
                fresh_model = await ChannelDAO.get_by_id(db, ch_model.id)
                if fresh_model:
                    await ChannelDAO.update(
                        db, fresh_model, status="error", status_message=str(exc)
                    )

    async def _stop_channel_if_running(self, channel_id: int) -> None:
        channel = self._channels.pop(channel_id, None)
        if channel:
            try:
                await channel.stop()
            except Exception:
                logger.exception("Error stopping channel %d", channel_id)

            async with self._session_factory() as db:
                ch_model = await ChannelDAO.get_by_id(db, channel_id)
                if ch_model:
                    await ChannelDAO.update(db, ch_model, status="stopped")

    async def dispatch_incoming(
        self, channel: BaseChannel, msg: IncomingMessage
    ) -> None:
        """消息分发委托给 Gateway。"""
        await self._gateway.dispatch(channel, msg)


# 模块级单例，由 main.py 注入 session_factory
channel_manager: Optional[ChannelManager] = None


def init_channel_manager(session_factory: async_sessionmaker[AsyncSession]) -> ChannelManager:
    global channel_manager
    channel_manager = ChannelManager(session_factory)
    return channel_manager
