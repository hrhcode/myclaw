import axios from 'axios';
import type {
  AgentTraceEventPayload,
  AgentTraceEventType,
  Automation,
  AutomationPayload,
  AutomationRun,
  AutomationStats,
  Channel,
  ChannelChat,
  ChannelCreatePayload,
  ChannelUpdatePayload,
  ChatRequest,
  ConfigItem,
  ConversationRuleResponse,
  Conversation,
  ConversationDetail,
  GlobalRuleResponse,
  KnowledgeBaseListResponse,
  LongTermMemory,
  MemorySearchResult,
  Message,
  Model,
  Provider,
  SessionSkill,
  Skill,
  ToolConfig,
  ToolInfo,
  ToolListResponse,
  McpServer,
  McpServerPayload,
  McpStats,
  McpImportResult,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

const getApiToken = (): string | null => {
  try {
    const token = localStorage.getItem('myclaw_api_token');
    if (!token) {
      return null;
    }
    const trimmed = token.trim();
    return trimmed.length > 0 ? trimmed : null;
  } catch {
    return null;
  }
};

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = getApiToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface StreamMessage {
  type:
    | 'conversation'
    | 'content'
    | 'reasoning'
    | 'tool_call'
    | 'tool_result'
    | 'knowledge_hits'
    | 'progress_warning'
    | 'loop_warning'
    | 'done'
    | 'error';
  content?: string;
  tool_name?: string;
  tool_call_id?: string;
  arguments?: string;
  phase?: string;
  conversation_id?: number;
  run_id?: string;
  severity?: string;
  message?: string;
  pattern?: string;
  count?: number;
  stalled_iterations?: number;
  iteration?: number;
  hits?: AgentTraceEventPayload['hits'];
  error?: string;
  status?: number;
}

interface SendMessageStreamCallbacks {
  onChunk: (content: string) => void;
  onComplete: (message: Message, conversationId: number) => void;
  onError: (error: Error) => void;
  onConversation?: (conversationId: number, runId?: string) => void;
  onTraceEvent?: (type: AgentTraceEventType, payload: AgentTraceEventPayload) => void;
}

export interface ConversationStats {
  conversation_id: number;
  message_count: number;
  last_message_id: number | null;
  last_message_content: string | null;
  last_message_created_at: string | null;
}

const parseEventPayload = (message: StreamMessage): AgentTraceEventPayload => ({
  content: message.content,
  tool_name: message.tool_name,
  tool_call_id: message.tool_call_id,
  arguments: message.arguments,
  phase: message.phase,
  severity: message.severity,
  message: message.message,
  pattern: message.pattern,
  count: message.count,
  stalled_iterations: message.stalled_iterations,
  iteration: message.iteration,
  hits: message.hits,
  conversation_id: message.conversation_id,
  run_id: message.run_id,
});

export const sendMessageStream = async (
  data: ChatRequest,
  callbacks: SendMessageStreamCallbacks,
) => {
  const { onChunk, onComplete, onError, onConversation, onTraceEvent } = callbacks;

  try {
    const token = getApiToken();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
    const response = await fetch(`${API_BASE_URL}/chat/stream`, {
      method: 'POST',
      headers,
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
    let buffer = '';
    let runId: string | undefined;

    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const frames = buffer.split('\n\n');
      buffer = frames.pop() || '';

      for (const frame of frames) {
        const dataLines = frame
          .split('\n')
          .filter((line) => line.startsWith('data: '))
          .map((line) => line.slice(6));

        if (dataLines.length === 0) {
          continue;
        }

        const payload = dataLines.join('\n');
        if (payload === '[DONE]') {
          onComplete(
            {
              id: Date.now(),
              conversation_id: conversationId,
              role: 'assistant',
              content: fullContent,
              created_at: new Date().toISOString(),
              runId,
            },
            conversationId,
          );
          return;
        }

        try {
          const parsed: StreamMessage = JSON.parse(payload);

          if (parsed.conversation_id) {
            conversationId = parsed.conversation_id;
          }
          if (parsed.run_id) {
            runId = parsed.run_id;
          }

          if (parsed.type === 'conversation') {
            onConversation?.(conversationId, runId);
            continue;
          }

          if (parsed.type === 'content' && parsed.content) {
            fullContent += parsed.content;
            onChunk(parsed.content);
            continue;
          }

          if (
            parsed.type === 'reasoning' ||
            parsed.type === 'tool_call' ||
            parsed.type === 'tool_result' ||
            parsed.type === 'knowledge_hits' ||
            parsed.type === 'progress_warning' ||
            parsed.type === 'loop_warning'
          ) {
            onTraceEvent?.(parsed.type, parseEventPayload(parsed));
            continue;
          }

          if (parsed.type === 'error') {
            onError(new Error(parsed.error || 'Unknown error'));
          }
        } catch (error) {
          console.error('Failed to parse SSE frame:', error, payload);
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

export const getConversationStats = async (): Promise<ConversationStats[]> => {
  const response = await api.get<ConversationStats[]>('/conversations/stats');
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

export const getGlobalRule = async (): Promise<GlobalRuleResponse> => {
  const response = await api.get<GlobalRuleResponse>('/rules/global');
  return response.data;
};

export const updateGlobalRule = async (rule: string): Promise<GlobalRuleResponse> => {
  const response = await api.put<GlobalRuleResponse>('/rules/global', { rule });
  return response.data;
};

export const getConversationRule = async (conversationId: number): Promise<ConversationRuleResponse> => {
  const response = await api.get<ConversationRuleResponse>(`/rules/conversations/${conversationId}`);
  return response.data;
};

export const updateConversationRule = async (
  conversationId: number,
  rule: string,
): Promise<ConversationRuleResponse> => {
  const response = await api.put<ConversationRuleResponse>(`/rules/conversations/${conversationId}`, { rule });
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

export interface MemorySearchResponse {
  results: MemorySearchResult[];
}

export const searchMemory = async (
  query: string,
  conversationId?: number,
  topK: number = 5,
  minScore: number = 0.5,
): Promise<MemorySearchResponse> => {
  const response = await api.post<MemorySearchResponse>('/memory/search', {
    query,
    conversation_id: conversationId,
    top_k: topK,
    min_score: minScore,
  });
  return response.data;
};

export const getLongTermMemories = async (): Promise<LongTermMemory[]> => {
  const response = await api.get<LongTermMemory[]>('/memory/long-term');
  return response.data;
};

export const createLongTermMemory = async (
  content: string,
  key?: string,
  importance: number = 0.5,
  source?: string,
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
  },
): Promise<LongTermMemory> => {
  const response = await api.put<LongTermMemory>(`/memory/long-term/${id}`, data);
  return response.data;
};

export const deleteLongTermMemory = async (id: number): Promise<void> => {
  await api.delete(`/memory/long-term/${id}`);
};

export interface KnowledgeUploadResponse {
  message: string;
  group_id: string;
  title: string;
  chunk_count: number;
  item_ids: number[];
}

export const getKnowledgeBase = async (): Promise<KnowledgeBaseListResponse> => {
  const response = await api.get<KnowledgeBaseListResponse>('/knowledge');
  return response.data;
};

export const uploadMarkdownKnowledge = async (
  file: File,
  options?: { title?: string; source?: string },
): Promise<KnowledgeUploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  if (options?.title) {
    formData.append('title', options.title);
  }
  if (options?.source) {
    formData.append('source', options.source);
  }

  const response = await api.post<KnowledgeUploadResponse>('/knowledge/markdown', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const saveMessageToKnowledge = async (
  messageId: number,
  options?: { title?: string; source?: string },
): Promise<LongTermMemory> => {
  const response = await api.post<LongTermMemory>('/knowledge/from-message', {
    message_id: messageId,
    title: options?.title,
    source: options?.source,
  });
  return response.data;
};

export const deleteKnowledge = async (identifier: string): Promise<{ message: string; deleted_count: number }> => {
  const response = await api.delete<{ message: string; deleted_count: number }>(`/knowledge/${identifier}`);
  return response.data;
};

export const indexConversation = async (conversationId: number): Promise<{
  message: string;
  conversation_id: number;
  indexed_count: number;
}> => {
  const response = await api.post(`/memory/index/${conversationId}`);
  return response.data;
};

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
    params: { enabled },
  });
  return response.data;
};

export interface WebSearchConfig {
  enabled?: boolean;
  provider: string;
  tavily_api_key?: string;
  brave_api_key?: string;
  perplexity_api_key?: string;
  max_results: number;
  search_depth: 'basic' | 'advanced';
  include_answer: boolean;
  timeout_seconds: number;
  cache_ttl_minutes: number;
}

export interface WebSearchConfigResponse {
  enabled?: boolean;
  provider: string;
  tavily_api_key?: string;
  brave_api_key?: string;
  perplexity_api_key?: string;
  max_results: number;
  search_depth: string;
  include_answer: boolean;
  timeout_seconds: number;
  cache_ttl_minutes: number;
}

export const getWebSearchConfig = async (): Promise<WebSearchConfigResponse> => {
  const response = await api.get<WebSearchConfigResponse>('/config/web-search');
  return response.data;
};

export const setWebSearchConfig = async (config: WebSearchConfig): Promise<{ message: string }> => {
  const response = await api.put<{ message: string }>('/config/web-search', config);
  return response.data;
};

export interface BrowserConfig {
  default_type: string;
  headless: boolean;
  viewport_width: number;
  viewport_height: number;
  timeout_ms: number;
  ssrf_allow_private: boolean;
  ssrf_whitelist: string;
  max_instances: number;
  idle_timeout_ms: number;
  use_system_browser: boolean;
  system_browser_channel: string;
}

export interface BrowserConfigResponse {
  default_type: string;
  headless: boolean;
  viewport_width: number;
  viewport_height: number;
  timeout_ms: number;
  ssrf_allow_private: boolean;
  ssrf_whitelist: string;
  max_instances: number;
  idle_timeout_ms: number;
  use_system_browser: boolean;
  system_browser_channel: string;
}

export const getBrowserConfig = async (): Promise<BrowserConfigResponse> => {
  const response = await api.get<BrowserConfigResponse>('/config/browser');
  return response.data;
};

export const setBrowserConfig = async (config: BrowserConfig): Promise<{ message: string }> => {
  const response = await api.put<{ message: string }>('/config/browser', config);
  return response.data;
};

export const getSkills = async (): Promise<Skill[]> => {
  const response = await api.get<Skill[]>('/skills');
  return response.data;
};

export interface GlobalRuntimeConfig {
  workspace_path?: string | null;
  memory_auto_extract: boolean;
  memory_threshold: number;
}

export const getGlobalRuntimeConfig = async (): Promise<GlobalRuntimeConfig> => {
  const response = await api.get<GlobalRuntimeConfig>('/config/runtime');
  return response.data;
};

export const updateGlobalRuntimeConfig = async (
  payload: Partial<GlobalRuntimeConfig>,
): Promise<GlobalRuntimeConfig> => {
  const response = await api.put<GlobalRuntimeConfig>('/config/runtime', payload);
  return response.data;
};

export const getGlobalSkills = async (): Promise<SessionSkill[]> => {
  const response = await api.get<{ skills: SessionSkill[] }>('/config/skills');
  return response.data.skills;
};

export const updateGlobalSkills = async (skills: SessionSkill[]): Promise<SessionSkill[]> => {
  const response = await api.put<{ skills: SessionSkill[] }>('/config/skills', { skills });
  return response.data.skills;
};

export const getAutomations = async (): Promise<Automation[]> => {
  const response = await api.get<Automation[]>('/automations');
  return response.data;
};

export const getAutomationStats = async (): Promise<AutomationStats> => {
  const response = await api.get<AutomationStats>('/automations/stats');
  return response.data;
};

export const createAutomation = async (
  payload: AutomationPayload,
): Promise<Automation> => {
  const response = await api.post<Automation>('/automations', payload);
  return response.data;
};

export const updateAutomation = async (automationId: number, payload: Partial<Automation>): Promise<Automation> => {
  const response = await api.put<Automation>(`/automations/${automationId}`, payload);
  return response.data;
};

export const deleteAutomation = async (automationId: number): Promise<void> => {
  await api.delete(`/automations/${automationId}`);
};

export const getAllAutomationRuns = async (limit: number = 200): Promise<AutomationRun[]> => {
  const response = await api.get<AutomationRun[]>(`/automations/runs`, { params: { limit } });
  return response.data;
};

export const runAutomationNow = async (
  automationId: number,
): Promise<{ success: boolean; automation_id: number; trigger_mode: string; run_id?: string | null }> => {
  const response = await api.post<{ success: boolean; automation_id: number; trigger_mode: string; run_id?: string | null }>(
    `/automations/${automationId}/run`,
  );
  return response.data;
};

export const getMcpServers = async (): Promise<McpServer[]> => {
  const response = await api.get<McpServer[]>('/mcp/servers');
  return response.data;
};

export const getMcpStats = async (): Promise<McpStats> => {
  const response = await api.get<McpStats>('/mcp/stats');
  return response.data;
};

export const createMcpServer = async (payload: McpServerPayload): Promise<McpServer> => {
  const response = await api.post<McpServer>('/mcp/servers', payload);
  return response.data;
};

export const updateMcpServer = async (serverId: string, payload: Partial<McpServerPayload>): Promise<McpServer> => {
  const response = await api.put<McpServer>(`/mcp/servers/${serverId}`, payload);
  return response.data;
};

export const deleteMcpServer = async (serverId: string): Promise<{ success: boolean }> => {
  const response = await api.delete<{ success: boolean }>(`/mcp/servers/${serverId}`);
  return response.data;
};

export const probeMcpServer = async (serverId: string): Promise<McpServer> => {
  const response = await api.post<McpServer>(`/mcp/servers/${serverId}/probe`);
  return response.data;
};

export const probeAllMcpServers = async (): Promise<McpServer[]> => {
  const response = await api.post<McpServer[]>('/mcp/probe-all');
  return response.data;
};

export const toggleMcpServer = async (serverId: string, enabled: boolean): Promise<McpServer> => {
  const response = await api.patch<McpServer>(`/mcp/servers/${serverId}/toggle`, { enabled });
  return response.data;
};

export const importMcpServers = async (jsonText: string, autoProbe: boolean = true): Promise<McpImportResult> => {
  const response = await api.post<McpImportResult>('/mcp/import', { json_text: jsonText, auto_probe: autoProbe });
  return response.data;
};

export interface AgentRunInfo {
  conversation_id: number;
  message_id: number | null;
}

export const getAgentRunByRunId = async (runId: string): Promise<AgentRunInfo> => {
  const response = await api.get<AgentRunInfo>(`/agent-runs/${runId}`);
  return response.data;
};

export const getChannels = async (): Promise<Channel[]> => {
  const response = await api.get<Channel[]>('/channels');
  return response.data;
};

export const createChannel = async (payload: ChannelCreatePayload): Promise<Channel> => {
  const response = await api.post<Channel>('/channels', payload);
  return response.data;
};

export const updateChannel = async (channelId: number, payload: ChannelUpdatePayload): Promise<Channel> => {
  const response = await api.put<Channel>(`/channels/${channelId}`, payload);
  return response.data;
};

export const deleteChannel = async (channelId: number): Promise<void> => {
  await api.delete(`/channels/${channelId}`);
};

export const startChannel = async (channelId: number): Promise<Channel> => {
  const response = await api.post<Channel>(`/channels/${channelId}/start`);
  return response.data;
};

export const stopChannel = async (channelId: number): Promise<Channel> => {
  const response = await api.post<Channel>(`/channels/${channelId}/stop`);
  return response.data;
};

export const restartChannel = async (channelId: number): Promise<Channel> => {
  const response = await api.post<Channel>(`/channels/${channelId}/restart`);
  return response.data;
};

export const getChannelChats = async (channelId: number): Promise<ChannelChat[]> => {
  const response = await api.get<ChannelChat[]>(`/channels/${channelId}/chats`);
  return response.data;
};
