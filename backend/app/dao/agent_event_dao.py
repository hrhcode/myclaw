import logging
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import AgentEvent

logger = logging.getLogger(__name__)


class AgentEventDAO:
    @staticmethod
    async def create(
        db: AsyncSession,
        conversation_id: int,
        run_id: str,
        event_type: str,
        payload: str,
        sequence: int,
        message_id: Optional[int] = None,
    ) -> AgentEvent:
        agent_event = AgentEvent(
            conversation_id=conversation_id,
            message_id=message_id,
            run_id=run_id,
            event_type=event_type,
            payload=payload,
            sequence=sequence,
        )
        db.add(agent_event)
        await db.commit()
        await db.refresh(agent_event)
        return agent_event

    @staticmethod
    async def list_by_message(db: AsyncSession, message_id: int) -> List[AgentEvent]:
        result = await db.execute(
            select(AgentEvent)
            .where(AgentEvent.message_id == message_id)
            .order_by(AgentEvent.sequence, AgentEvent.created_at)
        )
        return list(result.scalars().all())

    @staticmethod
    async def list_by_run_id(db: AsyncSession, run_id: str) -> List[AgentEvent]:
        result = await db.execute(
            select(AgentEvent)
            .where(AgentEvent.run_id == run_id)
            .order_by(AgentEvent.sequence, AgentEvent.created_at)
        )
        return list(result.scalars().all())

    @staticmethod
    async def update_message_id_by_run_id(
        db: AsyncSession,
        run_id: str,
        message_id: int,
    ) -> int:
        events = await AgentEventDAO.list_by_run_id(db, run_id)
        if not events:
            return 0

        for event in events:
            event.message_id = message_id

        await db.commit()
        return len(events)
