"""
向量搜索服务
提供消息和长期记忆的语义搜索功能
"""
import logging
from typing import List, Optional, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Message, LongTermMemory
from app.embedding_service import (
    get_embedding_service,
    bytes_to_embedding,
    cosine_similarity,
    embedding_to_bytes
)
from app.schemas import MemorySearchResult
from app.api.config import get_config_value, EMBEDDING_MODEL_KEY, OPENROUTER_API_KEY_KEY

logger = logging.getLogger(__name__)


async def generate_and_store_embedding(
    db: AsyncSession,
    content: str,
    model_type: str = "message",
    record_id: int = None
) -> Optional[bytes]:
    """
    生成并存储向量嵌入
    
    Args:
        db: 数据库会话
        content: 要嵌入的内容
        model_type: 模型类型 ("message" 或 "memory")
        record_id: 记录ID
        
    Returns:
        嵌入字节数据，失败返回 None
    """
    embedding_service = await get_embedding_service(db)
    if not embedding_service:
        logger.warning("嵌入服务不可用，跳过向量生成")
        return None
    
    embedding = await embedding_service.get_embedding(content)
    if not embedding:
        logger.warning(f"生成嵌入失败: {content[:50]}...")
        return None
    
    return embedding_to_bytes(embedding)


async def search_messages_by_similarity(
    db: AsyncSession,
    query_embedding: List[float],
    conversation_id: Optional[int] = None,
    top_k: int = 5,
    min_score: float = 0.5
) -> List[Tuple[Message, float]]:
    """
    通过向量相似度搜索消息
    
    Args:
        db: 数据库会话
        query_embedding: 查询向量
        conversation_id: 会话ID（可选）
        top_k: 返回结果数量
        min_score: 最小相似度阈值
        
    Returns:
        (消息, 相似度) 元组列表
    """
    query = select(Message).where(Message.embedding.isnot(None))
    
    if conversation_id:
        query = query.where(Message.conversation_id == conversation_id)
    
    query = query.order_by(Message.created_at.desc()).limit(100)
    
    result = await db.execute(query)
    messages = result.scalars().all()
    
    scored_messages = []
    for msg in messages:
        if not msg.embedding:
            continue
        
        msg_embedding = bytes_to_embedding(msg.embedding)
        if not msg_embedding:
            continue
        
        similarity = cosine_similarity(query_embedding, msg_embedding)
        
        if similarity >= min_score:
            scored_messages.append((msg, similarity))
    
    scored_messages.sort(key=lambda x: x[1], reverse=True)
    
    return scored_messages[:top_k]


async def search_long_term_memory_by_similarity(
    db: AsyncSession,
    query_embedding: List[float],
    top_k: int = 5,
    min_score: float = 0.5
) -> List[Tuple[LongTermMemory, float]]:
    """
    通过向量相似度搜索长期记忆
    
    Args:
        db: 数据库会话
        query_embedding: 查询向量
        top_k: 返回结果数量
        min_score: 最小相似度阈值
        
    Returns:
        (长期记忆, 相似度) 元组列表
    """
    query = select(LongTermMemory).where(LongTermMemory.embedding.isnot(None))
    query = query.order_by(LongTermMemory.importance.desc(), LongTermMemory.updated_at.desc())
    
    result = await db.execute(query)
    memories = result.scalars().all()
    
    scored_memories = []
    for mem in memories:
        if not mem.embedding:
            continue
        
        mem_embedding = bytes_to_embedding(mem.embedding)
        if not mem_embedding:
            continue
        
        similarity = cosine_similarity(query_embedding, mem_embedding)
        
        if similarity >= min_score:
            scored_memories.append((mem, similarity))
    
    scored_memories.sort(key=lambda x: x[1], reverse=True)
    
    return scored_memories[:top_k]


