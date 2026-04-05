from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.config import get_config_value, set_config_value
from app.common.constants import GLOBAL_RULE_KEY
from app.core.database import get_db
from app.dao.conversation_dao import ConversationDAO
from app.schemas.schemas import (
    ConversationRuleResponse,
    ConversationRuleUpdate,
    GlobalRuleResponse,
    GlobalRuleUpdate,
)

router = APIRouter()

GLOBAL_RULE_KEY = "global_rule"


@router.get("/rules/global", response_model=GlobalRuleResponse)
async def get_global_rule(db: AsyncSession = Depends(get_db)):
    return GlobalRuleResponse(rule=await get_config_value(db, GLOBAL_RULE_KEY) or "")


@router.put("/rules/global", response_model=GlobalRuleResponse)
async def update_global_rule(payload: GlobalRuleUpdate, db: AsyncSession = Depends(get_db)):
    await set_config_value(db, GLOBAL_RULE_KEY, payload.rule.strip(), "Global mandatory rule")
    return GlobalRuleResponse(rule=payload.rule.strip())


@router.get("/rules/conversations/{conversation_id}", response_model=ConversationRuleResponse)
async def get_conversation_rule(conversation_id: int, db: AsyncSession = Depends(get_db)):
    conversation = await ConversationDAO.get_by_id(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="conversation not found")
    return ConversationRuleResponse(
        conversation_id=conversation.id,
        title=conversation.title,
        rule=conversation.rule or "",
    )


@router.put("/rules/conversations/{conversation_id}", response_model=ConversationRuleResponse)
async def update_conversation_rule(
    conversation_id: int,
    payload: ConversationRuleUpdate,
    db: AsyncSession = Depends(get_db),
):
    conversation = await ConversationDAO.update_rule(db, conversation_id, payload.rule.strip() or None)
    if not conversation:
        raise HTTPException(status_code=404, detail="conversation not found")
    return ConversationRuleResponse(
        conversation_id=conversation.id,
        title=conversation.title,
        rule=conversation.rule or "",
    )
