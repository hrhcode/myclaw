"""
向量搜索服务
提供消息和长期记忆的语义搜索功能
支持sqlite-vec加速和Python降级
"""
import logging
import re
from typing import List, Optional, Tuple, Dict
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, func
from app.models.models import Message, LongTermMemory
from app.services.embedding_service import get_embedding_service
from app.common.utils.embedding import (
    bytes_to_embedding,
    cosine_similarity,
    embedding_to_bytes
)
from app.common.utils.search import (
    normalize_bm25_score,
    mmr_rerank,
    apply_temporal_decay
)
from app.common.utils.logging import log_search_start, log_search_result
from app.common.constants import LOG_SEPARATOR
from app.schemas.schemas import MemorySearchResult
from app.common.config import get_config_value
from app.common.constants import EMBEDDING_MODEL_KEY, OPENROUTER_API_KEY_KEY

logger = logging.getLogger(__name__)


def escape_fts_query(query: str) -> str:
    """
    转义 FTS5 查询字符串，避免特殊字符被误解析为列限定符
    
    参考 openclaw 项目的实现，通过双引号包裹每个 token 来避免
    类似 "command:" 这样的模式被 FTS5 解析为列限定符
    
    Args:
        query: 原始查询字符串
        
    Returns:
        转义后的查询字符串，每个 token 用双引号包裹并用 AND 连接
    """
    if not query or not query.strip():
        return ""
    
    # 提取所有字母、数字、中文、下划线
    # \w 匹配字母、数字、下划线
    # \u4e00-\u9fff 匹配中文字符
    tokens = re.findall(r'[\w\u4e00-\u9fff]+', query)
    
    if not tokens:
        return ""
    
    # 每个token用双引号包裹，转义内部的双引号
    quoted_tokens = []
    for token in tokens:
        escaped_token = token.replace('"', '""')
        quoted_tokens.append(f'"{escaped_token}"')
    
    # 用 AND 连接所有 token
    return " AND ".join(quoted_tokens)


_sqlite_vec_available = None


async def check_sqlite_vec_available(db: AsyncSession) -> bool:
    """
    检查sqlite-vec是否可用
    
    Args:
        db: 数据库会话
        
    Returns:
        是否可用
    """
    global _sqlite_vec_available
    
    if _sqlite_vec_available is not None:
        return _sqlite_vec_available
    
    try:
        result = await db.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='message_embeddings_vec'"
        ))
        if result.fetchone():
            _sqlite_vec_available = True
            logger.info("sqlite-vec向量表可用，将使用加速搜索")
            return True
        else:
            _sqlite_vec_available = False
            logger.info("sqlite-vec向量表不可用，将使用Python计算")
            return False
    except Exception as e:
        logger.warning(f"检查sqlite-vec可用性失败: {str(e)}")
        _sqlite_vec_available = False
        return False


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
    
    embedding = await embedding_service.get_embedding(db, content)
    if not embedding:
        logger.warning(f"生成嵌入失败: {content[:50]}...")
        return None
    
    return embedding_to_bytes(embedding)


