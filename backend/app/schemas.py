from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ConversationBase(BaseModel):
    title: str


class ConversationCreate(ConversationBase):
    pass


class ConversationResponse(ConversationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageBase(BaseModel):
    role: str
    content: str


class MessageResponse(MessageBase):
    id: int
    conversation_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    conversation_id: Optional[int] = None
    message: str


class ConfigBase(BaseModel):
    key: str
    value: str
    description: Optional[str] = None


class ConfigCreate(ConfigBase):
    pass


class ConfigUpdate(BaseModel):
    value: str
    description: Optional[str] = None


class ConfigResponse(ConfigBase):
    id: int
    updated_at: datetime

    class Config:
        from_attributes = True