async def hybrid_memory_search(
    db: AsyncSession,
    query: str,
    conversation_id: Optional[int] = None,
    top_k: int = 5,
    min_score: float = 0.5,
    include_messages: bool = True,
    include_long_term: bool = True
) -> List[MemorySearchResult]:
    """
    混合记忆搜索（消息 + 长期记忆）
    
    Args:
        db: 数据库会话
        query: 搜索查询
        conversation_id: 会话ID（可选）
        top_k: 返回结果数量
        min_score: 最小相似度阈值
        include_messages: 是否包含消息
        include_long_term: 是否包含长期记忆
        
    Returns:
        搜索结果列表
    """
    embedding_service = await get_embedding_service(db)
    if not embedding_service:
        logger.warning("嵌入服务不可用，返回空结果")
        return []
    
    query_embedding = await embedding_service.get_embedding(query)
    if not query_embedding:
        logger.warning("生成查询嵌入失败")
        return []
    
    results = []
    
    if include_messages:
        message_results = await search_messages_by_similarity(
            db, query_embedding, conversation_id, top_k, min_score
        )
        
        for msg, score in message_results:
            results.append(MemorySearchResult(
                message_id=msg.id,
                memory_id=None,
                content=msg.content,
                score=score,
                source="message",
                created_at=msg.created_at
            ))
    
    if include_long_term:
        memory_results = await search_long_term_memory_by_similarity(
            db, query_embedding, top_k, min_score
        )
        
        for mem, score in memory_results:
            results.append(MemorySearchResult(
                message_id=None,
                memory_id=mem.id,
                content=mem.content,
                score=score,
                source="long_term_memory",
                created_at=mem.created_at
            ))
    
    results.sort(key=lambda x: x.score, reverse=True)
    
    return results[:top_k]


async def index_message_embedding(message_id: int) -> bool:
    """
    为消息生成并存储向量嵌入（后台任务使用独立数据库会话）
    
    Args:
        message_id: 消息ID
        
    Returns:
        是否成功
    """
    from app.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        try:
            message = await db.get(Message, message_id)
            if not message:
                logger.warning(f"消息 {message_id} 不存在")
                return False
            
            embedding_bytes = await generate_and_store_embedding(db, message.content)
            
            if embedding_bytes:
                message.embedding = embedding_bytes
                model = await get_config_value(db, EMBEDDING_MODEL_KEY)
                message.embedding_model = model or "nvidia/llama-nemotron-embed-vl-1b-v2:free"
                await db.commit()
                logger.info(f"消息 {message.id} 向量嵌入已生成")
                return True
            
            return False
        except Exception as e:
            logger.error(f"索引消息 {message_id} 失败: {str(e)}")
            return False


async def index_long_term_memory_embedding(memory_id: int) -> bool:
    """
    为长期记忆生成并存储向量嵌入（后台任务使用独立数据库会话）
    
    Args:
        memory_id: 长期记忆ID
        
    Returns:
        是否成功
    """
    from app.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        try:
            memory = await db.get(LongTermMemory, memory_id)
            if not memory:
                logger.warning(f"长期记忆 {memory_id} 不存在")
                return False
            
            embedding_bytes = await generate_and_store_embedding(db, memory.content)
            
            if embedding_bytes:
                memory.embedding = embedding_bytes
                model = await get_config_value(db, EMBEDDING_MODEL_KEY)
                memory.embedding_model = model or "nvidia/llama-nemotron-embed-vl-1b-v2:free"
                await db.commit()
                logger.info(f"长期记忆 {memory.id} 向量嵌入已生成")
                return True
            
            return False
        except Exception as e:
            logger.error(f"索引长期记忆 {memory_id} 失败: {str(e)}")
            return False


async def batch_index_conversation_messages(
    conversation_id: int,
    batch_size: int = 10
) -> int:
    """
    批量为会话中的消息生成向量嵌入（使用独立数据库会话）
    
    Args:
        conversation_id: 会话ID
        batch_size: 批次大小
        
    Returns:
        成功索引的消息数量
    """
    from app.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        query = select(Message).where(
            Message.conversation_id == conversation_id,
            Message.embedding.is_(None)
        ).order_by(Message.created_at)
        
        result = await db.execute(query)
        messages = result.scalars().all()
        
        message_ids = [msg.id for msg in messages]
    
    indexed_count = 0
    for msg_id in message_ids:
        if await index_message_embedding(msg_id):
            indexed_count += 1
    
    logger.info(f"会话 {conversation_id} 索引完成，共 {indexed_count} 条消息")
    return indexed_count
