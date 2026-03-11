"""
向量存储模块
实现基于 Embedding 和 FTS 的混合检索对话记忆存储
"""

import logging
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiosqlite
import numpy as np

from app.agent.embedding import get_embedding_client
from app.config import get_config

logger = logging.getLogger(__name__)


class MemoryStore:
    """
    记忆存储类
    支持向量检索和 FTS 全文检索的混合搜索
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
            
            try:
                await db.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts 
                    USING fts5(content, content='memories', content_rowid='id')
                """)
                logger.info("FTS5 全文检索表初始化成功")
            except Exception as e:
                logger.warning(f"FTS5 初始化失败，将仅使用向量检索: {e}")
            
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
                embedding_client = get_embedding_client()
                embedding_vec = await embedding_client.get_embedding(content)
                if embedding_vec:
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
            
            try:
                await db.execute(
                    "INSERT INTO memories_fts(rowid, content) VALUES (?, ?)",
                    (memory_id, content),
                )
            except Exception as e:
                logger.debug(f"FTS 索引更新失败: {e}")
            
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
        搜索相关记忆（混合检索）
        
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
                "vector_score": similarity,
                "fts_score": 0.0,
                "created_at": row["created_at"],
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
                db.row_factory = sqlite3.Row
                
                if session_id:
                    cursor = await db.execute(
                        """
                        SELECT m.*, fts.rank
                        FROM memories_fts fts
                        JOIN memories m ON fts.rowid = m.id
                        WHERE memories_fts MATCH ? AND m.session_id = ?
                        ORDER BY fts.rank
                        LIMIT ?
                        """,
                        (fts_query, session_id, limit),
                    )
                else:
                    cursor = await db.execute(
                        """
                        SELECT m.*, fts.rank
                        FROM memories_fts fts
                        JOIN memories m ON fts.rowid = m.id
                        WHERE memories_fts MATCH ?
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
                "created_at": row["created_at"],
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
                "created_at": r["created_at"],
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
                    "created_at": r["created_at"],
                }
        
        merged = []
        for entry in by_id.values():
            score = vector_weight * entry["vector_score"] + fts_weight * entry["fts_score"]
            entry["similarity"] = score
            merged.append(entry)
        
        merged.sort(key=lambda x: x["similarity"], reverse=True)
        
        return [r for r in merged if r["similarity"] >= min_score][:limit]

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
