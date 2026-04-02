from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.utils.text import chunk_markdown_text
from app.core.database import get_db
from app.dao.memory_dao import MemoryDAO
from app.dao.message_dao import MessageDAO
from app.schemas.schemas import (
    KnowledgeBaseItemResponse,
    KnowledgeBaseListResponse,
    KnowledgeBaseStatsResponse,
    KnowledgeFromMessageCreate,
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


def _build_stats(items: list[dict]) -> KnowledgeBaseStatsResponse:
    markdown_groups = sum(1 for item in items if item["content_type"] == "markdown")
    assistant_replies = sum(
        item["item_count"] for item in items if item["content_type"] == "assistant_reply"
    )
    total_items = sum(item["item_count"] for item in items)
    return KnowledgeBaseStatsResponse(
        total_items=total_items,
        markdown_groups=markdown_groups,
        assistant_replies=assistant_replies,
    )


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
        title=memory_create.title,
        content=memory_create.content,
        key=memory_create.key,
        importance=memory_create.importance,
        source=memory_create.source,
        content_type=memory_create.content_type,
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
        title=memory_update.title,
        content=memory_update.content,
        key=memory_update.key,
        importance=memory_update.importance,
        source=memory_update.source,
        content_type=memory_update.content_type,
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


@router.get("/knowledge", response_model=KnowledgeBaseListResponse)
async def list_knowledge_base(
    db: AsyncSession = Depends(get_db),
    session_id: int | None = None,
):
    items = await MemoryDAO.list_grouped(db, session_id=session_id)
    return KnowledgeBaseListResponse(
        items=[KnowledgeBaseItemResponse(**item) for item in items],
        stats=_build_stats(items),
    )


@router.post("/knowledge/markdown")
async def upload_markdown_knowledge(
    file: UploadFile = File(...),
    session_id: int | None = Form(default=None),
    title: str | None = Form(default=None),
    source: str | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
):
    filename = file.filename or "document.md"
    suffix = Path(filename).suffix.lower()
    if suffix not in {".md", ".markdown"}:
        raise HTTPException(status_code=400, detail="only markdown files are supported")

    raw = await file.read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("utf-8", errors="ignore")

    chunks = chunk_markdown_text(text)
    if not chunks:
        raise HTTPException(status_code=400, detail="markdown file is empty")

    group_id = f"kb-{uuid4().hex}"
    display_title = (title or Path(filename).stem or filename).strip()
    created_ids: list[int] = []
    for chunk_index, chunk in enumerate(chunks, start=1):
        memory = await MemoryDAO.create(
            db=db,
            session_id=session_id,
            title=display_title,
            key=f"{display_title}#{chunk_index}",
            content=chunk,
            importance=0.7,
            source=source or f"markdown:{filename}",
            content_type="markdown",
            group_id=group_id,
        )
        created_ids.append(memory.id)
        asyncio.create_task(index_long_term_memory_embedding(memory.id))

    return {
        "message": "markdown uploaded",
        "group_id": group_id,
        "title": display_title,
        "chunk_count": len(created_ids),
        "item_ids": created_ids,
    }


@router.post("/knowledge/from-message", response_model=LongTermMemoryResponse)
async def save_message_to_knowledge(
    payload: KnowledgeFromMessageCreate,
    db: AsyncSession = Depends(get_db),
):
    message = await MessageDAO.get_by_id(db, payload.message_id)
    if not message:
        raise HTTPException(status_code=404, detail="message not found")
    if message.role != "assistant":
        raise HTTPException(status_code=400, detail="only assistant messages can be saved")

    title = (payload.title or message.content.splitlines()[0][:60] or "Saved reply").strip()
    memory = await MemoryDAO.create(
        db=db,
        session_id=payload.session_id or message.session_id,
        title=title,
        key=title,
        content=message.content,
        importance=0.8,
        source=payload.source or f"assistant_reply:conversation:{message.conversation_id}",
        content_type="assistant_reply",
        origin_message_id=message.id,
    )
    asyncio.create_task(index_long_term_memory_embedding(memory.id))
    return memory


@router.delete("/knowledge/{identifier}")
async def delete_knowledge(
    identifier: str,
    db: AsyncSession = Depends(get_db),
):
    deleted_count = await MemoryDAO.delete_group_or_item(db, identifier)
    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="knowledge item not found")
    return {"message": "knowledge deleted", "deleted_count": deleted_count}
