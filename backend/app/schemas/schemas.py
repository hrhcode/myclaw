from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class ConversationBase(BaseModel):
    title: str


class ConversationCreate(ConversationBase):
    session_id: Optional[int] = None


class ConversationUpdate(BaseModel):
    title: str


class ConversationResponse(ConversationBase):
    id: int
    session_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageBase(BaseModel):
    role: str
    content: str


class ToolCallInMessage(BaseModel):
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
    session_id: Optional[int] = None
    conversation_id: int
    created_at: datetime
    tool_calls: List[ToolCallInMessage] = []
    agent_events: List[AgentEventInMessage] = []

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    session_id: Optional[int] = None
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
    half_life_days: int = 30


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
    session_id: Optional[int] = None
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
    session_id: Optional[int] = None
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
    tool_name: str
    tool_call_id: str
    arguments: str


class ToolCallCreate(ToolCallBase):
    pass


class ToolCallResponse(ToolCallBase):
    id: int
    session_id: Optional[int] = None
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
    profile: Optional[str] = "full"
    allow: Optional[List[str]] = None
    deny: Optional[List[str]] = None
    max_iterations: Optional[int] = 5
    timeout_seconds: Optional[int] = 30


class ToolConfigResponse(BaseModel):
    profile: str
    allow: List[str]
    deny: List[str]
    max_iterations: int
    timeout_seconds: int


class ToolInfo(BaseModel):
    name: str
    description: str
    enabled: bool
    parameters: dict


class ToolListResponse(BaseModel):
    tools: List[ToolInfo]
    total: int


class WebSearchConfig(BaseModel):
    provider: str = "tavily"
    tavily_api_key: Optional[str] = None
    max_results: int = 5
    search_depth: str = "basic"
    include_answer: bool = True
    timeout_seconds: int = 30
    cache_ttl_minutes: int = 15


class WebSearchConfigResponse(BaseModel):
    provider: str
    tavily_api_key: Optional[str] = None
    max_results: int
    search_depth: str
    include_answer: bool
    timeout_seconds: int
    cache_ttl_minutes: int


class BrowserConfig(BaseModel):
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


class SessionBase(BaseModel):
    name: str
    mode: str = "personal"
    workspace_path: Optional[str] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    tool_profile: str = "full"
    tool_allow: List[str] = []
    tool_deny: List[str] = []
    max_iterations: int = 5
    context_summary: str = ""
    memory_auto_extract: bool = False
    memory_threshold: int = 8
    is_default: bool = False


class SessionCreate(SessionBase):
    pass


class SessionUpdate(BaseModel):
    name: Optional[str] = None
    mode: Optional[str] = None
    workspace_path: Optional[str] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    tool_profile: Optional[str] = None
    tool_allow: Optional[List[str]] = None
    tool_deny: Optional[List[str]] = None
    max_iterations: Optional[int] = None
    context_summary: Optional[str] = None
    memory_auto_extract: Optional[bool] = None
    memory_threshold: Optional[int] = None
    is_default: Optional[bool] = None


class SessionResponse(SessionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgentRunSummary(BaseModel):
    run_id: str
    conversation_id: int
    user_message: str
    stop_reason: Optional[str] = None
    compacted_summary: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class SessionStatusResponse(BaseModel):
    id: int
    name: str
    mode: str
    workspace_path: Optional[str] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    tool_profile: str
    tool_allow: List[str] = []
    tool_deny: List[str] = []
    max_iterations: int
    context_summary: str = ""
    memory_auto_extract: bool = False
    memory_threshold: int = 8
    is_default: bool = False
    recent_runs: List[AgentRunSummary] = []


class SessionDispatchRequest(BaseModel):
    message: str


class SessionHistorySummaryResponse(BaseModel):
    session_id: int
    summary: str
    recent_messages: List[str] = []


class SkillResponse(BaseModel):
    name: str
    path: str
    description: str = ""


class SessionSkillItem(BaseModel):
    skill_name: str
    skill_path: str
    enabled: bool = True


class SessionSkillUpdateRequest(BaseModel):
    skills: List[SessionSkillItem]


class AutomationBase(BaseModel):
    name: str
    session_id: int
    prompt: str
    schedule_type: str
    schedule_value: str
    enabled: bool = True


class AutomationCreate(AutomationBase):
    pass


class AutomationUpdate(BaseModel):
    name: Optional[str] = None
    session_id: Optional[int] = None
    prompt: Optional[str] = None
    schedule_type: Optional[str] = None
    schedule_value: Optional[str] = None
    enabled: Optional[bool] = None


class AutomationResponse(AutomationBase):
    id: int
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AutomationRunResponse(BaseModel):
    id: int
    automation_id: int
    session_id: int
    status: str
    triggered_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    run_id: Optional[str] = None

    class Config:
        from_attributes = True
