"""
通道基类模块
定义消息通道的基础接口，支持 Gateway 架构
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from app.gateway.types import ChannelStatus, Message

if TYPE_CHECKING:
    from app.gateway import Gateway

logger = logging.getLogger(__name__)


class BaseChannel(ABC):
    """
    通道基类
    定义消息通道的标准接口，所有通道都需要继承此类
    
    通道的生命周期:
    1. 创建实例
    2. 设置 Gateway 引用 (set_gateway)
    3. 启动通道 (start)
    4. 接收消息并转发给 Gateway (_on_message)
    5. 停止通道 (stop)
    """
    
    def __init__(self, channel_name: str = "base"):
        """
        初始化通道
        
        Args:
            channel_name: 通道名称
        """
        self._name = channel_name
        self._gateway: Optional["Gateway"] = None
        self._enabled = True
        self._running = False
        self._connected = False
        self._last_message_at: Optional[datetime] = None
        self._error: Optional[str] = None
    
    @property
    def name(self) -> str:
        """
        获取通道名称
        
        Returns:
            通道名称
        """
        return self._name
    
    @property
    def status(self) -> ChannelStatus:
        """
        获取通道状态
        
        Returns:
            ChannelStatus 状态对象
        """
        return ChannelStatus(
            name=self._name,
            enabled=self._enabled,
            running=self._running,
            connected=self._connected,
            last_message_at=self._last_message_at,
            error=self._error,
        )
    
    def set_gateway(self, gateway: "Gateway") -> None:
        """
        设置 Gateway 引用
        
        由 Gateway 在注册通道时调用
        
        Args:
            gateway: Gateway 实例
        """
        self._gateway = gateway
    
    @abstractmethod
    async def start(self) -> None:
        """
        启动通道
        
        子类需要实现此方法，完成通道的初始化和连接
        """
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """
        停止通道
        
        子类需要实现此方法，完成通道的清理和断开
        """
        pass
    
    @abstractmethod
    async def send(self, target: str, message: str) -> bool:
        """
        发送消息
        
        子类需要实现此方法，将消息发送到指定目标
        
        Args:
            target: 目标标识 (user_id 或 group_id)
            message: 消息内容
            
        Returns:
            是否发送成功
        """
        pass
    
    async def _on_message(self, message: Message) -> None:
        """
        收到消息时调用
        
        子类在收到消息后应调用此方法，将消息转发给 Gateway
        
        Args:
            message: 消息对象
        """
        self._last_message_at = datetime.now()
        
        if self._gateway:
            await self._gateway.on_message(self._name, message)
        else:
            logger.warning(f"通道 {self._name} 未设置 Gateway，无法处理消息")
    
    def enable(self) -> None:
        """
        启用通道
        """
        self._enabled = True
    
    def disable(self) -> None:
        """
        禁用通道
        """
        self._enabled = False
    
    def set_error(self, error: Optional[str]) -> None:
        """
        设置错误状态
        
        Args:
            error: 错误信息，None 表示清除错误
        """
        self._error = error
    
    def set_connected(self, connected: bool) -> None:
        """
        设置连接状态
        
        Args:
            connected: 是否已连接
        """
        self._connected = connected
