"""
通道模块
提供各种消息通道的集成
"""

from app.channels.base import BaseChannel
from app.channels.wechat import WechatChannel
from app.channels.web import WebChannel, get_web_channel
from app.channels.qq import QQChannel

__all__ = [
    "BaseChannel",
    "WechatChannel",
    "WebChannel",
    "get_web_channel",
    "QQChannel",
]
