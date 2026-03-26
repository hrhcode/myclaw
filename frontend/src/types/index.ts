export type MessageRole = 'user' | 'assistant';

export interface Message {
  id: number;
  conversation_id: number;
  role: MessageRole;
  content: string;
  created_at: string;
}

export interface Conversation {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
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