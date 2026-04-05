export type MessageRole = 'user' | 'assistant';

export type AgentTraceEventType =
  | 'reasoning'
  | 'tool_call'
  | 'tool_result'
  | 'knowledge_hits'
  | 'progress_warning'
  | 'loop_warning';

export interface KnowledgeHit {
  memory_id?: number | null;
  title?: string | null;
  content: string;
  content_type?: string | null;
  score: number;
  source: string;
  created_at?: string | null;
}

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
  hits?: KnowledgeHit[];
  conversation_id?: number;
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
  title: string;
  rule?: string;
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

export interface GlobalRuleResponse {
  rule: string;
}

export interface ConversationRuleResponse {
  conversation_id: number;
  title: string;
  rule: string;
}

export interface Skill {
  name: string;
  path: string;
  description: string;
}

export interface SessionSummary {
  id: number;
  name: string;
  mode: string;
  is_default: boolean;
}

export interface SessionSkill {
  skill_name: string;
  skill_path: string;
  enabled: boolean;
}

export interface Automation {
  id: number;
  name: string;
  conversation_id: number;
  prompt: string;
  schedule_type: string;
  schedule_value: string;
  timezone: string;
  enabled: boolean;
  last_run_at?: string | null;
  next_run_at?: string | null;
  created_at: string;
  updated_at: string;
}

export type AutomationPayload = {
  name: string;
  conversation_id?: number;
  prompt: string;
  schedule_type: string;
  schedule_value: string;
  timezone: string;
  enabled: boolean;
};

export interface AutomationRun {
  id: number;
  automation_id: number;
  status: string;
  trigger_mode: string;
  triggered_at: string;
  completed_at?: string | null;
  error?: string | null;
  run_id?: string | null;
  automation_name?: string | null;
  conversation_id?: number | null;
  response_snippet?: string | null;
}

export interface AutomationStats {
  total: number;
  enabled: number;
  disabled: number;
  due_now: number;
  running: number;
  failed_recently: number;
  next_run_at?: string | null;
  last_run_at?: string | null;
}

export interface ChatRequest {
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
  title?: string | null;
  content: string;
  content_type?: string | null;
  score: number;
  source: string;
  created_at: string | null;
}

export interface LongTermMemory {
  id: number;
  title?: string | null;
  key: string | null;
  content: string;
  content_type?: string;
  group_id?: string | null;
  origin_message_id?: number | null;
  importance: number;
  source: string | null;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeBaseItem {
  id: string;
  memory_id?: number | null;
  title: string;
  content_type: string;
  source?: string | null;
  item_count: number;
  preview: string;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeBaseStats {
  total_items: number;
  markdown_groups: number;
  assistant_replies: number;
}

export interface KnowledgeBaseListResponse {
  items: KnowledgeBaseItem[];
  stats: KnowledgeBaseStats;
}

export interface ToolInfo {
  name: string;
  description: string;
  enabled: boolean;
  parameters: Record<string, unknown>;
  source: string;
  mcp_server_name?: string | null;
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

export interface McpServerEvent {
  id: string;
  level: 'info' | 'warning' | 'success';
  message: string;
  time: string;
}

export interface McpServer {
  id: string;
  name: string;
  description: string;
  transport: 'stdio' | 'http' | 'sse';
  command?: string | null;
  args: string[];
  endpoint?: string | null;
  enabled: boolean;
  tags: string[];
  workspaces: string[];
  env: Record<string, string>;
  headers: Record<string, string>;
  timeout_seconds: number;
  status: 'connected' | 'degraded' | 'disabled';
  resources: number;
  tools: number;
  prompts: number;
  alerts: number;
  capabilities: string[];
  tool_names: string[];
  resource_names: string[];
  prompt_names: string[];
  status_reason?: string | null;
  last_probe_at?: string | null;
  updated_at?: string | null;
  events: McpServerEvent[];
}

export interface McpServerPayload {
  name: string;
  description: string;
  transport: 'stdio' | 'http' | 'sse';
  command?: string | null;
  args: string[];
  endpoint?: string | null;
  enabled: boolean;
  tags: string[];
  workspaces: string[];
  env: Record<string, string>;
  headers: Record<string, string>;
  timeout_seconds: number;
}

export interface McpStats {
  total: number;
  enabled: number;
  resources: number;
  alerts: number;
}

export interface McpImportResult {
  servers: McpServer[];
  errors: string[];
  created_count: number;
  skipped_count: number;
}

export interface Channel {
  id: number;
  name: string;
  channel_type: string;
  enabled: boolean;
  config: Record<string, unknown>;
  conversation_id: number | null;
  status: string;
  status_message: string | null;
  last_event_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ChannelCreatePayload {
  name: string;
  channel_type: string;
  enabled: boolean;
  config: Record<string, unknown>;
  conversation_id?: number | null;
}

export interface ChannelUpdatePayload {
  name?: string;
  enabled?: boolean;
  config?: Record<string, unknown>;
  conversation_id?: number | null;
}

export interface ChannelChat {
  id: number;
  channel_id: number;
  external_chat_id: string;
  external_chat_type: string;
  conversation_id: number | null;
  external_user_id: string | null;
  external_user_name: string | null;
  last_message_at: string | null;
  created_at: string;
}
