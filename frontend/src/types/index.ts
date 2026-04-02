export type MessageRole = 'user' | 'assistant';

export type AgentTraceEventType =
  | 'reasoning'
  | 'tool_call'
  | 'tool_result'
  | 'progress_warning'
  | 'loop_warning';

export interface AgentTraceEventPayload {
  content?: string;
  tool_name?: string;
  tool_call_id?: string;
  arguments?: string;
  phase?: string;
  severity?: string;
  message?: string;
  pattern?: string;
  count?: number;
  stalled_iterations?: number;
  iteration?: number;
  conversation_id?: number;
  session_id?: number;
  run_id?: string;
}

export interface AgentTraceEvent {
  id: string;
  type: AgentTraceEventType;
  createdAt?: string;
  payload: AgentTraceEventPayload;
}

export interface ToolCallFromDB {
  id: number;
  session_id?: number | null;
  tool_name: string;
  tool_call_id: string;
  arguments: string;
  result: string | null;
  status: string;
  error: string | null;
  execution_time_ms: number | null;
  created_at: string;
  completed_at: string | null;
}

export interface AgentEventFromDB {
  id: number;
  run_id: string;
  event_type: AgentTraceEventType;
  payload: string;
  sequence: number;
  created_at: string;
}

export interface Message {
  id: number;
  session_id?: number | null;
  conversation_id: number;
  role: MessageRole;
  content: string;
  created_at: string;
  tool_calls?: ToolCallFromDB[];
  agent_events?: AgentEventFromDB[];
  traceEvents?: AgentTraceEvent[];
  isStreaming?: boolean;
  runId?: string;
}

export interface Conversation {
  id: number;
  session_id?: number | null;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ConversationDetail extends Conversation {
  message_count: number;
  last_message?: {
    content: string;
    role: MessageRole;
    created_at: string;
  };
}

export interface Skill {
  name: string;
  path: string;
  description: string;
}

export interface SessionSkill {
  skill_name: string;
  skill_path: string;
  enabled: boolean;
}

export interface Automation {
  id: number;
  name: string;
  session_id: number;
  prompt: string;
  schedule_type: string;
  schedule_value: string;
  enabled: boolean;
  last_run_at?: string | null;
  next_run_at?: string | null;
  created_at: string;
  updated_at: string;
}

export type AutomationPayload = {
  name: string;
  session_id?: number;
  prompt: string;
  schedule_type: string;
  schedule_value: string;
  enabled: boolean;
};

export interface AutomationRun {
  id: number;
  automation_id: number;
  session_id: number;
  status: string;
  triggered_at: string;
  completed_at?: string | null;
  error?: string | null;
  run_id?: string | null;
}

export interface ChatRequest {
  session_id?: number;
  conversation_id?: number;
  message: string;
}

export interface Provider {
  id: string;
  name: string;
}

export interface Model {
  id: string;
  name: string;
}

export interface ConfigItem {
  id: number;
  key: string;
  value: string;
  description?: string;
  updated_at: string;
}

export interface MemorySearchResult {
  message_id: number | null;
  memory_id: number | null;
  content: string;
  score: number;
  source: string;
  created_at: string | null;
}

export interface LongTermMemory {
  id: number;
  session_id?: number | null;
  key: string | null;
  content: string;
  importance: number;
  source: string | null;
  created_at: string;
  updated_at: string;
}

export interface ToolInfo {
  name: string;
  description: string;
  enabled: boolean;
  parameters: Record<string, unknown>;
}

export interface ToolListResponse {
  tools: ToolInfo[];
  total: number;
}

export interface ToolConfig {
  profile: string;
  allow: string[];
  deny: string[];
  max_iterations: number;
  timeout_seconds: number;
}
