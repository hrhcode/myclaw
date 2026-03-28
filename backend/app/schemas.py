from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class ConversationBase(BaseModel):
    title: str


class ConversationCreate(ConversationBase):
    pass


class ConversationUpdate(BaseModel):
    title: str


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
    use_hybrid: bool = True
    vector_weight: float = 0.7
    text_weight: float = 0.3
    enable_mmr: bool = True
    mmr_lambda: float = 0.7
    enable_temporal_decay: bool = True


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


class MemorySearchConfig(BaseModel):
    use_hybrid: bool = True
    vector_weight: float = 0.7
    text_weight: float = 0.3
    enable_mmr: bool = True
    mmr_lambda: float = 0.7
    enable_temporal_decay: bool = True
    half_life_days: int = 30


class EmbeddingConfig(BaseModel):
    provider: str = "openrouter"
    model: str = "nvidia/llama-nemotron-embed-vl-1b-v2:free"
    fallback: Optional[str] = None
    cache_enabled: bool = True
    cache_max_entries: int = 50000


class MemorySearchResultExtended(BaseModel):
    message_id: Optional[int] = None
    memory_id: Optional[int] = None
    content: str
    score: float
    source: str
    created_at: Optional[datetime] = None
    search_mode: Optional[str] = None

    class Config:
        from_attributes = True


class MemorySearchResponseExtended(BaseModel):
    results: List[MemorySearchResultExtended]
    search_mode: str
    provider: Optional[str] = None
    model: Optional[str] = None