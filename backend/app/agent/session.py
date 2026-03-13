"""
会话管理模块
提供会话和消息管理的便捷接口
"""

import logging
from typing import Any, Optional

from app.storage.database import Database, get_database

logger = logging.getLogger(__name__)


class SessionManager:
    """
    会话管理器
    提供会话和消息管理的便捷接口，底层使用统一的 Database 类
    """

    def __init__(self, db: Optional[Database] = None):
        """
        初始化会话管理器
        
        Args:
            db: 数据库实例，默认使用全局实例
        """
        self.db = db or get_database()

    async def init_db(self) -> None:
        """初始化数据库"""
        await self.db.init_db()

    async def create_session(
        self,
        session_id: str,
        channel: str = "web",
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        创建新会话
        
        Args:
            session_id: 会话 ID
            channel: 通道来源
            metadata: 会话元数据
        """
        await self.db.create_session(session_id, channel, metadata)

    async def get_session(self, session_id: str) -> Optional[dict[str, Any]]:
        """
        获取会话信息
        
        Args:
            session_id: 会话 ID
            
        Returns:
            会话信息字典
        """
        return await self.db.get_session(session_id)

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        thoughts: Optional[str] = None,
        tool_calls: Optional[list[dict[str, Any]]] = None,
        tool_call_id: Optional[str] = None,
        generate_embedding: bool = True,
    ) -> int:
        """
        添加消息到会话
        
        Args:
            session_id: 会话 ID
            role: 消息角色
            content: 消息内容
            thoughts: 思考过程
            tool_calls: 工具调用列表
            tool_call_id: 工具调用 ID
            generate_embedding: 是否生成嵌入向量
            
        Returns:
            消息 ID
        """
        return await self.db.add_message(
            session_id=session_id,
            role=role,
            content=content,
            thoughts=thoughts,
            tool_calls=tool_calls,
            tool_call_id=tool_call_id,
            generate_embedding=generate_embedding,
        )

    async def get_messages(
        self,
        session_id: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        获取会话的消息历史
        
        Args:
            session_id: 会话 ID
            limit: 最大消息数量
            
        Returns:
            消息列表
        """
        return await self.db.get_messages(session_id, limit)

    async def get_messages_for_llm(
        self,
        session_id: str,
        limit: int = 20,
    ) -> list[dict[str, str]]:
        """
        获取适合 LLM 输入的消息格式
        
        Args:
            session_id: 会话 ID
            limit: 最大消息数量
            
        Returns:
            LLM 格式的消息列表
        """
        return await self.db.get_messages_for_llm(session_id, limit)

    async def search_memories(
        self,
        query: str,
        session_id: Optional[str] = None,
        limit: int = 5,
    ) -> list[dict]:
        """
        搜索相关记忆
        
        Args:
            query: 查询文本
            session_id: 会话 ID（可选，为空时全局搜索）
            limit: 返回数量限制
            
        Returns:
            相关记忆列表
        """
        return await self.db.search_memories(query, session_id, limit)

    async def clear_session(self, session_id: str) -> None:
        """
        清除会话的所有数据
        
        Args:
            session_id: 会话 ID
        """
        await self.db.clear_session(session_id)


_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """
    获取全局会话管理器实例（单例模式）
    
    Returns:
        SessionManager 实例
    """
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
