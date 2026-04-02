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


class ToolCallInMessage(BaseModel):
    """
    消息中嵌套的工具调用信息
    用于在消息响应中返回关联的工具调用记录
    """
    id: int
    tool_name: str
    tool_call_id: str
    arguments: str
    result: Optional[str] = None
    status: str
    error: Optional[str] = None
    execution_time_ms: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AgentEventInMessage(BaseModel):
    id: int
    run_id: str
    event_type: str
    payload: str
    sequence: int
    created_at: datetime

    class Config:
        from_attributes = True


class MessageResponse(MessageBase):
    id: int
    conversation_id: int
    created_at: datetime
    tool_calls: List[ToolCallInMessage] = []
    agent_events: List[AgentEventInMessage] = []

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


 

 
class ToolCallBase(BaseModel):
    """工具调用基础 Schema"""
    tool_name: str
    tool_call_id: str
    arguments: str


class ToolCallCreate(ToolCallBase):
    """创建工具调用"""
    pass


class ToolCallResponse(ToolCallBase):
    """工具调用响应"""
    id: int
    message_id: Optional[int] = None
    conversation_id: int
    result: Optional[str] = None
    status: str
    error: Optional[str] = None
    execution_time_ms: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ToolConfigRequest(BaseModel):
    """工具配置请求"""
    profile: Optional[str] = "full"
    allow: Optional[List[str]] = None
    deny: Optional[List[str]] = None
    max_iterations: Optional[int] = 5
    timeout_seconds: Optional[int] = 30


class ToolConfigResponse(BaseModel):
    """工具配置响应"""
    profile: str
    allow: List[str]
    deny: List[str]
    max_iterations: int
    timeout_seconds: int


class ToolInfo(BaseModel):
    """工具信息"""
    name: str
    description: str
    enabled: bool
    parameters: dict


class ToolListResponse(BaseModel):
    """工具列表响应"""
    tools: List[ToolInfo]
    total: int


class WebSearchConfig(BaseModel):
    """网络搜索配置"""
    provider: str = "tavily"
    tavily_api_key: Optional[str] = None
    max_results: int = 5
    search_depth: str = "basic"
    include_answer: bool = True
    timeout_seconds: int = 30
    cache_ttl_minutes: int = 15


class WebSearchConfigResponse(BaseModel):
    """网络搜索配置响应"""
    provider: str
    tavily_api_key: Optional[str] = None
    max_results: int
    search_depth: str
    include_answer: bool
    timeout_seconds: int
    cache_ttl_minutes: int


class BrowserConfig(BaseModel):
    """浏览器配置"""
    default_type: str = "chromium"
    headless: bool = False
    viewport_width: int = 1280
    viewport_height: int = 720
    timeout_ms: int = 30000
    ssrf_allow_private: bool = False
    ssrf_whitelist: str = ""
    max_instances: int = 1
    idle_timeout_ms: int = 300000
    use_system_browser: bool = True
    system_browser_channel: str = "chrome"


class BrowserConfigResponse(BaseModel):
    """浏览器配置响应"""
    default_type: str
    headless: bool
    viewport_width: int
    viewport_height: int
    timeout_ms: int
    ssrf_allow_private: bool
    ssrf_whitelist: str
    max_instances: int
    idle_timeout_ms: int
    use_system_browser: bool
    system_browser_channel: str
