from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# 会话相关Schema
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

# 消息相关Schema
class MessageBase(BaseModel):
    role: str
    content: str

class MessageCreate(MessageBase):
    conversation_id: int

class MessageResponse(MessageBase):
    id: int
    conversation_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# 聊天请求Schema
class ChatRequest(BaseModel):
    conversation_id: Optional[int] = None
    message: str
    api_key: str

# 聊天响应Schema
class ChatResponse(BaseModel):
    message: MessageResponse
    conversation_id: int
