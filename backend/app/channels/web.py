"""
Web 通道模块
将现有 REST API 适配为 Channel，支持 Gateway 架构
"""

import asyncio
import logging
import uuid
from typing import Dict, Optional

from app.channels.base import BaseChannel
from app.gateway.types import Message

logger = logging.getLogger(__name__)


class WebChannel(BaseChannel):
    """
    Web 通道
    适配现有 REST API，支持通过 HTTP 接口进行聊天
    
    特点:
    - 不需要主动连接，通过 HTTP 请求触发
    - 支持流式响应 (SSE)
    - 支持响应队列机制
    """
    
    def __init__(self):
        """
        初始化 Web 通道
        """
        super().__init__(channel_name="web")
        self._response_queues: Dict[str, asyncio.Queue] = {}
        self._streaming_sessions: Dict[str, bool] = {}
    
    async def start(self) -> None:
        """
        启动 Web 通道
        
        Web 通道不需要主动连接，只需标记为运行状态
        """
        self._running = True
        self._connected = True
        logger.info("Web 通道已启动")
    
    async def stop(self) -> None:
        """
        停止 Web 通道
        
        清理所有响应队列
        """
        self._running = False
        self._connected = False
        self._response_queues.clear()
        self._streaming_sessions.clear()
        logger.info("Web 通道已停止")
    
    async def send(self, target: str, message: str) -> bool:
        """
        发送消息到 Web 客户端
        
        通过响应队列将消息传递给等待的客户端
        
        Args:
            target: 目标标识 (session_id)
            message: 消息内容
            
        Returns:
            是否发送成功
        """
        if target in self._response_queues:
            try:
                await self._response_queues[target].put(message)
                return True
            except Exception as e:
                logger.error(f"Web 通道发送消息失败: {e}")
                return False
        return True
    
    async def create_session_queue(self, session_id: str) -> asyncio.Queue:
        """
        为会话创建响应队列
        
        Args:
            session_id: 会话 ID
            
        Returns:
            响应队列
        """
        if session_id not in self._response_queues:
            self._response_queues[session_id] = asyncio.Queue()
        return self._response_queues[session_id]
    
    def remove_session_queue(self, session_id: str) -> None:
        """
        移除会话的响应队列
        
        Args:
            session_id: 会话 ID
        """
        if session_id in self._response_queues:
            del self._response_queues[session_id]
    
    async def get_response(
        self,
        session_id: str,
        timeout: float = 30.0,
    ) -> Optional[str]:
        """
        获取会话的响应
        
        Args:
            session_id: 会话 ID
            timeout: 超时时间（秒）
            
        Returns:
            响应内容，超时返回 None
        """
        if session_id not in self._response_queues:
            return None
        
        queue = self._response_queues[session_id]
        try:
            response = await asyncio.wait_for(queue.get(), timeout=timeout)
            return response
        except asyncio.TimeoutError:
            return None
    
    async def handle_chat_request(
        self,
        content: str,
        user_id: Optional[str] = None,
        user_name: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> str:
        """
        处理聊天请求
        
        将 HTTP 聊天请求转换为消息并转发给 Gateway
        
        Args:
            content: 消息内容
            user_id: 用户 ID
            user_name: 用户名
            session_id: 会话 ID
            
        Returns:
            会话 ID
        """
        if not self._running:
            raise RuntimeError("Web 通道未启动")
        
        actual_session_id = session_id or str(uuid.uuid4())
        actual_user_id = user_id or "default"
        actual_user_name = user_name or "User"
        
        message = Message(
            id=str(uuid.uuid4()),
            content=content,
            user_id=actual_user_id,
            user_name=actual_user_name,
            channel="web",
        )
        
        await self.create_session_queue(actual_session_id)
        
        await self._on_message(message)
        
        return actual_session_id
    
    def set_streaming(self, session_id: str, streaming: bool) -> None:
        """
        设置会话的流式状态
        
        Args:
            session_id: 会话 ID
            streaming: 是否流式
        """
        self._streaming_sessions[session_id] = streaming
    
    def is_streaming(self, session_id: str) -> bool:
        """
        检查会话是否为流式
        
        Args:
            session_id: 会话 ID
            
        Returns:
            是否流式
        """
        return self._streaming_sessions.get(session_id, False)


_web_channel: Optional[WebChannel] = None


def get_web_channel() -> WebChannel:
    """
    获取全局 Web 通道实例（单例模式）
    
    Returns:
        WebChannel 实例
    """
    global _web_channel
    if _web_channel is None:
        _web_channel = WebChannel()
    return _web_channel
