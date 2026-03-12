"""
消息路由器模块
负责将消息路由到正确的会话
"""

from app.gateway.types import Message


class MessageRouter:
    """
    消息路由器
    根据通道和消息内容确定目标会话
    """
    
    def route(self, channel: str, message: Message) -> str:
        """
        根据通道和消息确定目标会话
        
        Args:
            channel: 通道名称
            message: 消息对象
            
        Returns:
            会话 ID，格式为: channel:kind:id
            - 私聊: channel:user:user_id
            - 群聊: channel:group:group_id
        """
        if message.is_group and message.group_id:
            return f"{channel}:group:{message.group_id}"
        return f"{channel}:user:{message.user_id}"
    
    def parse_session_id(self, session_id: str) -> dict:
        """
        解析会话 ID
        
        Args:
            session_id: 会话 ID
            
        Returns:
            解析结果字典，包含 channel, kind, target
        """
        parts = session_id.split(":", 2)
        if len(parts) == 3:
            return {
                "channel": parts[0],
                "kind": parts[1],
                "target": parts[2],
            }
        elif len(parts) == 2:
            return {
                "channel": parts[0],
                "kind": "user",
                "target": parts[1],
            }
        return {
            "channel": parts[0] if parts else "",
            "kind": "unknown",
            "target": "",
        }
    
    def get_channel_from_session(self, session_id: str) -> str:
        """
        从会话 ID 中提取通道名称
        
        Args:
            session_id: 会话 ID
            
        Returns:
            通道名称
        """
        parsed = self.parse_session_id(session_id)
        return parsed.get("channel", "")
    
    def get_kind_from_session(self, session_id: str) -> str:
        """
        从会话 ID 中提取会话类型
        
        Args:
            session_id: 会话 ID
            
        Returns:
            会话类型: user/group/unknown
        """
        parsed = self.parse_session_id(session_id)
        return parsed.get("kind", "unknown")
    
    def get_target_from_session(self, session_id: str) -> str:
        """
        从会话 ID 中提取目标 ID
        
        Args:
            session_id: 会话 ID
            
        Returns:
            目标 ID (user_id 或 group_id)
        """
        parsed = self.parse_session_id(session_id)
        return parsed.get("target", "")
