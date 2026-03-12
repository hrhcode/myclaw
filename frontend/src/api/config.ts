/**
 * 配置管理 API
 */
import { get, put, post, del } from '@/utils/request'

export interface LLMConfig {
  provider: string
  model: string
  api_key: string
}

export interface MemoryConfig {
  enabled: boolean
  max_memories: number
  embedding: {
    provider: string
    model: string
    api_key: string
    base_url: string
  }
  hybrid_search: {
    enabled: boolean
    vector_weight: number
    fts_weight: number
    min_score: number
  }
}

export interface AgentConfig {
  system_prompt: string
}

export interface AppConfig {
  server: {
    port: number
    host: string
  }
  gateway: {
    enabled: boolean
  }
  channels: {
    web: { enabled: boolean }
    qq: { enabled: boolean; api_url: string; access_token: string }
    wechat: {
      enabled: boolean
      corp_id: string
      agent_id: string
      secret: string
      token: string
      encoding_aes_key: string
    }
  }
  llm: LLMConfig
  memory: MemoryConfig
  agent: AgentConfig
}

export const configApi = {
  async get(): Promise<AppConfig> {
    return get('/api/config')
  },

  async update(data: Partial<{
    llm_provider: string
    llm_model: string
    llm_api_key: string
    memory_enabled: boolean
    embedding_provider: string
    embedding_api_key: string
    embedding_base_url: string
    vector_weight: number
    fts_weight: number
    min_score: number
    system_prompt: string
  }>): Promise<{ status: string; message: string }> {
    return put('/api/config', data)
  },

  async reload(): Promise<{ status: string; message: string }> {
    return post('/api/config/reload', {})
  },
}

export interface Tool {
  name: string
  description: string
  parameters: Record<string, any>
  enabled: boolean
}

export const toolsApi = {
  async list(): Promise<{ tools: Tool[] }> {
    return get('/api/tools')
  },

  async setEnabled(name: string, enabled: boolean): Promise<{ status: string; message: string }> {
    return put(`/api/tools/${name}/enabled`, { enabled })
  },
}

export interface Memory {
  id: number
  session_id: string
  role: string
  content: string
  tool_calls: any[] | null
  tool_call_id: string | null
  timestamp: string
}

export interface MemoryStats {
  total_messages: number
  total_sessions: number
}

export const memoriesApi = {
  async list(params?: {
    query?: string
    session_id?: string
    limit?: number
    offset?: number
  }): Promise<{ memories: Memory[]; total: number }> {
    const query = new URLSearchParams()
    if (params?.query) query.set('query', params.query)
    if (params?.session_id) query.set('session_id', params.session_id)
    if (params?.limit) query.set('limit', params.limit.toString())
    if (params?.offset) query.set('offset', params.offset.toString())
    return get(`/api/memories?${query.toString()}`)
  },

  async stats(): Promise<MemoryStats> {
    return get('/api/memories/stats')
  },

  async delete(id: number): Promise<{ status: string; message: string }> {
    return del(`/api/memories/${id}`)
  },

  async clearAll(): Promise<{ status: string; message: string }> {
    return del('/api/memories')
  },
}

export const channelConfigApi = {
  async update(channelName: string, config: {
    enabled?: boolean
    api_url?: string
    access_token?: string
    corp_id?: string
    agent_id?: string
    secret?: string
    token?: string
    encoding_aes_key?: string
  }): Promise<{ status: string; message: string }> {
    return put(`/api/channels/${channelName}/config`, config)
  },
}
