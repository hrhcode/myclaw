import logging
from typing import List, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dao._utils import commit_or_flush
from app.models.models import Conversation, Message, ToolCall, AgentEvent, AgentRun, Automation, AutomationRun

logger = logging.getLogger(__name__)


class ConversationDAO:
    @staticmethod
    async def create(db: AsyncSession, title: str, session_id: Optional[int] = None, *, commit: bool = True) -> Conversation:
        conversation = Conversation(title=title, session_id=session_id)
        db.add(conversation)
        await commit_or_flush(db, commit)
        await db.refresh(conversation)
        logger.info("[DAO-Conversation] created conversation id=%s", conversation.id)
        return conversation

    @staticmethod
    async def get_by_id(db: AsyncSession, conversation_id: int) -> Optional[Conversation]:
        result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def list_all(db: AsyncSession, limit: int = 50) -> List[Conversation]:
        result = await db.execute(
            select(Conversation).order_by(Conversation.updated_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def list_by_session(db: AsyncSession, session_id: int, limit: int = 100) -> List[Conversation]:
        result = await db.execute(
            select(Conversation)
            .where(Conversation.session_id == session_id)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def update_title(db: AsyncSession, conversation_id: int, title: str, *, commit: bool = True) -> Optional[Conversation]:
        conversation = await ConversationDAO.get_by_id(db, conversation_id)
        if not conversation:
            logger.warning("[DAO-Conversation] update title failed, not found id=%s", conversation_id)
            return None

        conversation.title = title
        await commit_or_flush(db, commit)
        await db.refresh(conversation)
        return conversation

    @staticmethod
    async def update_rule(
        db: AsyncSession,
        conversation_id: int,
        rule: Optional[str],
        *,
        commit: bool = True,
    ) -> Optional[Conversation]:
        conversation = await ConversationDAO.get_by_id(db, conversation_id)
        if not conversation:
            logger.warning("[DAO-Conversation] update rule failed, not found id=%s", conversation_id)
            return None

        conversation.rule = rule
        await commit_or_flush(db, commit)
        await db.refresh(conversation)
        return conversation

    @staticmethod
    async def delete(db: AsyncSession, conversation_id: int, *, commit: bool = True) -> bool:
        conversation = await ConversationDAO.get_by_id(db, conversation_id)
        if not conversation:
            logger.warning("[DAO-Conversation] delete failed, not found id=%s", conversation_id)
            return False

        await db.execute(delete(AgentEvent).where(AgentEvent.conversation_id == conversation_id))
        await db.execute(delete(AgentRun).where(AgentRun.conversation_id == conversation_id))
        await db.execute(delete(AutomationRun).where(AutomationRun.conversation_id == conversation_id))
        await db.execute(delete(Automation).where(Automation.conversation_id == conversation_id))
        await db.execute(delete(ToolCall).where(ToolCall.conversation_id == conversation_id))
        await db.execute(delete(Message).where(Message.conversation_id == conversation_id))
        await db.delete(conversation)
        await commit_or_flush(db, commit)
        return True

    @staticmethod
    async def exists(db: AsyncSession, conversation_id: int) -> bool:
        conversation = await ConversationDAO.get_by_id(db, conversation_id)
        return conversation is not None
