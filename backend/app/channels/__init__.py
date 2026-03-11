"""
通道模块
提供各种消息通道的集成
"""

from app.channels.base import BaseChannel
from app.channels.wechat import WechatChannel

__all__ = [
    "BaseChannel",
    "WechatChannel",
]
