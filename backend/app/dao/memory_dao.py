import logging
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dao._utils import commit_or_flush
from app.models.models import LongTermMemory

logger = logging.getLogger(__name__)


class MemoryDAO:
    @staticmethod
    async def create(
        db: AsyncSession,
        content: str,
        session_id: Optional[int] = None,
        title: Optional[str] = None,
        key: Optional[str] = None,
        importance: float = 0.5,
        source: Optional[str] = None,
        content_type: str = "note",
        group_id: Optional[str] = None,
        origin_message_id: Optional[int] = None,
        *,
        commit: bool = True,
    ) -> LongTermMemory:
        memory = LongTermMemory(
            session_id=session_id,
            title=title,
            key=key,
            content=content,
            importance=importance,
            source=source,
            content_type=content_type,
            group_id=group_id,
            origin_message_id=origin_message_id,
        )
        db.add(memory)
        await commit_or_flush(db, commit)
        await db.refresh(memory)
        logger.info("[DAO-Memory] created long-term memory id=%s", memory.id)
        return memory

    @staticmethod
    async def get_by_id(db: AsyncSession, memory_id: int) -> Optional[LongTermMemory]:
        result = await db.execute(select(LongTermMemory).where(LongTermMemory.id == memory_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def list_all(db: AsyncSession, limit: int = 50) -> List[LongTermMemory]:
        result = await db.execute(
            select(LongTermMemory)
            .order_by(LongTermMemory.importance.desc(), LongTermMemory.updated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def update(
        db: AsyncSession,
        memory_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        key: Optional[str] = None,
        importance: Optional[float] = None,
        source: Optional[str] = None,
        content_type: Optional[str] = None,
        *,
        commit: bool = True,
    ) -> Optional[LongTermMemory]:
        memory = await MemoryDAO.get_by_id(db, memory_id)
        if not memory:
            logger.warning("[DAO-Memory] update failed, memory not found id=%s", memory_id)
            return None

        if title is not None:
            memory.title = title
        if content is not None:
            memory.content = content
        if key is not None:
            memory.key = key
        if importance is not None:
            memory.importance = importance
        if source is not None:
            memory.source = source
        if content_type is not None:
            memory.content_type = content_type

        await commit_or_flush(db, commit)
        await db.refresh(memory)
        return memory

    @staticmethod
    async def delete(db: AsyncSession, memory_id: int, *, commit: bool = True) -> bool:
        memory = await MemoryDAO.get_by_id(db, memory_id)
        if not memory:
            logger.warning("[DAO-Memory] delete failed, memory not found id=%s", memory_id)
            return False

        await db.delete(memory)
        await commit_or_flush(db, commit)
        return True

    @staticmethod
    async def get_by_content_hash(db: AsyncSession, content_hash: str) -> Optional[LongTermMemory]:
        result = await db.execute(
            select(LongTermMemory).where(LongTermMemory.content_hash == content_hash)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def count(db: AsyncSession) -> int:
        from sqlalchemy import func

        result = await db.execute(select(func.count(LongTermMemory.id)))
        return result.scalar() or 0

    @staticmethod
    async def list_by_importance(
        db: AsyncSession,
        min_importance: float = 0.0,
        limit: int = 50,
    ) -> List[LongTermMemory]:
        result = await db.execute(
            select(LongTermMemory)
            .where(LongTermMemory.importance >= min_importance)
            .order_by(LongTermMemory.importance.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def list_grouped(db: AsyncSession, session_id: Optional[int] = None) -> List[dict]:
        query = select(LongTermMemory).order_by(
            LongTermMemory.updated_at.desc(),
            LongTermMemory.created_at.desc(),
        )
        if session_id is not None:
            query = query.where(LongTermMemory.session_id == session_id)

        result = await db.execute(query)
        records = list(result.scalars().all())

        grouped: dict[str, dict] = {}
        singles: List[dict] = []
        for memory in records:
            title = memory.title or memory.key or f"Knowledge #{memory.id}"
            if memory.group_id:
                item = grouped.setdefault(
                    memory.group_id,
                    {
                        "id": memory.group_id,
                        "memory_id": None,
                        "session_id": memory.session_id,
                        "title": title,
                        "content_type": memory.content_type or "note",
                        "source": memory.source,
                        "item_count": 0,
                        "preview": memory.content[:280],
                        "created_at": memory.created_at,
                        "updated_at": memory.updated_at,
                    },
                )
                item["item_count"] += 1
                if memory.updated_at and memory.updated_at > item["updated_at"]:
                    item["updated_at"] = memory.updated_at
                continue

            singles.append(
                {
                    "id": str(memory.id),
                    "memory_id": memory.id,
                    "session_id": memory.session_id,
                    "title": title,
                    "content_type": memory.content_type or "note",
                    "source": memory.source,
                    "item_count": 1,
                    "preview": memory.content[:280],
                    "created_at": memory.created_at,
                    "updated_at": memory.updated_at,
                }
            )

        items = list(grouped.values()) + singles
        items.sort(key=lambda item: item["updated_at"], reverse=True)
        return items

    @staticmethod
    async def delete_group_or_item(db: AsyncSession, identifier: str, *, commit: bool = True) -> int:
        if identifier.isdigit():
            memory = await MemoryDAO.get_by_id(db, int(identifier))
            if not memory:
                return 0
            await db.delete(memory)
            await commit_or_flush(db, commit)
            return 1

        result = await db.execute(
            select(LongTermMemory).where(LongTermMemory.group_id == identifier)
        )
        records = list(result.scalars().all())
        if not records:
            return 0

        for record in records:
            await db.delete(record)
        await commit_or_flush(db, commit)
        return len(records)
