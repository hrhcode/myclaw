from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class IncomingMessage:
    """平台无关的入站消息表示。"""

    channel_type: str  # "qq", "telegram", "discord"
    channel_id: int  # DB 中的 channel 记录 ID
    chat_type: str  # "group" / "private"
    chat_id: str  # 平台侧聊天标识
    user_id: str  # 平台侧用户标识
    user_name: str  # 显示名
    text: str  # 纯文本内容
    message_id: str  # 平台侧消息 ID（用于回复引用）
    is_at: bool = False  # 是否 @了机器人
    images: List[str] = field(default_factory=list)  # 图片 URL 列表
    raw: Dict[str, Any] = field(default_factory=dict)  # 原始平台数据


@dataclass
class OutgoingMessage:
    """平台无关的出站消息。"""

    text: str = ""
    reply_to: Optional[str] = None  # 引用回复的消息 ID


class BaseChannel(ABC):
    """消息通道抽象基类。所有通道实现必须继承此类。"""

    def __init__(self, channel_id: int, config: Dict[str, Any]) -> None:
        self.channel_id = channel_id
        self.config = config

    @abstractmethod
    async def start(self) -> None:
        """启动通道（建立连接、开始监听消息）。"""
        ...

    @abstractmethod
    async def stop(self) -> None:
        """停止通道（断开连接、清理资源）。"""
        ...

    @abstractmethod
    async def send_message(self, chat_id: str, message: OutgoingMessage) -> None:
        """向平台发送消息。"""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """返回通道连接是否健康。"""
        ...

    def set_on_message_callback(
        self, callback: Callable[..., Any]
    ) -> None:
        """设置消息回调，由 ChannelManager 注入。"""
        self._on_message_callback = callback

    async def _emit_message(self, msg: IncomingMessage) -> None:
        """子类调用此方法将消息上抛给 ChannelManager。"""
        if hasattr(self, "_on_message_callback") and self._on_message_callback:
            await self._on_message_callback(self, msg)
