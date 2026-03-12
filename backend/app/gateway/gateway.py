"""
Gateway 网关主模块
常驻运行的总控面板，协调 Channel 和 Session
"""

import asyncio
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional

from app.gateway.router import MessageRouter
from app.gateway.types import ChannelStatus, GatewayStatus, Message, SessionInfo

if TYPE_CHECKING:
    from app.channels.base import BaseChannel

logger = logging.getLogger(__name__)


class Gateway:
    """
    Gateway 网关总控面板
    常驻运行，统一调度 Channel 和 Session
    
    核心职责:
    1. 管理多个消息通道 (Channel)
    2. 路由消息到正确的会话 (Session)
    3. 协调 Agent 处理消息
    4. 提供状态查询接口
    """
    
    def __init__(self):
        """
        初始化 Gateway
        """
        self._channels: Dict[str, "BaseChannel"] = {}
        self._router = MessageRouter()
        self._running = False
        self._started_at: Optional[datetime] = None
        self._sessions_cache: Dict[str, SessionInfo] = {}
        self._agent = None
        self._session_manager = None
        self._lock = asyncio.Lock()
    
    @property
    def status(self) -> GatewayStatus:
        """
        获取 Gateway 状态
        
        Returns:
            GatewayStatus 状态对象
        """
        uptime = 0.0
        if self._started_at:
            uptime = (datetime.now() - self._started_at).total_seconds()
        
        channels_status = {}
        for name, channel in self._channels.items():
            channels_status[name] = channel.status
        
        return GatewayStatus(
            running=self._running,
            started_at=self._started_at,
            uptime_seconds=uptime,
            channels=channels_status,
            sessions_count=len(self._sessions_cache),
        )
    
    @property
    def channels(self) -> Dict[str, "BaseChannel"]:
        """
        获取已注册的通道
        
        Returns:
            通道字典
        """
        return self._channels
    
    @property
    def router(self) -> MessageRouter:
        """
        获取消息路由器
        
        Returns:
            MessageRouter 实例
        """
        return self._router
    
    def set_agent(self, agent: Any) -> None:
        """
        设置 Agent 实例
        
        Args:
            agent: Agent 实例
        """
        self._agent = agent
    
    def set_session_manager(self, session_manager: Any) -> None:
        """
        设置会话管理器
        
        Args:
            session_manager: SessionManager 实例
        """
        self._session_manager = session_manager
    
    async def register_channel(self, channel: "BaseChannel") -> None:
        """
        注册通道
        
        Args:
            channel: 通道实例
        """
        async with self._lock:
            self._channels[channel.name] = channel
            channel.set_gateway(self)
            logger.info(f"通道已注册: {channel.name}")
    
    async def unregister_channel(self, channel_name: str) -> bool:
        """
        注销通道
        
        Args:
            channel_name: 通道名称
            
        Returns:
            是否注销成功
        """
        async with self._lock:
            if channel_name in self._channels:
                channel = self._channels.pop(channel_name)
                await channel.stop()
                logger.info(f"通道已注销: {channel_name}")
                return True
            return False
    
    async def start(self) -> None:
        """
        启动 Gateway
        
        启动所有已注册的通道
        """
        if self._running:
            logger.warning("Gateway 已经在运行中")
            return
        
        self._running = True
        self._started_at = datetime.now()
        
        logger.info("Gateway 启动中...")
        
        await self._start_channels()
        
        logger.info("Gateway 启动完成")
    
    async def stop(self) -> None:
        """
        停止 Gateway
        
        停止所有通道
        """
        if not self._running:
            return
        
        logger.info("Gateway 停止中...")
        
        self._running = False
        await self._stop_channels()
        
        logger.info("Gateway 已停止")
    
    async def _start_channels(self) -> None:
        """
        启动所有已注册的通道
        """
        for name, channel in self._channels.items():
            try:
                await channel.start()
                logger.info(f"通道已启动: {name}")
            except Exception as e:
                logger.error(f"通道启动失败 {name}: {e}")
    
    async def _stop_channels(self) -> None:
        """
        停止所有通道
        """
        for name, channel in self._channels.items():
            try:
                await channel.stop()
                logger.info(f"通道已停止: {name}")
            except Exception as e:
                logger.error(f"通道停止失败 {name}: {e}")
    
    async def on_message(self, channel: str, message: Message) -> None:
        """
        处理来自通道的消息
        
        这是通道调用此方法将消息传递给 Gateway
        
        Args:
            channel: 通道名称
            message: 消息对象
        """
        if not self._running:
            logger.warning(f"Gateway 未运行，忽略消息: {channel}")
            return
        
        try:
            session_id = self._router.route(channel, message)
            
            session = await self._get_or_create_session(session_id, channel, message)
            
            if self._agent:
                response = await self._agent.process_message(
                    session_id,
                    message.content,
                    channel=channel,
                )
                
                if response:
                    await self._send_response(channel, session_id, response)
            else:
                logger.warning("Agent 未设置，无法处理消息")
                
        except Exception as e:
            logger.error(f"处理消息失败: {e}")
    
    async def _get_or_create_session(
        self,
        session_id: str,
        channel: str,
        message: Message,
    ) -> SessionInfo:
        """
        获取或创建会话
        
        Args:
            session_id: 会话 ID
            channel: 通道名称
            message: 消息对象
            
        Returns:
            SessionInfo 会话信息
        """
        if session_id in self._sessions_cache:
            return self._sessions_cache[session_id]
        
        kind = "group" if message.is_group else "direct"
        session = SessionInfo(
            id=session_id,
            channel=channel,
            kind=kind,
            user_id=message.user_id if not message.is_group else None,
            group_id=message.group_id if message.is_group else None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        self._sessions_cache[session_id] = session
        
        if self._session_manager:
            existing = await self._session_manager.get_session(session_id)
            if not existing:
                await self._session_manager.create_session(
                    session_id,
                    channel,
                    metadata={"kind": kind, "user_name": message.user_name},
                )
        
        return session
    
    async def _send_response(
        self,
        channel: str,
        session_id: str,
        response: str,
    ) -> None:
        """
        发送响应到通道
        
        Args:
            channel: 通道名称
            session_id: 会话 ID
            response: 响应内容
        """
        if channel not in self._channels:
            logger.warning(f"通道不存在: {channel}")
            return
        
        ch = self._channels[channel]
        target = self._router.get_target_from_session(session_id)
        
        try:
            await ch.send(target, response)
        except Exception as e:
            logger.error(f"发送响应失败: {e}")
    
    def get_channel_status(self, channel_name: str) -> Optional[ChannelStatus]:
        """
        获取通道状态
        
        Args:
            channel_name: 通道名称
            
        Returns:
            通道状态，不存在则返回 None
        """
        if channel_name in self._channels:
            return self._channels[channel_name].status
        return None
    
    def get_all_channels_status(self) -> Dict[str, ChannelStatus]:
        """
        获取所有通道状态
        
        Returns:
            通道状态字典
        """
        return {name: ch.status for name, ch in self._channels.items()}
    
    def get_sessions(self) -> Dict[str, SessionInfo]:
        """
        获取所有会话
        
        Returns:
            会话字典
        """
        return self._sessions_cache.copy()


_gateway: Optional[Gateway] = None


def get_gateway() -> Gateway:
    """
    获取全局 Gateway 实例（单例模式）
    
    Returns:
        Gateway 实例
    """
    global _gateway
    if _gateway is None:
        _gateway = Gateway()
    return _gateway
