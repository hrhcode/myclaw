import axios from 'axios';
import type { ChatRequest, ChatResponse, Conversation, Message } from '../types';

const API_BASE_URL = 'http://localhost:8000/api';

// 创建axios实例
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 发送聊天消息（非流式）
export const sendMessage = async (data: ChatRequest): Promise<ChatResponse> => {
  const response = await api.post<ChatResponse>('/chat', data);
  return response.data;
};

// 发送聊天消息（流式）
export const sendMessageStream = async (
  data: ChatRequest,
  onChunk: (content: string) => void,
  onComplete: (message: Message, conversationId: number) => void,
  onError: (error: Error) => void
) => {
  try {
    const response = await fetch(`${API_BASE_URL}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('Response body is not readable');
    }

    const decoder = new TextDecoder();
    let fullContent = '';
    let conversationId = data.conversation_id || 0;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data === '[DONE]') {
            onComplete(
              {
                id: Date.now(),
                conversation_id: conversationId,
                role: 'assistant',
                content: fullContent,
                created_at: new Date().toISOString(),
              },
              conversationId
            );
            return;
          }

          try {
            const parsed = JSON.parse(data);
            if (parsed.content) {
              fullContent += parsed.content;
              onChunk(parsed.content);
            }
            if (parsed.conversation_id) {
              conversationId = parsed.conversation_id;
            }
          } catch (e) {
            console.error('Failed to parse chunk:', e);
          }
        }
      }
    }
  } catch (error) {
    onError(error as Error);
  }
};

// 获取会话列表
export const getConversations = async (): Promise<Conversation[]> => {
  const response = await api.get<Conversation[]>('/conversations');
  return response.data;
};

// 创建新会话
export const createConversation = async (title: string): Promise<Conversation> => {
  const response = await api.post<Conversation>('/conversations', { title });
  return response.data;
};

// 删除会话
export const deleteConversation = async (id: number): Promise<void> => {
  await api.delete(`/conversations/${id}`);
};

// 获取会话消息
export const getMessages = async (conversationId: number): Promise<Message[]> => {
  const response = await api.get<Message[]>(`/conversations/${conversationId}/messages`);
  return response.data;
};
