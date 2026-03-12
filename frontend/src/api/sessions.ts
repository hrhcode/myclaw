/**
 * Sessions API
 * 会话管理相关 API 接口
 */
import { get, del } from '@/utils/request'

export interface Session {
  id: string
  channel: string
  created_at: string
  updated_at?: string
  message_count?: number
  last_message?: string
}

export interface SessionListResponse {
  sessions: Session[]
  total: number
}

export interface SessionListParams {
  query?: string
  channel?: string
  limit?: number
  offset?: number
}

export const sessionsApi = {
  /**
   * 获取会话列表
   */
  async list(params: SessionListParams = {}): Promise<SessionListResponse> {
    const searchParams = new URLSearchParams()
    if (params.query) searchParams.set('query', params.query)
    if (params.channel) searchParams.set('channel', params.channel)
    if (params.limit) searchParams.set('limit', params.limit.toString())
    if (params.offset) searchParams.set('offset', params.offset.toString())
    
    const queryString = searchParams.toString()
    const url = queryString ? `/api/sessions?${queryString}` : '/api/sessions'
    return get(url)
  },

  /**
   * 获取单个会话详情
   */
  async get(id: string): Promise<Session> {
    return get(`/api/sessions/${id}`)
  },

  /**
   * 删除会话
   */
  async delete(id: string): Promise<void> {
    return del(`/api/sessions/${id}`)
  },
}
