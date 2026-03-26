// 消息角色类型
export type MessageRole = 'user' | 'assistant';

// 消息接口
export interface Message {
  id: number;
  conversation_id: number;
  role: MessageRole;
  content: string;
  created_at: string;
}

// 会话接口
export interface Conversation {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
}

// 聊天请求参数
export interface ChatRequest {
  conversation_id?: number;
  message: string;
  api_key: string;
}

// 聊天响应类型
export interface ChatResponse {
  message: Message;
  conversation_id: number;
}

// 流式聊天响应
export interface StreamChatChunk {
  content: string;
  done: boolean;
}
