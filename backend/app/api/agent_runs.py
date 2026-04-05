from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.models import AgentEvent, AgentRun

router = APIRouter()


@router.get("/agent-runs/{run_id}")
async def get_agent_run(run_id: str, db: AsyncSession = Depends(get_db)):
    """通过 run_id 查找关联的 conversation_id 和 message_id。"""
    result = await db.execute(select(AgentRun).where(AgentRun.run_id == run_id))
    agent_run = result.scalar_one_or_none()
    if not agent_run:
        raise HTTPException(status_code=404, detail="agent run not found")

    # 查找该 run 下有 message_id 的 agent_events，取最后一条对应的 assistant message
    evt_result = await db.execute(
        select(AgentEvent.message_id)
        .where(AgentEvent.run_id == run_id, AgentEvent.message_id.is_not(None))
        .order_by(AgentEvent.sequence.desc())
        .limit(1)
    )
    message_id = evt_result.scalar_one_or_none()

    return {
        "conversation_id": agent_run.conversation_id,
        "message_id": message_id,
    }
