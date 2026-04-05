from __future__ import annotations

from typing import Dict, Type

from app.channels.base import BaseChannel


def _get_qq_channel() -> Type[BaseChannel]:
    from app.channels.qq.channel import QQChannel
    return QQChannel


# 通道类型注册表。新增通道类型只需在此添加映射。
# 使用延迟导入避免循环依赖。
CHANNEL_REGISTRY: Dict[str, Type[BaseChannel]] = {
    "qq": _get_qq_channel(),
}


def get_channel_class(channel_type: str) -> Type[BaseChannel] | None:
    return CHANNEL_REGISTRY.get(channel_type)


def get_supported_types() -> list[str]:
    return list(CHANNEL_REGISTRY.keys())
