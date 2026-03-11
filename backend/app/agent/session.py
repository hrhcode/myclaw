"""
会话管理模块
使用 SQLite 数据库存储会话和消息
"""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import aiosqlite

logger = logging.getLogger(__name__)


class SessionManager:
    """
    会话管理器
    管理会话和消息的存储与检索
    """

    def __init__(self, db_path: str = "data/myclaw.db"):
        """
        初始化会话管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._ensure_db_dir()

    def _ensure_db_dir(self) -> None:
        """确保数据库目录存在"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    async def init_db(self) -> None:
        """初始化数据库表"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    channel TEXT NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tool_calls TEXT,
                    tool_call_id TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_session_id 
                ON messages(session_id)
            """)
            
            await db.commit()
        logger.info(f"数据库初始化完成: {self.db_path}")

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
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO sessions (id, channel, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    channel,
                    json.dumps(metadata) if metadata else None,
                    datetime.now(),
                    datetime.now(),
                ),
            )
            await db.commit()

    async def get_session(self, session_id: str) -> Optional[dict[str, Any]]:
        """
        获取会话信息
        
        Args:
            session_id: 会话 ID
            
        Returns:
            会话信息字典，不存在则返回 None
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = sqlite3.Row
            cursor = await db.execute(
                "SELECT * FROM sessions WHERE id = ?", (session_id,)
            )
            row = await cursor.fetchone()
            if row:
                return {
                    "id": row["id"],
                    "channel": row["channel"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else None,
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                }
            return None

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        tool_calls: Optional[list[dict[str, Any]]] = None,
        tool_call_id: Optional[str] = None,
    ) -> int:
        """
        添加消息到会话
        
        Args:
            session_id: 会话 ID
            role: 消息角色 (user/assistant/tool)
            content: 消息内容
            tool_calls: 工具调用列表
            tool_call_id: 工具调用 ID
            
        Returns:
            消息 ID
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO messages (session_id, role, content, tool_calls, tool_call_id, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    role,
                    content,
                    json.dumps(tool_calls) if tool_calls else None,
                    tool_call_id,
                    datetime.now(),
                ),
            )
            message_id = cursor.lastrowid
            
            await db.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (datetime.now(), session_id),
            )
            
            await db.commit()
            return message_id

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
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = sqlite3.Row
            cursor = await db.execute(
                """
                SELECT * FROM messages 
                WHERE session_id = ? 
                ORDER BY timestamp ASC 
                LIMIT ?
                """,
                (session_id, limit),
            )
            rows = await cursor.fetchall()
            
            return [
                {
                    "id": row["id"],
                    "session_id": row["session_id"],
                    "role": row["role"],
                    "content": row["content"],
                    "tool_calls": json.loads(row["tool_calls"]) if row["tool_calls"] else None,
                    "tool_call_id": row["tool_call_id"],
                    "timestamp": row["timestamp"],
                }
                for row in rows
            ]

    async def get_messages_for_llm(self, session_id: str, limit: int = 20) -> list[dict[str, str]]:
        """
        获取适合 LLM 输入的消息格式
        
        Args:
            session_id: 会话 ID
            limit: 最大消息数量
            
        Returns:
            LLM 格式的消息列表
        """
        messages = await self.get_messages(session_id, limit)
        result = []
        
        for msg in messages:
            if msg["role"] == "tool":
                result.append({
                    "role": "tool",
                    "content": msg["content"],
                    "tool_call_id": msg["tool_call_id"],
                })
            elif msg["tool_calls"]:
                result.append({
                    "role": "assistant",
                    "content": msg["content"] or "",
                    "tool_calls": msg["tool_calls"],
                })
            else:
                result.append({
                    "role": msg["role"],
                    "content": msg["content"],
                })
        
        return result

    async def clear_session(self, session_id: str) -> None:
        """
        清除会话的所有消息
        
        Args:
            session_id: 会话 ID
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            await db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            await db.commit()


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
