from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dao.memory_dao import MemoryDAO
from app.schemas.schemas import (
    LongTermMemoryCreate,
    LongTermMemoryResponse,
    LongTermMemoryUpdate,
    MemorySearchRequest,
    MemorySearchResponse,
)
from app.services.vector_search_service import (
    batch_index_conversation_messages,
    hybrid_memory_search,
    index_long_term_memory_embedding,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/memory/search", response_model=MemorySearchResponse)
async def search_memory(
    request: MemorySearchRequest,
    db: AsyncSession = Depends(get_db),
):
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
            half_life_days=request.half_life_days,
        )
        return MemorySearchResponse(results=results)
    except Exception as exc:
        logger.exception("[memory] search failed")
        raise HTTPException(status_code=500, detail=f"memory search failed: {exc}") from exc


@router.post("/memory/index/{conversation_id}")
async def index_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
):
    try:
        indexed_count = await batch_index_conversation_messages(conversation_id)
        return {
            "message": "index completed",
            "conversation_id": conversation_id,
            "indexed_count": indexed_count,
        }
    except Exception as exc:
        logger.exception("[memory] index conversation failed")
        raise HTTPException(status_code=500, detail=f"indexing failed: {exc}") from exc


@router.get("/memory/long-term", response_model=list[LongTermMemoryResponse])
async def list_long_term_memories(
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    session_id: int | None = None,
):
    memories = await MemoryDAO.list_all(db, limit)
    if session_id is not None:
        memories = [memory for memory in memories if memory.session_id == session_id]
    return memories


@router.post("/memory/long-term", response_model=LongTermMemoryResponse)
async def create_long_term_memory(
    memory_create: LongTermMemoryCreate,
    db: AsyncSession = Depends(get_db),
):
    memory = await MemoryDAO.create(
        db=db,
        session_id=getattr(memory_create, "session_id", None),
        content=memory_create.content,
        key=memory_create.key,
        importance=memory_create.importance,
        source=memory_create.source,
    )
    asyncio.create_task(index_long_term_memory_embedding(memory.id))
    return memory


@router.get("/memory/long-term/{memory_id}", response_model=LongTermMemoryResponse)
async def get_long_term_memory(
    memory_id: int,
    db: AsyncSession = Depends(get_db),
):
    memory = await MemoryDAO.get_by_id(db, memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="memory not found")
    return memory


@router.put("/memory/long-term/{memory_id}", response_model=LongTermMemoryResponse)
async def update_long_term_memory(
    memory_id: int,
    memory_update: LongTermMemoryUpdate,
    db: AsyncSession = Depends(get_db),
):
    existing = await MemoryDAO.get_by_id(db, memory_id)
    if not existing:
        raise HTTPException(status_code=404, detail="memory not found")

    memory = await MemoryDAO.update(
        db=db,
        memory_id=memory_id,
        content=memory_update.content,
        key=memory_update.key,
        importance=memory_update.importance,
        source=memory_update.source,
    )

    if memory_update.content is not None:
        asyncio.create_task(index_long_term_memory_embedding(memory.id))
    return memory


@router.delete("/memory/long-term/{memory_id}")
async def delete_long_term_memory(
    memory_id: int,
    db: AsyncSession = Depends(get_db),
):
    deleted = await MemoryDAO.delete(db, memory_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="memory not found")
    return {"message": "memory deleted"}
