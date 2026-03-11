"""
通道基类模块
定义消息通道的基础接口
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseChannel(ABC):
    """
    通道基类
    定义消息通道的标准接口
    """

    def __init__(self, channel_name: str = "base"):
        """
        初始化通道
        
        Args:
            channel_name: 通道名称
        """
        self.channel_name = channel_name

    @abstractmethod
    async def send_message(self, to: str, content: str, **kwargs) -> bool:
        """
        发送消息
        
        Args:
            to: 接收者标识
            content: 消息内容
            **kwargs: 其他参数
            
        Returns:
            是否发送成功
        """
        pass

    @abstractmethod
    async def handle_message(self, message: dict[str, Any]) -> Optional[str]:
        """
        处理接收到的消息
        
        Args:
            message: 消息内容
            
        Returns:
            回复消息内容，无需回复则返回 None
        """
        pass

    def get_session_id(self, sender: str, **kwargs) -> str:
        """
        生成会话 ID
        
        Args:
            sender: 发送者标识
            **kwargs: 其他参数
            
        Returns:
            会话 ID
        """
        return f"{self.channel_name}:{sender}"
