from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


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


class MemorySearchRequest(BaseModel):
    query: str
    conversation_id: Optional[int] = None
    top_k: int = 5
    min_score: float = 0.5


class MemorySearchResult(BaseModel):
    message_id: Optional[int] = None
    memory_id: Optional[int] = None
    content: str
    score: float
    source: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MemorySearchResponse(BaseModel):
    results: List[MemorySearchResult]


class LongTermMemoryBase(BaseModel):
    key: Optional[str] = None
    content: str
    importance: float = 0.5
    source: Optional[str] = None


class LongTermMemoryCreate(LongTermMemoryBase):
    pass


class LongTermMemoryUpdate(BaseModel):
    key: Optional[str] = None
    content: Optional[str] = None
    importance: Optional[float] = None
    source: Optional[str] = None


class LongTermMemoryResponse(LongTermMemoryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True