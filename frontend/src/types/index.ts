export type MessageRole = 'user' | 'assistant';

export interface ToolCallInfo {
  toolName: string;
  toolCallId: string;
  arguments: string;
}

export interface ToolResultInfo {
  toolCallId: string;
  content: string;
}

export interface Message {
  id: number;
  conversation_id: number;
  role: MessageRole;
  content: string;
  created_at: string;
  toolCalls?: ToolCallInfo[];
  toolResults?: Map<string, ToolResultInfo>;
}

export interface Conversation {
  id: number;
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
  content: string;
  score: number;
  source: string;
  created_at: string | null;
}

export interface LongTermMemory {
  id: number;
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

export interface ToolCallInfo {
  tool_name: string;
  tool_call_id: string;
  arguments: string;
}

export interface ToolResultInfo {
  tool_call_id: string;
  content: string;
}