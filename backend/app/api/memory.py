"""
记忆搜索 API
提供语义搜索和长期记忆管理功能
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.database import get_db
from app.models import LongTermMemory
from app.schemas import (
    MemorySearchRequest,
    MemorySearchResponse,
    MemorySearchResult,
    LongTermMemoryCreate,
    LongTermMemoryUpdate,
    LongTermMemoryResponse
)
from app.vector_search_service import (
    hybrid_memory_search,
    index_long_term_memory_embedding,
    batch_index_conversation_messages
)
import logging

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
    logger.info(f"记忆搜索: query='{request.query[:30]}...', top_k={request.top_k}, use_hybrid={request.use_hybrid}")
    
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
        
        logger.info(f"搜索完成，找到 {len(results)} 条结果")
        return MemorySearchResponse(results=results)
        
    except Exception as e:
        logger.error(f"记忆搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.post("/memory/index/{conversation_id}")
async def index_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    为指定会话的所有消息生成向量嵌入
    """
    logger.info(f"开始索引会话 {conversation_id} 的消息")
    
    try:
        indexed_count = await batch_index_conversation_messages(conversation_id)
        
        return {
            "message": "索引完成",
            "conversation_id": conversation_id,
            "indexed_count": indexed_count
        }
        
    except Exception as e:
        logger.error(f"索引失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"索引失败: {str(e)}")


@router.get("/memory/long-term", response_model=List[LongTermMemoryResponse])
async def list_long_term_memories(
    db: AsyncSession = Depends(get_db),
    limit: int = 50
):
    """
    获取所有长期记忆
    """
    logger.info("获取长期记忆列表")
    
    result = await db.execute(
        select(LongTermMemory)
        .order_by(LongTermMemory.importance.desc(), LongTermMemory.updated_at.desc())
        .limit(limit)
    )
    memories = result.scalars().all()
    
    return memories


@router.post("/memory/long-term", response_model=LongTermMemoryResponse)
async def create_long_term_memory(
    memory_create: LongTermMemoryCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建长期记忆
    """
    import asyncio
    
    logger.info(f"创建长期记忆: key={memory_create.key}")
    
    memory = LongTermMemory(
        key=memory_create.key,
        content=memory_create.content,
        importance=memory_create.importance,
        source=memory_create.source
    )
    
    db.add(memory)
    await db.commit()
    await db.refresh(memory)
    
    asyncio.create_task(index_long_term_memory_embedding(memory.id))
    
    return memory


@router.get("/memory/long-term/{memory_id}", response_model=LongTermMemoryResponse)
async def get_long_term_memory(
    memory_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定的长期记忆
    """
    memory = await db.get(LongTermMemory, memory_id)
    
    if not memory:
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
    import asyncio
    
    memory = await db.get(LongTermMemory, memory_id)
    
    if not memory:
        raise HTTPException(status_code=404, detail="长期记忆不存在")
    
    if memory_update.key is not None:
        memory.key = memory_update.key
    if memory_update.content is not None:
        memory.content = memory_update.content
    if memory_update.importance is not None:
        memory.importance = memory_update.importance
    if memory_update.source is not None:
        memory.source = memory_update.source
    
    await db.commit()
    await db.refresh(memory)
    
    if memory_update.content is not None:
        asyncio.create_task(index_long_term_memory_embedding(memory.id))
    
    return memory


@router.delete("/memory/long-term/{memory_id}")
async def delete_long_term_memory(
    memory_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    删除长期记忆
    """
    memory = await db.get(LongTermMemory, memory_id)
    
    if not memory:
        raise HTTPException(status_code=404, detail="长期记忆不存在")
    
    await db.delete(memory)
    await db.commit()
    
    logger.info(f"长期记忆已删除: {memory_id}")
    
    return {"message": "长期记忆已删除"}