async def generate_embedding_standalone(content: str) -> Optional[bytes]:
    """
    生成向量嵌入（使用独立数据库会话，用于后台任务）
    
    Args:
        content: 要嵌入的内容
        
    Returns:
        嵌入字节数据，失败返回 None
    """
    from app.core.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        try:
            embedding_service = await get_embedding_service(db)
            if not embedding_service:
                logger.warning("[独立嵌入] 嵌入服务不可用，跳过向量生成")
                return None
            
            embedding = await embedding_service.get_embedding(db, content)
            if not embedding:
                logger.warning(f"[独立嵌入] 生成嵌入失败: {content[:50]}...")
                return None
            
            logger.debug(f"[独立嵌入] 成功生成嵌入，维度: {len(embedding)}")
            return embedding_to_bytes(embedding)
        except Exception as e:
            logger.error(f"[独立嵌入] 生成失败: {str(e)}")
            return None


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
    include_long_term: bool = True,
    use_hybrid: bool = True,
    vector_weight: float = 0.7,
    text_weight: float = 0.3,
    enable_mmr: bool = True,
    mmr_lambda: float = 0.7,
    enable_temporal_decay: bool = True,
    half_life_days: int = 30
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
        use_hybrid: 是否使用混合搜索
        vector_weight: 向量搜索权重
        text_weight: BM25搜索权重
        enable_mmr: 是否启用MMR重排序
        mmr_lambda: MMR参数
        enable_temporal_decay: 是否启用时间衰减
        half_life_days: 半衰期天数
        
    Returns:
        搜索结果列表
    """
    logger.info(LOG_SEPARATOR)
    logger.info("[混合搜索] 开始混合记忆搜索")
    logger.info(f"  ├─ 查询: {query[:50]}{'...' if len(query) > 50 else ''}")
    logger.info(f"  ├─ 会话ID: {conversation_id or '全部'}")
    logger.info(f"  ├─ 返回数量: {top_k}")
    logger.info(f"  ├─ 最小分数: {min_score}")
    logger.info(f"  ├─ 混合模式: {'启用' if use_hybrid else '禁用'}")
    if use_hybrid:
        logger.info(f"  │   ├─ 向量权重: {vector_weight}")
        logger.info(f"  │   └─ 文本权重: {text_weight}")
    logger.info(f"  ├─ MMR重排序: {'启用' if enable_mmr else '禁用'}")
    if enable_mmr:
        logger.info(f"  │   └─ Lambda: {mmr_lambda}")
    logger.info(f"  └─ 时间衰减: {'启用' if enable_temporal_decay else '禁用'}")
    if enable_temporal_decay:
        logger.info(f"      └─ 半衰期: {half_life_days}天")
    
    results = []
    
    if include_messages:
        logger.info("[消息搜索] 开始搜索历史消息...")
        if use_hybrid:
            message_results = await hybrid_search(
                db, query, conversation_id, top_k, min_score,
                vector_weight, text_weight, use_hybrid, search_type="message"
            )
            
            for msg, score, source in message_results:
                results.append(MemorySearchResult(
                    message_id=msg.id,
                    memory_id=None,
                    content=msg.content,
                    score=score,
                    source=f"message_{source}",
                    created_at=msg.created_at
                ))
            logger.info(f"[消息搜索] 找到 {len(message_results)} 条相关消息")
        else:
            embedding_service = await get_embedding_service(db)
            if not embedding_service:
                logger.warning("[消息搜索] 嵌入服务不可用，返回空结果")
                return []
            
            query_embedding = await embedding_service.get_embedding(db, query)
            if not query_embedding:
                logger.warning("[消息搜索] 生成查询嵌入失败")
                return []
            
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
            logger.info(f"[消息搜索] 找到 {len(message_results)} 条相关消息 (纯向量模式)")
    
    if include_long_term:
        logger.info("[长期记忆搜索] 开始搜索长期记忆...")
        if use_hybrid:
            memory_results = await hybrid_search(
                db, query, None, top_k, min_score,
                vector_weight, text_weight, use_hybrid, search_type="long_term_memory"
            )
            
            for mem, score, source in memory_results:
                results.append(MemorySearchResult(
                    message_id=None,
                    memory_id=mem.id,
                    content=mem.content,
                    score=score,
                    source=f"long_term_memory_{source}",
                    created_at=mem.created_at
                ))
            logger.info(f"[长期记忆搜索] 找到 {len(memory_results)} 条相关记忆")
        else:
            embedding_service = await get_embedding_service(db)
            if not embedding_service:
                logger.warning("[长期记忆搜索] 嵌入服务不可用，返回空结果")
                return []
            
            query_embedding = await embedding_service.get_embedding(db, query)
            if not query_embedding:
                logger.warning("[长期记忆搜索] 生成查询嵌入失败")
                return []
            
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
            logger.info(f"[长期记忆搜索] 找到 {len(memory_results)} 条相关记忆 (纯向量模式)")
    
    logger.info(f"[混合搜索] 合并结果: {len(results)} 条")
    
    if enable_mmr:
        logger.info(f"[MMR重排序] 开始MMR重排序，lambda={mmr_lambda}")
        results_with_scores = [(r, r.score, r.source) for r in results]
        reranked = mmr_rerank(results_with_scores, mmr_lambda, top_k)
        results = [MemorySearchResult(
            message_id=r.message_id if hasattr(r, 'message_id') else None,
            memory_id=r.memory_id if hasattr(r, 'memory_id') else None,
            content=r.content if hasattr(r, 'content') else '',
            score=score,
            source=source,
            created_at=getattr(r, 'created_at', None)
        ) for r, score, source in reranked]
        logger.info(f"[MMR重排序] 完成，保留 {len(results)} 条结果")
    
    if enable_temporal_decay:
        logger.info(f"[时间衰减] 应用时间衰减，半衰期={half_life_days}天")
        results_with_sources = [(r, r.score, r.source) for r in results]
        decayed = apply_temporal_decay(results_with_sources, half_life_days, enable_temporal_decay)
        results = [MemorySearchResult(
            message_id=r[0].message_id if hasattr(r[0], 'message_id') else None,
            memory_id=r[0].memory_id if hasattr(r[0], 'memory_id') else None,
            content=r[0].content if hasattr(r[0], 'content') else '',
            score=r[1],
            source=r[2],
            created_at=getattr(r[0], 'created_at', None)
        ) for r in decayed]
        logger.debug(f"[时间衰减] 完成")
    
    results.sort(key=lambda x: x.score, reverse=True)
    final_results = results[:top_k]
    
    logger.info(f"[混合搜索] 最终返回 {len(final_results)} 条结果")
    for i, r in enumerate(final_results, 1):
        source_type = "消息" if "message" in r.source else "长期记忆"
        logger.debug(f"  #{i}: [{source_type}] 分数={r.score:.3f}, 内容={r.content[:30]}...")
    logger.info(LOG_SEPARATOR)
    
    return final_results


async def index_message_embedding(message_id: int) -> bool:
    """
    为消息生成并存储向量嵌入（后台任务使用独立数据库会话）
    
    Args:
        message_id: 消息ID
        
    Returns:
        是否成功
    """
    from app.core.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        try:
            message = await db.get(Message, message_id)
            if not message:
                logger.warning(f"[消息嵌入] 消息 {message_id} 不存在")
                return False
            
            content = message.content
            embedding_bytes = await generate_embedding_standalone(content)
            
            if embedding_bytes:
                message.embedding = embedding_bytes
                model = await get_config_value(db, EMBEDDING_MODEL_KEY)
                message.embedding_model = model or "nvidia/llama-nemotron-embed-vl-1b-v2:free"
                await db.commit()
                logger.info(f"[消息嵌入] 消息 {message.id} 向量嵌入已生成")
                return True
            
            logger.warning(f"[消息嵌入] 消息 {message_id} 嵌入生成失败")
            return False
        except Exception as e:
            logger.error(f"[消息嵌入] 索引消息 {message_id} 失败: {str(e)}")
            return False


async def index_long_term_memory_embedding(memory_id: int) -> bool:
    """
    为长期记忆生成并存储向量嵌入（后台任务使用独立数据库会话）
    
    Args:
        memory_id: 长期记忆ID
        
    Returns:
        是否成功
    """
    from app.core.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        try:
            memory = await db.get(LongTermMemory, memory_id)
            if not memory:
                logger.warning(f"[长期记忆嵌入] 长期记忆 {memory_id} 不存在")
                return False
            
            content = memory.content
            embedding_bytes = await generate_embedding_standalone(content)
            
            if embedding_bytes:
                memory.embedding = embedding_bytes
                model = await get_config_value(db, EMBEDDING_MODEL_KEY)
                memory.embedding_model = model or "nvidia/llama-nemotron-embed-vl-1b-v2:free"
                await db.commit()
                logger.info(f"[长期记忆嵌入] 长期记忆 {memory.id} 向量嵌入已生成")
                return True
            
            logger.warning(f"[长期记忆嵌入] 长期记忆 {memory_id} 嵌入生成失败")
            return False
        except Exception as e:
            logger.error(f"[长期记忆嵌入] 索引长期记忆 {memory_id} 失败: {str(e)}")
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
    from app.core.database import AsyncSessionLocal
    
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


async def search_messages_by_bm25(
    db: AsyncSession,
    query: str,
    conversation_id: Optional[int] = None,
    top_k: int = 5,
    min_score: float = 0.0
) -> List[Tuple[Message, float]]:
    """
    通过BM25全文搜索消息
    
    Args:
        db: 数据库会话
        query: 搜索查询
        conversation_id: 会话ID（可选）
        top_k: 返回结果数量
        min_score: 最小BM25分数阈值
        
    Returns:
        (消息, BM25分数) 元组列表
    """
    try:
        result = await db.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='messages_fts'"
        ))
        if not result.fetchone():
            logger.warning("messages_fts表不存在，BM25搜索不可用，请运行数据库迁移")
            return []
        
        # 转义查询以避免FTS5特殊字符问题
        escaped_query = escape_fts_query(query)
        if not escaped_query:
            logger.warning(f"BM25搜索查询为空，原查询: {query}")
            return []
        
        base_query = """
            SELECT m.*, bm25(messages_fts) AS bm25_score
            FROM messages m
            JOIN messages_fts fts ON m.id = fts.rowid
            WHERE messages_fts MATCH :query
        """
        
        params = {"query": escaped_query}
        
        if conversation_id:
            base_query += " AND m.conversation_id = :conversation_id"
            params["conversation_id"] = conversation_id
        
        base_query += f" ORDER BY bm25_score DESC LIMIT {top_k * 4}"
        
        result = await db.execute(text(base_query), params)
        rows = result.fetchall()
        
        scored_messages = []
        for row in rows:
            msg = await db.get(Message, row[0])
            if msg:
                bm25_score = row[-1]
                if bm25_score >= min_score:
                    scored_messages.append((msg, bm25_score))
        
        logger.debug(f"BM25搜索消息成功，找到 {len(scored_messages)} 条结果")
        return scored_messages
    except Exception as e:
        logger.error(f"BM25搜索消息失败: {str(e)}", exc_info=True)
        return []


async def search_long_term_memory_by_bm25(
    db: AsyncSession,
    query: str,
    top_k: int = 5,
    min_score: float = 0.0
) -> List[Tuple[LongTermMemory, float]]:
    """
    通过BM25全文搜索长期记忆
    
    Args:
        db: 数据库会话
        query: 搜索查询
        top_k: 返回结果数量
        min_score: 最小BM25分数阈值
        
    Returns:
        (长期记忆, BM25分数) 元组列表
    """
    try:
        result = await db.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='long_term_memory_fts'"
        ))
        if not result.fetchone():
            logger.warning("long_term_memory_fts表不存在，BM25搜索不可用，请运行数据库迁移")
            return []
        
        # 转义查询以避免FTS5特殊字符问题
        escaped_query = escape_fts_query(query)
        if not escaped_query:
            logger.warning(f"BM25搜索查询为空，原查询: {query}")
            return []
        
        query_sql = """
            SELECT m.*, bm25(long_term_memory_fts) AS bm25_score
            FROM long_term_memory m
            JOIN long_term_memory_fts fts ON m.id = fts.rowid
            WHERE long_term_memory_fts MATCH :query
            ORDER BY bm25_score DESC
            LIMIT :limit
        """
        
        result = await db.execute(
            text(query_sql),
            {"query": escaped_query, "limit": top_k * 4}
        )
        rows = result.fetchall()
        
        scored_memories = []
        for row in rows:
            memory = await db.get(LongTermMemory, row[0])
            if memory:
                bm25_score = row[-1]
                if bm25_score >= min_score:
                    scored_memories.append((memory, bm25_score))
        
        logger.debug(f"BM25搜索长期记忆成功，找到 {len(scored_memories)} 条结果")
        return scored_memories
    except Exception as e:
        logger.error(f"BM25搜索长期记忆失败: {str(e)}", exc_info=True)
        return []


async def hybrid_search(
    db: AsyncSession,
    query: str,
    conversation_id: Optional[int] = None,
    top_k: int = 5,
    min_score: float = 0.5,
    vector_weight: float = 0.7,
    text_weight: float = 0.3,
    use_hybrid: bool = True,
    search_type: str = "message"
) -> List[Tuple[object, float, str]]:
    """
    混合搜索（向量 + BM25）
    
    Args:
        db: 数据库会话
        query: 搜索查询
        conversation_id: 会话ID（可选）
        top_k: 返回结果数量
        min_score: 最小分数阈值
        vector_weight: 向量搜索权重
        text_weight: BM25搜索权重
        use_hybrid: 是否使用混合搜索
        search_type: 搜索类型 ("message" 或 "long_term_memory")
        
    Returns:
        (对象, 分数, 来源) 元组列表
    """
    logger.debug(f"[混合搜索-{search_type}] 开始，查询: {query[:30]}...")
    
    embedding_service = await get_embedding_service(db)
    if not embedding_service:
        logger.warning(f"[混合搜索-{search_type}] 嵌入服务不可用，仅使用BM25搜索")
        if use_hybrid:
            if search_type == "message":
                results = await search_messages_by_bm25(
                    db, query, conversation_id, top_k, min_score
                )
            else:
                results = await search_long_term_memory_by_bm25(
                    db, query, top_k, min_score
                )
            logger.info(f"[混合搜索-{search_type}] BM25搜索完成，找到 {len(results)} 条结果")
            return [(obj, score, "bm25") for obj, score in results]
        else:
            return []
    
    if not use_hybrid:
        logger.debug(f"[混合搜索-{search_type}] 纯向量模式")
        query_embedding = await embedding_service.get_embedding(db, query)
        if not query_embedding:
            logger.warning(f"[混合搜索-{search_type}] 生成查询嵌入失败")
            return []
        
        if search_type == "message":
            results = await search_messages_by_similarity(
                db, query_embedding, conversation_id, top_k, min_score
            )
        else:
            results = await search_long_term_memory_by_similarity(
                db, query_embedding, top_k, min_score
            )
        logger.info(f"[混合搜索-{search_type}] 向量搜索完成，找到 {len(results)} 条结果")
        return [(obj, score, "vector") for obj, score in results]
    
    query_embedding = await embedding_service.get_embedding(db, query)
    if not query_embedding:
        logger.warning(f"[混合搜索-{search_type}] 生成查询嵌入失败，仅使用BM25搜索")
        if search_type == "message":
            results = await search_messages_by_bm25(
                db, query, conversation_id, top_k, min_score
            )
        else:
            results = await search_long_term_memory_by_bm25(
                db, query, top_k, min_score
            )
        logger.info(f"[混合搜索-{search_type}] BM25搜索完成，找到 {len(results)} 条结果")
        return [(obj, score, "bm25") for obj, score in results]
    
    logger.debug(f"[混合搜索-{search_type}] 执行向量搜索...")
    if search_type == "message":
        vector_results = await search_messages_by_similarity(
            db, query_embedding, conversation_id, top_k * 4, min_score
        )
    else:
        vector_results = await search_long_term_memory_by_similarity(
            db, query_embedding, top_k * 4, min_score
        )
    logger.debug(f"[混合搜索-{search_type}] 向量搜索找到 {len(vector_results)} 条")
    
    logger.debug(f"[混合搜索-{search_type}] 执行BM25搜索...")
    if search_type == "message":
        bm25_results = await search_messages_by_bm25(
            db, query, conversation_id, top_k * 4, min_score
        )
    else:
        bm25_results = await search_long_term_memory_by_bm25(
            db, query, top_k * 4, min_score
        )
    logger.debug(f"[混合搜索-{search_type}] BM25搜索找到 {len(bm25_results)} 条")
    
    merged_results = {}
    
    for obj, vec_score in vector_results:
        obj_id = obj.id
        if obj_id not in merged_results:
            merged_results[obj_id] = {
                "obj": obj,
                "vector_score": vec_score,
                "bm25_score": 0.0,
                "source": "vector"
            }
        else:
            merged_results[obj_id]["vector_score"] = vec_score
    
    for obj, bm25_score in bm25_results:
        obj_id = obj.id
        if obj_id not in merged_results:
            merged_results[obj_id] = {
                "obj": obj,
                "vector_score": 0.0,
                "bm25_score": bm25_score,
                "source": "bm25"
            }
        else:
            merged_results[obj_id]["bm25_score"] = bm25_score
            merged_results[obj_id]["source"] = "hybrid"
    
    logger.debug(f"[混合搜索-{search_type}] 合并后共 {len(merged_results)} 条唯一结果")
    
    final_results = []
    for result_id, result_data in merged_results.items():
        vec_score = result_data["vector_score"]
        bm25_score = result_data["bm25_score"]
        
        normalized_bm25 = normalize_bm25_score(bm25_score) if isinstance(bm25_score, (int, float)) else 0.0
        
        final_score = vector_weight * vec_score + text_weight * normalized_bm25
        
        if final_score >= min_score:
            final_results.append((result_data["obj"], final_score, result_data["source"]))
    
    final_results.sort(key=lambda x: x[1], reverse=True)
    
    logger.info(f"[混合搜索-{search_type}] 完成，返回 {len(final_results[:top_k])} 条结果")
    return final_results[:top_k]
