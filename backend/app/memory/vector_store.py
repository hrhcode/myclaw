"""
向量存储模块
实现基于智谱 AI embedding 的对话记忆存储和检索
"""

import json
import logging
import math
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiosqlite
import numpy as np

from app.agent.llm import get_llm_client
from app.config import get_config

logger = logging.getLogger(__name__)


class MemoryStore:
    """
    记忆存储类
    使用向量相似度进行对话记忆的存储和检索
    """

    def __init__(self, db_path: str = "data/memory.db"):
        """
        初始化记忆存储
        
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
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    embedding BLOB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_session_id 
                ON memories(session_id)
            """)
            
            await db.commit()
        logger.info(f"记忆数据库初始化完成: {self.db_path}")

    async def add_memory(
        self,
        session_id: str,
        role: str,
        content: str,
    ) -> int:
        """
        添加记忆
        
        Args:
            session_id: 会话 ID
            role: 角色 (user/assistant)
            content: 内容
            
        Returns:
            记忆 ID
        """
        config = get_config()
        
        embedding = None
        if config.memory.enabled and content.strip():
            try:
                llm = get_llm_client()
                embedding_vec = await llm.get_embedding(content)
                embedding = np.array(embedding_vec, dtype=np.float32).tobytes()
            except Exception as e:
                logger.warning(f"获取嵌入向量失败: {e}")
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO memories (session_id, role, content, embedding, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (session_id, role, content, embedding, datetime.now()),
            )
            memory_id = cursor.lastrowid
            await db.commit()
            
            await self._cleanup_old_memories(db)
            
            return memory_id

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
            session_id: 会话 ID（可选，用于限定搜索范围）
            limit: 返回数量限制
            
        Returns:
            相关记忆列表
        """
        config = get_config()
        if not config.memory.enabled:
            return []
        
        try:
            llm = get_llm_client()
            query_embedding = await llm.get_embedding(query)
            query_vec = np.array(query_embedding, dtype=np.float32)
        except Exception as e:
            logger.warning(f"获取查询嵌入向量失败: {e}")
            return []
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = sqlite3.Row
            
            if session_id:
                cursor = await db.execute(
                    "SELECT * FROM memories WHERE session_id = ? AND embedding IS NOT NULL",
                    (session_id,),
                )
            else:
                cursor = await db.execute(
                    "SELECT * FROM memories WHERE embedding IS NOT NULL",
                )
            
            rows = await cursor.fetchall()
            
        memories_with_scores = []
        for row in rows:
            stored_embedding = np.frombuffer(row["embedding"], dtype=np.float32)
            similarity = self._cosine_similarity(query_vec, stored_embedding)
            
            memories_with_scores.append({
                "id": row["id"],
                "session_id": row["session_id"],
                "role": row["role"],
                "content": row["content"],
                "similarity": similarity,
                "created_at": row["created_at"],
            })
        
        memories_with_scores.sort(key=lambda x: x["similarity"], reverse=True)
        
        return memories_with_scores[:limit]

    async def get_recent_memories(
        self,
        session_id: str,
        limit: int = 10,
    ) -> list[dict]:
        """
        获取最近的记忆
        
        Args:
            session_id: 会话 ID
            limit: 返回数量限制
            
        Returns:
            记忆列表
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = sqlite3.Row
            cursor = await db.execute(
                """
                SELECT id, session_id, role, content, created_at
                FROM memories 
                WHERE session_id = ?
                ORDER BY created_at DESC 
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
                    "created_at": row["created_at"],
                }
                for row in rows
            ]

    async def clear_memories(self, session_id: str) -> None:
        """
        清除指定会话的记忆
        
        Args:
            session_id: 会话 ID
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM memories WHERE session_id = ?", (session_id,))
            await db.commit()

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        计算余弦相似度
        
        Args:
            vec1: 向量1
            vec2: 向量2
            
        Returns:
            相似度分数
        """
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))

    async def _cleanup_old_memories(self, db: aiosqlite.Connection) -> None:
        """
        清理旧记忆，保持数量在限制内
        
        Args:
            db: 数据库连接
        """
        config = get_config()
        max_memories = config.memory.max_memories
        
        cursor = await db.execute("SELECT COUNT(*) FROM memories")
        count = (await cursor.fetchone())[0]
        
        if count > max_memories:
            delete_count = count - max_memories
            await db.execute(
                """
                DELETE FROM memories 
                WHERE id IN (
                    SELECT id FROM memories 
                    ORDER BY created_at ASC 
                    LIMIT ?
                )
                """,
                (delete_count,),
            )
            await db.commit()
            logger.info(f"清理了 {delete_count} 条旧记忆")


_memory_store: Optional[MemoryStore] = None


def get_memory_store() -> MemoryStore:
    """
    获取全局记忆存储实例（单例模式）
    
    Returns:
        MemoryStore 实例
    """
    global _memory_store
    if _memory_store is None:
        _memory_store = MemoryStore()
    return _memory_store
