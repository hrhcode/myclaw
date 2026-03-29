"""
记忆搜索API
提供语义搜索和长期记忆管理功能的HTTP接口
业务逻辑已委托给Service/DAO层，API层仅处理HTTP请求/响应
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.dao.memory_dao import MemoryDAO
from app.services.vector_search_service import (
    hybrid_memory_search,
    index_long_term_memory_embedding,
    batch_index_conversation_messages
)
from app.schemas.schemas import (
    MemorySearchRequest,
    MemorySearchResponse,
    LongTermMemoryCreate,
    LongTermMemoryUpdate,
    LongTermMemoryResponse
)
from app.common.constants import LOG_SEPARATOR
import logging
import asyncio

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/memory/search", response_model=MemorySearchResponse)
async def search_memory(
    request: MemorySearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    语义搜索记忆（消息 + 长期记忆）

    通过向量相似度搜索相关的历史消息和长期记忆
    """
    logger.info(LOG_SEPARATOR)
    logger.info("[记忆搜索API] 收到搜索请求")
    logger.info(f"  ├─ 查询: {request.query[:50]}{'...' if len(request.query) > 50 else ''}")
    logger.info(f"  ├─ 会话ID: {request.conversation_id or '全部'}")
    logger.info(f"  ├─ 返回数量: {request.top_k}")
    logger.info(f"  ├─ 最小分数: {request.min_score}")
    logger.info(f"  └─ 混合模式: {'启用' if request.use_hybrid else '禁用'}")

    try:
        results = await hybrid_memory_search(
            db=db,
            query=request.query,
            conversation_id=request.conversation_id,
            top_k=request.top_k,
            min_score=request.min_score,
            include_messages=True,
            include_long_term=True,
            use_hybrid=request.use_hybrid,
            vector_weight=request.vector_weight,
            text_weight=request.text_weight,
            enable_mmr=request.enable_mmr,
            mmr_lambda=request.mmr_lambda,
            enable_temporal_decay=request.enable_temporal_decay,
            half_life_days=request.half_life_days
        )

        logger.info(f"[记忆搜索API] 搜索完成，返回 {len(results)} 条结果")
        for i, r in enumerate(results, 1):
            logger.debug(f"  #{i}: 分数={r.score:.3f}, 来源={r.source}")
        logger.info(LOG_SEPARATOR)

        return MemorySearchResponse(results=results)

    except Exception as e:
        logger.error(f"[记忆搜索API] 搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.post("/memory/index/{conversation_id}")
async def index_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    为指定会话的所有消息生成向量嵌入
    """
    logger.info(LOG_SEPARATOR)
    logger.info(f"[消息索引API] 开始索引会话 {conversation_id} 的消息")

    try:
        indexed_count = await batch_index_conversation_messages(conversation_id)

        logger.info(f"[消息索引API] 索引完成，共索引 {indexed_count} 条消息")
        logger.info(LOG_SEPARATOR)

        return {
            "message": "索引完成",
            "conversation_id": conversation_id,
            "indexed_count": indexed_count
        }

    except Exception as e:
        logger.error(f"[消息索引API] 索引失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"索引失败: {str(e)}")


@router.get("/memory/long-term", response_model=List[LongTermMemoryResponse])
async def list_long_term_memories(
    db: AsyncSession = Depends(get_db),
    limit: int = 50
):
    """
    获取所有长期记忆
    """
    logger.info(f"[长期记忆API] 获取长期记忆列表，限制: {limit}")

    memories = await MemoryDAO.list_all(db, limit)

    logger.info(f"[长期记忆API] 返回 {len(memories)} 条长期记忆")

    return memories


@router.post("/memory/long-term", response_model=LongTermMemoryResponse)
async def create_long_term_memory(
    memory_create: LongTermMemoryCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建长期记忆
    """
    logger.info(LOG_SEPARATOR)
    logger.info("[长期记忆API] 创建新长期记忆")
    logger.info(f"  ├─ Key: {memory_create.key or '无'}")
    logger.info(f"  ├─ 内容: {memory_create.content[:50]}{'...' if len(memory_create.content) > 50 else ''}")
    logger.info(f"  ├─ 重要性: {memory_create.importance}")
    logger.info(f"  └─ 来源: {memory_create.source or '手动创建'}")

    memory = await MemoryDAO.create(
        db=db,
        content=memory_create.content,
        key=memory_create.key,
        importance=memory_create.importance,
        source=memory_create.source
    )

    logger.info(f"[长期记忆API] 记忆已保存，ID: {memory.id}")

    asyncio.create_task(index_long_term_memory_embedding(memory.id))
    logger.info(f"[长期记忆API] 已创建异步嵌入任务")
    logger.info(LOG_SEPARATOR)

    return memory


@router.get("/memory/long-term/{memory_id}", response_model=LongTermMemoryResponse)
async def get_long_term_memory(
    memory_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定的长期记忆
    """
    logger.debug(f"[长期记忆API] 获取记忆 ID: {memory_id}")

    memory = await MemoryDAO.get_by_id(db, memory_id)

    if not memory:
        logger.warning(f"[长期记忆API] 记忆不存在，ID: {memory_id}")
        raise HTTPException(status_code=404, detail="长期记忆不存在")

    return memory


@router.put("/memory/long-term/{memory_id}", response_model=LongTermMemoryResponse)
async def update_long_term_memory(
    memory_id: int,
    memory_update: LongTermMemoryUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    更新长期记忆
    """
    logger.info(LOG_SEPARATOR)
    logger.info(f"[长期记忆API] 更新记忆 ID: {memory_id}")

    existing_memory = await MemoryDAO.get_by_id(db, memory_id)
    if not existing_memory:
        logger.warning(f"[长期记忆API] 记忆不存在，ID: {memory_id}")
        raise HTTPException(status_code=404, detail="长期记忆不存在")

    memory = await MemoryDAO.update(
        db=db,
        memory_id=memory_id,
        content=memory_update.content,
        key=memory_update.key,
        importance=memory_update.importance,
        source=memory_update.source
    )

    if memory_update.content is not None:
        asyncio.create_task(index_long_term_memory_embedding(memory.id))
        logger.info(f"[长期记忆API] 已创建异步嵌入任务（内容已更新）")

    logger.info(f"[长期记忆API] 更新完成")
    logger.info(LOG_SEPARATOR)

    return memory


@router.delete("/memory/long-term/{memory_id}")
async def delete_long_term_memory(
    memory_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    删除长期记忆
    """
    logger.info(f"[长期记忆API] 删除记忆 ID: {memory_id}")

    success = await MemoryDAO.delete(db, memory_id)

    if not success:
        logger.warning(f"[长期记忆API] 记忆不存在，ID: {memory_id}")
        raise HTTPException(status_code=404, detail="长期记忆不存在")

    logger.info(f"[长期记忆API] 记忆已删除，ID: {memory_id}")

    return {"message": "长期记忆已删除"}
