"""
Gateway 类型定义模块
定义 Gateway、Channel、Message 等核心数据类型
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class Message:
    """
    统一消息格式
    所有通道的消息都会转换为此格式
    """
    id: str
    content: str
    user_id: str
    user_name: str = ""
    group_id: Optional[str] = None
    group_name: Optional[str] = None
    is_group: bool = False
    channel: str = ""
    raw: Optional[dict] = None
    
    def to_dict(self) -> dict:
        """
        转换为字典格式
        
        Returns:
            消息字典
        """
        return {
            "id": self.id,
            "content": self.content,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "group_id": self.group_id,
            "group_name": self.group_name,
            "is_group": self.is_group,
            "channel": self.channel,
        }


@dataclass
class ChannelStatus:
    """
    通道状态
    描述通道的运行状态
    """
    name: str
    enabled: bool = False
    running: bool = False
    connected: bool = False
    last_message_at: Optional[datetime] = None
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        """
        转换为字典格式
        
        Returns:
            状态字典
        """
        return {
            "name": self.name,
            "enabled": self.enabled,
            "running": self.running,
            "connected": self.connected,
            "last_message_at": self.last_message_at.isoformat() if self.last_message_at else None,
            "error": self.error,
        }


@dataclass
class GatewayStatus:
    """
    Gateway 状态
    描述网关的整体运行状态
    """
    running: bool = False
    started_at: Optional[datetime] = None
    uptime_seconds: float = 0.0
    channels: Dict[str, ChannelStatus] = field(default_factory=dict)
    sessions_count: int = 0
    
    def to_dict(self) -> dict:
        """
        转换为字典格式
        
        Returns:
            状态字典
        """
        return {
            "running": self.running,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "uptime_seconds": self.uptime_seconds,
            "channels": {k: v.to_dict() for k, v in self.channels.items()},
            "sessions_count": self.sessions_count,
        }


@dataclass
class SessionInfo:
    """
    会话信息
    描述会话的基本信息
    """
    id: str
    channel: str
    kind: str = "direct"
    user_id: Optional[str] = None
    group_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """
        转换为字典格式
        
        Returns:
            会话信息字典
        """
        return {
            "id": self.id,
            "channel": self.channel,
            "kind": self.kind,
            "user_id": self.user_id,
            "group_id": self.group_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.metadata,
        }
