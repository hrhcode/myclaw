"""
SQLite-VEC向量加速服务
使用sqlite-vec扩展加速向量搜索
"""
import logging
import struct
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from app.models.models import Message, LongTermMemory

logger = logging.getLogger(__name__)


class SQLiteVecService:
    """
    SQLite-VEC向量加速服务
    提供向量存储和搜索功能
    """
    
    def __init__(self, db: AsyncSession, embedding_dim: int = 384):
        """
        初始化SQLite-VEC服务
        
        Args:
            db: 数据库会话
            embedding_dim: 嵌入向量维度
        """
        self.db = db
        self.embedding_dim = embedding_dim
        self._vec_available = None
    
    async def is_available(self) -> bool:
        """
        检查sqlite-vec是否可用
        
        Returns:
            是否可用
        """
        if self._vec_available is not None:
            return self._vec_available
        
        try:
            result = await self.db.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='message_embeddings_vec'"
            ))
            if result.fetchone():
                self._vec_available = True
                logger.info("sqlite-vec向量表可用")
                return True
            else:
                self._vec_available = False
                logger.warning("sqlite-vec向量表不存在")
                return False
        except Exception as e:
            logger.warning(f"检查sqlite-vec可用性失败: {str(e)}")
            self._vec_available = False
            return False
    
    async def create_vector_tables(self) -> bool:
        """
        创建向量虚拟表
        
        Returns:
            是否成功
        """
        try:
            await self.db.execute(text(f"""
                CREATE VIRTUAL TABLE IF NOT EXISTS message_embeddings_vec USING vec0(
                    embedding FLOAT[{self.embedding_dim}]
                )
            """))
            
            await self.db.execute(text(f"""
                CREATE VIRTUAL TABLE IF NOT EXISTS long_term_memory_embeddings_vec USING vec0(
                    embedding FLOAT[{self.embedding_dim}]
                )
            """))
            
            await self.db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_message_embeddings_vec_id 
                ON message_embeddings_vec(rowid)
            """))
            
            await self.db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_long_term_memory_embeddings_vec_id 
                ON long_term_memory_embeddings_vec(rowid)
            """))
            
            await self.db.commit()
            
            logger.info("sqlite-vec向量表创建成功")
            self._vec_available = True
            return True
        except Exception as e:
            logger.error(f"创建sqlite-vec向量表失败: {str(e)}")
            self._vec_available = False
            return False
    
    async def migrate_message_embeddings(self, batch_size: int = 100) -> int:
        """
        迁移消息嵌入到向量表
        
        Args:
            batch_size: 批次大小
            
        Returns:
            迁移的记录数
        """
        try:
            result = await self.db.execute(
                select(Message)
                .where(Message.embedding.isnot(None))
                .order_by(Message.id)
            )
            messages = result.scalars().all()
            
            migrated_count = 0
            for i in range(0, len(messages), batch_size):
                batch = messages[i:i + batch_size]
                
                for msg in batch:
                    if msg.embedding:
                        embedding = self._bytes_to_float_list(msg.embedding)
                        if embedding:
                            await self.db.execute(text("""
                                INSERT OR REPLACE INTO message_embeddings_vec (rowid, embedding)
                                VALUES (:id, :embedding)
                            """), {"id": msg.id, "embedding": self._embedding_to_blob(embedding)})
                
                migrated_count += len(batch)
                
                if migrated_count % 1000 == 0:
                    logger.info(f"已迁移 {migrated_count} 条消息嵌入")
            
            await self.db.commit()
            
            logger.info(f"消息嵌入迁移完成，共迁移 {migrated_count} 条")
            return migrated_count
        except Exception as e:
            logger.error(f"迁移消息嵌入失败: {str(e)}")
            return 0
    
    async def migrate_long_term_memory_embeddings(self, batch_size: int = 100) -> int:
        """
        迁移长期记忆嵌入到向量表
        
        Args:
            batch_size: 批次大小
            
        Returns:
            迁移的记录数
        """
        try:
            result = await self.db.execute(
                select(LongTermMemory)
                .where(LongTermMemory.embedding.isnot(None))
                .order_by(LongTermMemory.id)
            )
            memories = result.scalars().all()
            
            migrated_count = 0
            for i in range(0, len(memories), batch_size):
                batch = memories[i:i + batch_size]
                
                for mem in batch:
                    if mem.embedding:
                        embedding = self._bytes_to_float_list(mem.embedding)
                        if embedding:
                            await self.db.execute(text("""
                                INSERT OR REPLACE INTO long_term_memory_embeddings_vec (rowid, embedding)
                                VALUES (:id, :embedding)
                            """), {"id": mem.id, "embedding": self._embedding_to_blob(embedding)})
                
                migrated_count += len(batch)
            
            await self.db.commit()
            
            logger.info(f"长期记忆嵌入迁移完成，共迁移 {migrated_count} 条")
            return migrated_count
        except Exception as e:
            logger.error(f"迁移长期记忆嵌入失败: {str(e)}")
            return 0
    
    async def search_messages_by_vector(
        self,
        query_embedding: List[float],
        conversation_id: Optional[int] = None,
        top_k: int = 5,
        min_score: float = 0.0
    ) -> List[Tuple[Message, float]]:
        """
        使用向量表搜索消息
        
        Args:
            query_embedding: 查询向量
            conversation_id: 会话ID（可选）
            top_k: 返回结果数量
            min_score: 最小相似度阈值
            
        Returns:
            (消息, 相似度) 元组列表
        """
        if not await self.is_available():
            logger.warning("sqlite-vec不可用，返回空结果")
            return []
        
        try:
            query_blob = self._embedding_to_blob(query_embedding)
            
            base_query = """
                SELECT m.id, vec_distance_cosine(v.embedding, :query_embedding) AS distance
                FROM message_embeddings_vec v
                JOIN messages m ON m.id = v.rowid
                WHERE m.embedding IS NOT NULL
            """
            
            params = {"query_embedding": query_blob}
            
            if conversation_id:
                base_query += " AND m.conversation_id = :conversation_id"
                params["conversation_id"] = conversation_id
            
            base_query += f" ORDER BY distance ASC LIMIT {top_k * 2}"
            
            result = await self.db.execute(text(base_query), params)
            rows = result.fetchall()
            
            scored_messages = []
            for row in rows:
                msg_id = row[0]
                distance = row[1]
                
                similarity = 1.0 - distance
                
                if similarity >= min_score:
                    msg = await self.db.get(Message, msg_id)
                    if msg:
                        scored_messages.append((msg, similarity))
            
            return scored_messages
        except Exception as e:
            logger.error(f"向量搜索消息失败: {str(e)}")
            return []
    
    async def search_long_term_memory_by_vector(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        min_score: float = 0.0
    ) -> List[Tuple[LongTermMemory, float]]:
        """
        使用向量表搜索长期记忆
        
        Args:
            query_embedding: 查询向量
            top_k: 返回结果数量
            min_score: 最小相似度阈值
            
        Returns:
            (长期记忆, 相似度) 元组列表
        """
        if not await self.is_available():
            logger.warning("sqlite-vec不可用，返回空结果")
            return []
        
        try:
            query_blob = self._embedding_to_blob(query_embedding)
            
            query_sql = """
                SELECT m.id, vec_distance_cosine(v.embedding, :query_embedding) AS distance
                FROM long_term_memory_embeddings_vec v
                JOIN long_term_memory m ON m.id = v.rowid
                WHERE m.embedding IS NOT NULL
                ORDER BY distance ASC
                LIMIT :limit
            """
            
            result = await self.db.execute(
                text(query_sql),
                {"query_embedding": query_blob, "limit": top_k * 2}
            )
            rows = result.fetchall()
            
            scored_memories = []
            for row in rows:
                mem_id = row[0]
                distance = row[1]
                
                similarity = 1.0 - distance
                
                if similarity >= min_score:
                    mem = await self.db.get(LongTermMemory, mem_id)
                    if mem:
                        scored_memories.append((mem, similarity))
            
            return scored_memories
        except Exception as e:
            logger.error(f"向量搜索长期记忆失败: {str(e)}")
            return []
    
    def _bytes_to_float_list(self, data: bytes) -> Optional[List[float]]:
        """
        将字节转换为浮点数列表
        
        Args:
            data: 字节数据
            
        Returns:
            浮点数列表
        """
        if not data:
            return None
        
        try:
            count = len(data) // 4
            return list(struct.unpack(f'{count}f', data))
        except Exception as e:
            logger.warning(f"字节转换失败: {str(e)}")
            return None
    
    def _embedding_to_blob(self, embedding: List[float]) -> bytes:
        """
        将浮点数列表转换为字节
        
        Args:
            embedding: 浮点数列表
            
        Returns:
            字节数据
        """
        return struct.pack(f'{len(embedding)}f', *embedding)


async def get_sqlite_vec_service(db: AsyncSession, embedding_dim: int = 384) -> Optional[SQLiteVecService]:
    """
    获取SQLite-VEC服务实例
    
    Args:
        db: 数据库会话
        embedding_dim: 嵌入向量维度
        
    Returns:
        SQLiteVecService实例，不可用返回None
    """
    service = SQLiteVecService(db, embedding_dim)
    
    if await service.is_available():
        return service
    else:
        logger.warning("sqlite-vec服务不可用")
        return None
