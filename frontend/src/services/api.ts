import axios from 'axios';
import type { ChatRequest, Conversation, ConversationDetail, Message, Provider, Model, ConfigItem } from '../types';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface StreamMessage {
  type: 'content' | 'reasoning' | 'tool_call' | 'tool_result' | 'error';
  content?: string;
  tool_name?: string;
  tool_call_id?: string;
  arguments?: string;
  conversation_id?: number;
  error?: string;
  status?: number;
}

export const sendMessageStream = async (
  data: ChatRequest,
  onChunk: (content: string) => void,
  onComplete: (message: Message, conversationId: number) => void,
  onError: (error: Error) => void,
  onToolCall?: (toolName: string, toolCallId: string, arguments: string) => void,
  onToolResult?: (toolCallId: string, content: string) => void,
  onReasoning?: (content: string) => void
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
            const parsed: StreamMessage = JSON.parse(data);
            
            if (parsed.type === 'content' && parsed.content) {
              fullContent += parsed.content;
              onChunk(parsed.content);
            }
            
            if (parsed.type === 'reasoning' && parsed.content && onReasoning) {
              onReasoning(parsed.content);
            }
            
            if (parsed.type === 'tool_call' && onToolCall) {
              onToolCall(
                parsed.tool_name || '',
                parsed.tool_call_id || '',
                parsed.arguments || '{}'
              );
            }
            
            if (parsed.type === 'tool_result' && onToolResult) {
              onToolResult(parsed.tool_call_id || '', parsed.content || '{}');
            }
            
            if (parsed.type === 'error') {
              onError(new Error(parsed.error || 'Unknown error'));
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

export const renameConversation = async (id: number, title: string): Promise<Conversation> => {
  const response = await api.put<Conversation>(`/conversations/${id}`, { title });
  return response.data;
};

export const getConversationDetail = async (id: number): Promise<ConversationDetail> => {
  const response = await api.get<ConversationDetail>(`/conversations/${id}/detail`);
  return response.data;
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

export const getEmbeddingProviders = async (): Promise<Provider[]> => {
  const response = await api.get<Provider[]>('/config/embedding-providers');
  return response.data;
};

export const getEmbeddingProviderModels = async (provider: string): Promise<Model[]> => {
  const response = await api.get<Model[]>(`/config/embedding-providers/${provider}/models`);
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

export interface MemorySearchResult {
  message_id: number | null;
  memory_id: number | null;
  content: string;
  score: number;
  source: string;
  created_at: string | null;
}

export interface MemorySearchResponse {
  results: MemorySearchResult[];
}

export const searchMemory = async (
  query: string,
  conversationId?: number,
  topK: number = 5,
  minScore: number = 0.5
): Promise<MemorySearchResponse> => {
  const response = await api.post<MemorySearchResponse>('/memory/search', {
    query,
    conversation_id: conversationId,
    top_k: topK,
    min_score: minScore,
  });
  return response.data;
};

export interface LongTermMemory {
  id: number;
  key: string | null;
  content: string;
  importance: number;
  source: string | null;
  created_at: string;
  updated_at: string;
}

export const getLongTermMemories = async (): Promise<LongTermMemory[]> => {
  const response = await api.get<LongTermMemory[]>('/memory/long-term');
  return response.data;
};

export const createLongTermMemory = async (
  content: string,
  key?: string,
  importance: number = 0.5,
  source?: string
): Promise<LongTermMemory> => {
  const response = await api.post<LongTermMemory>('/memory/long-term', {
    content,
    key,
    importance,
    source,
  });
  return response.data;
};

export const updateLongTermMemory = async (
  id: number,
  data: {
    key?: string;
    content?: string;
    importance?: number;
    source?: string;
  }
): Promise<LongTermMemory> => {
  const response = await api.put<LongTermMemory>(`/memory/long-term/${id}`, data);
  return response.data;
};

export const deleteLongTermMemory = async (id: number): Promise<void> => {
  await api.delete(`/memory/long-term/${id}`);
};

export const indexConversation = async (conversationId: number): Promise<{
  message: string;
  conversation_id: number;
  indexed_count: number;
}> => {
  const response = await api.post(`/memory/index/${conversationId}`);
  return response.data;
};

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

export const getTools = async (): Promise<ToolListResponse> => {
  const response = await api.get<ToolListResponse>('/tools');
  return response.data;
};

export const getToolConfig = async (): Promise<ToolConfig> => {
  const response = await api.get<ToolConfig>('/tools/config');
  return response.data;
};

export const updateToolConfig = async (config: Partial<ToolConfig>): Promise<{ success: boolean; message: string }> => {
  const response = await api.put<{ success: boolean; message: string }>('/tools/config', config);
  return response.data;
};

export const toggleTool = async (toolName: string, enabled: boolean): Promise<{ success: boolean; message: string }> => {
  const response = await api.put<{ success: boolean; message: string }>(`/tools/${toolName}/toggle`, null, {
    params: { enabled }
  });
  return response.data;
};