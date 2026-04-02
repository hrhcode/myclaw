from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class LoopRuntimeConfig:
    use_tools: bool = True
    max_iterations: int = 5
    timeout_seconds: int = 30
    profile: str = "full"
    allow: List[str] = field(default_factory=list)
    deny: List[str] = field(default_factory=list)


@dataclass
class ToolExecutionRecord:
    tool_name: str
    tool_call_id: str
    arguments: Dict[str, Any]
    success: bool
    result: Any
    error: Optional[str] = None
    sanitized_content: str = ""
    novelty_key: Optional[str] = None


@dataclass
class ProgressSnapshot:
    stalled_iterations: int = 0
    repeated_tool_call_count: int = 0
    last_signature: Optional[str] = None
    last_success_signature: Optional[str] = None


@dataclass
class AgentRunState:
    run_id: str
    conversation_id: int
    user_message: str
    messages: List[Dict[str, Any]]
    memory_context: str = ""
    iteration: int = 0
    final_answer: str = ""
    tool_calls_info: List[Dict[str, Any]] = field(default_factory=list)
    tool_history: List[ToolExecutionRecord] = field(default_factory=list)
    progress: ProgressSnapshot = field(default_factory=ProgressSnapshot)
    force_answer_next: bool = False
    stop_reason: Optional[str] = None
    compacted_summary: str = ""
    event_sequence: int = 0
