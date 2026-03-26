import axios from 'axios';
import type { ChatRequest, Conversation, Message, Provider, Model, ConfigItem } from '../types';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

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

export const getConversations = async (): Promise<Conversation[]> => {
  const response = await api.get<Conversation[]>('/conversations');
  return response.data;
};

export const createConversation = async (title: string): Promise<Conversation> => {
  const response = await api.post<Conversation>('/conversations', { title });
  return response.data;
};

export const deleteConversation = async (id: number): Promise<void> => {
  await api.delete(`/conversations/${id}`);
};

export const getMessages = async (conversationId: number): Promise<Message[]> => {
  const response = await api.get<Message[]>(`/conversations/${conversationId}/messages`);
  return response.data;
};

export const getProviders = async (): Promise<Provider[]> => {
  const response = await api.get<Provider[]>('/config/providers');
  return response.data;
};

export const getProviderModels = async (provider: string): Promise<Model[]> => {
  const response = await api.get<Model[]>(`/config/providers/${provider}/models`);
  return response.data;
};

export const getConfig = async (key: string): Promise<string> => {
  const response = await api.get<string>(`/config/${key}`);
  return response.data;
};

export const setConfig = async (key: string, value: string): Promise<ConfigItem> => {
  const response = await api.put<ConfigItem>(`/config/${key}`, { value });
  return response.data;
};

export const getAllConfigs = async (): Promise<ConfigItem[]> => {
  const response = await api.get<ConfigItem[]>('/config');
  return response.data;
};