"""
数据库存储模块
统一管理会话、消息和记忆存储
"""

import hashlib
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import aiosqlite
import numpy as np

from app.agent.embedding import get_embedding_client
from app.config import get_config

logger = logging.getLogger(__name__)


def compute_content_hash(content: str) -> str:
    """
    计算内容的哈希值
    
    Args:
        content: 文本内容
        
    Returns:
        SHA256 哈希值
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


class Database:
    """
    统一数据库管理类
    整合会话管理、消息存储和记忆检索功能
    """

    def __init__(self, db_path: str = "data/myclaw.db"):
        """
        初始化数据库
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._ensure_db_dir()

    def _ensure_db_dir(self) -> None:
        """确保数据库目录存在"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    async def init_db(self) -> None:
        """初始化数据库表结构"""
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
                    session_id TEXT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tool_calls TEXT,
                    tool_call_id TEXT,
                    embedding BLOB,
                    embedding_model TEXT,
                    content_hash TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS embedding_cache (
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    embedding BLOB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (provider, model, content_hash)
                )
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_session_id 
                ON messages(session_id)
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_timestamp 
                ON messages(timestamp)
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_content_hash 
                ON messages(content_hash)
            """)
            
            try:
                await db.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts 
                    USING fts5(
                        content, 
                        id UNINDEXED, 
                        session_id UNINDEXED, 
                        role UNINDEXED
                    )
                """)
                logger.info("FTS5 全文检索表初始化成功")
            except Exception as e:
                logger.warning(f"FTS5 初始化失败，将仅使用向量检索: {e}")
            
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
            会话信息字典
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
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
        generate_embedding: bool = True,
    ) -> int:
        """
        添加消息
        
        Args:
            session_id: 会话 ID
            role: 消息角色
            content: 消息内容
            tool_calls: 工具调用列表
            tool_call_id: 工具调用 ID
            generate_embedding: 是否生成嵌入向量
            
        Returns:
            消息 ID
        """
        config = get_config()
        content_hash = compute_content_hash(content)
        
        embedding = None
        embedding_model = None
        
        if generate_embedding and config.memory.enabled and content.strip():
            try:
                embedding_data = await self._get_or_create_embedding(content)
                if embedding_data:
                    embedding, embedding_model = embedding_data
            except Exception as e:
                logger.warning(f"获取嵌入向量失败: {e}")
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO messages (
                    session_id, role, content, tool_calls, tool_call_id,
                    embedding, embedding_model, content_hash, timestamp
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    role,
                    content,
                    json.dumps(tool_calls) if tool_calls else None,
                    tool_call_id,
                    embedding,
                    embedding_model,
                    content_hash,
                    datetime.now(),
                ),
            )
            message_id = cursor.lastrowid
            
            if session_id:
                await db.execute(
                    "UPDATE sessions SET updated_at = ? WHERE id = ?",
                    (datetime.now(), session_id),
                )
            
            try:
                await db.execute(
                    "INSERT INTO messages_fts(id, content, session_id, role) VALUES (?, ?, ?, ?)",
                    (message_id, content, session_id or "", role),
                )
            except Exception as e:
                logger.debug(f"FTS 索引更新失败: {e}")
            
            await db.commit()
            
            return message_id

    async def _get_or_create_embedding(self, content: str) -> Optional[tuple[bytes, str]]:
        """
        获取或创建嵌入向量（带缓存）
        
        Args:
            content: 文本内容
            
        Returns:
            (embedding_blob, model_name) 或 None
        """
        config = get_config()
        embedding_config = config.memory.embedding
        content_hash = compute_content_hash(content)
        
        provider = embedding_config.provider
        model = embedding_config.model
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT embedding FROM embedding_cache 
                WHERE provider = ? AND model = ? AND content_hash = ?
                """,
                (provider, model, content_hash),
            )
            row = await cursor.fetchone()
            if row:
                logger.debug(f"使用缓存的嵌入向量: {content_hash[:8]}...")
                return row[0], model
        
        try:
            embedding_client = get_embedding_client()
            embedding_vec = await embedding_client.get_embedding(content)
            if not embedding_vec:
                return None
            
            embedding_blob = np.array(embedding_vec, dtype=np.float32).tobytes()
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    INSERT OR REPLACE INTO embedding_cache (provider, model, content_hash, embedding, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (provider, model, content_hash, embedding_blob, datetime.now()),
                )
                await db.commit()
            
            return embedding_blob, model
        except Exception as e:
            logger.warning(f"生成嵌入向量失败: {e}")
            return None

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
            db.row_factory = aiosqlite.Row
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

    async def search_memories(
        self,
        query: str,
        session_id: Optional[str] = None,
        limit: int = 5,
    ) -> list[dict]:
        """
        搜索相关记忆（混合检索）
        
        Args:
            query: 查询文本
            session_id: 会话 ID（可选，为空时全局搜索）
            limit: 返回数量限制
            
        Returns:
            相关记忆列表
        """
        config = get_config()
        if not config.memory.enabled:
            return []
        
        hybrid_config = config.memory.hybrid_search
        
        if not query.strip():
            return []
        
        vector_results = []
        fts_results = []
        
        if hybrid_config.enabled:
            vector_results = await self._search_vector(query, session_id, limit * 2)
            fts_results = await self._search_fts(query, session_id, limit * 2)
            return self._merge_results(
                vector_results,
                fts_results,
                hybrid_config.vector_weight,
                hybrid_config.fts_weight,
                hybrid_config.min_score,
                limit,
            )
        else:
            vector_results = await self._search_vector(query, session_id, limit)
            return [r for r in vector_results if r.get("similarity", 0) >= hybrid_config.min_score][:limit]

    async def _search_vector(
        self,
        query: str,
        session_id: Optional[str] = None,
        limit: int = 10,
    ) -> list[dict]:
        """
        向量检索
        
        Args:
            query: 查询文本
            session_id: 会话 ID
            limit: 返回数量限制
            
        Returns:
            相关记忆列表
        """
        try:
            embedding_client = get_embedding_client()
            query_embedding = await embedding_client.get_embedding(query)
            if not query_embedding:
                return []
            query_vec = np.array(query_embedding, dtype=np.float32)
        except Exception as e:
            logger.warning(f"获取查询嵌入向量失败: {e}")
            return []
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            if session_id:
                cursor = await db.execute(
                    "SELECT * FROM messages WHERE session_id = ? AND embedding IS NOT NULL",
                    (session_id,),
                )
            else:
                cursor = await db.execute(
                    "SELECT * FROM messages WHERE embedding IS NOT NULL",
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
                "vector_score": similarity,
                "fts_score": 0.0,
                "timestamp": row["timestamp"],
            })
        
        memories_with_scores.sort(key=lambda x: x["similarity"], reverse=True)
        return memories_with_scores[:limit]

    async def _search_fts(
        self,
        query: str,
        session_id: Optional[str] = None,
        limit: int = 10,
    ) -> list[dict]:
        """
        FTS 全文检索
        
        Args:
            query: 查询文本
            session_id: 会话 ID
            limit: 返回数量限制
            
        Returns:
            相关记忆列表
        """
        fts_query = self._build_fts_query(query)
        if not fts_query:
            return []
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                
                if session_id:
                    cursor = await db.execute(
                        """
                        SELECT m.*, fts.rank
                        FROM messages_fts fts
                        JOIN messages m ON fts.id = m.id
                        WHERE messages_fts MATCH ? AND m.session_id = ?
                        ORDER BY fts.rank
                        LIMIT ?
                        """,
                        (fts_query, session_id, limit),
                    )
                else:
                    cursor = await db.execute(
                        """
                        SELECT m.*, fts.rank
                        FROM messages_fts fts
                        JOIN messages m ON fts.id = m.id
                        WHERE messages_fts MATCH ?
                        ORDER BY fts.rank
                        LIMIT ?
                        """,
                        (fts_query, limit),
                    )
                
                rows = await cursor.fetchall()
        except Exception as e:
            logger.debug(f"FTS 检索失败: {e}")
            return []
        
        results = []
        for row in rows:
            bm25_score = row["rank"] if "rank" in row.keys() else 0
            fts_score = self._bm25_to_score(bm25_score)
            
            results.append({
                "id": row["id"],
                "session_id": row["session_id"],
                "role": row["role"],
                "content": row["content"],
                "similarity": fts_score,
                "vector_score": 0.0,
                "fts_score": fts_score,
                "timestamp": row["timestamp"],
            })
        
        return results

    def _build_fts_query(self, raw_query: str) -> Optional[str]:
        """
        构建 FTS 查询语句
        
        Args:
            raw_query: 原始查询文本
            
        Returns:
            FTS 查询语句
        """
        tokens = re.findall(r"[\w\u4e00-\u9fff]+", raw_query)
        if not tokens:
            return None
        
        quoted = [f'"{t}"' for t in tokens[:10]]
        return " OR ".join(quoted)

    def _bm25_to_score(self, rank: float) -> float:
        """
        将 BM25 排名转换为 0-1 的相似度分数
        
        Args:
            rank: BM25 排名值（负数，越负越相关）
            
        Returns:
            相似度分数
        """
        if not isinstance(rank, (int, float)) or not float("-inf") < rank < float("inf"):
            return 0.0
        
        if rank < 0:
            relevance = -rank
            return relevance / (1 + relevance)
        
        return 1 / (1 + rank)

    def _merge_results(
        self,
        vector_results: list[dict],
        fts_results: list[dict],
        vector_weight: float,
        fts_weight: float,
        min_score: float,
        limit: int,
    ) -> list[dict]:
        """
        合并向量检索和 FTS 检索结果
        
        Args:
            vector_results: 向量检索结果
            fts_results: FTS 检索结果
            vector_weight: 向量权重
            fts_weight: FTS 权重
            min_score: 最低分数阈值
            limit: 返回数量限制
            
        Returns:
            合并后的结果列表
        """
        by_id: dict[int, dict] = {}
        
        for r in vector_results:
            by_id[r["id"]] = {
                "id": r["id"],
                "session_id": r["session_id"],
                "role": r["role"],
                "content": r["content"],
                "vector_score": r.get("vector_score", r.get("similarity", 0)),
                "fts_score": 0.0,
                "timestamp": r["timestamp"],
            }
        
        for r in fts_results:
            if r["id"] in by_id:
                by_id[r["id"]]["fts_score"] = r.get("fts_score", r.get("similarity", 0))
            else:
                by_id[r["id"]] = {
                    "id": r["id"],
                    "session_id": r["session_id"],
                    "role": r["role"],
                    "content": r["content"],
                    "vector_score": 0.0,
                    "fts_score": r.get("fts_score", r.get("similarity", 0)),
                    "timestamp": r["timestamp"],
                }
        
        merged = []
        for entry in by_id.values():
            score = vector_weight * entry["vector_score"] + fts_weight * entry["fts_score"]
            entry["similarity"] = score
            merged.append(entry)
        
        merged.sort(key=lambda x: x["similarity"], reverse=True)
        
        return [r for r in merged if r["similarity"] >= min_score][:limit]

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

    async def clear_session(self, session_id: str) -> None:
        """
        清除指定会话的所有数据
        
        Args:
            session_id: 会话 ID
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            await db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            await db.commit()

    async def cleanup_old_messages(self, max_age_days: int = 30) -> int:
        """
        清理旧消息
        
        Args:
            max_age_days: 最大保留天数
            
        Returns:
            删除的消息数量
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                DELETE FROM messages 
                WHERE timestamp < datetime('now', ?)
                """,
                (f"-{max_age_days} days",),
            )
            deleted_count = cursor.rowcount
            await db.commit()
            
            if deleted_count > 0:
                logger.info(f"清理了 {deleted_count} 条旧消息")
            
            return deleted_count


_database: Optional[Database] = None


def get_database() -> Database:
    """
    获取全局数据库实例（单例模式）
    
    Returns:
        Database 实例
    """
    global _database
    if _database is None:
        _database = Database()
    return _database
