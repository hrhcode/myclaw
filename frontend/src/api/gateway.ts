/**
 * Gateway API 封装
 * 提供所有与 Gateway 相关的 API 调用
 */
import { get, post } from '@/utils/request'

export interface GatewayStatus {
  running: boolean
  started_at: string | null
  uptime_seconds: number
  channels: Record<string, ChannelStatus>
  sessions_count: number
}

export interface ChannelStatus {
  name: string
  enabled: boolean
  running: boolean
  connected: boolean
  last_message_at: string | null
  error: string | null
}

export interface SessionInfo {
  id: string
  channel: string
  message_count: number
  created_at: string
  updated_at: string
}

export const gatewayApi = {
  async getStatus(): Promise<GatewayStatus> {
    return get('/api/gateway/status')
  },

  async getInfo(): Promise<{
    version: string
    uptime_seconds: number
    started_at: string | null
    channels: string[]
    sessions_count: number
  }> {
    return get('/api/gateway/info')
  },
}

export const channelApi = {
  async list(): Promise<{ channels: Array<{ name: string; status: ChannelStatus }> }> {
    return get('/api/channels')
  },

  async get(name: string): Promise<ChannelStatus> {
    return get(`/api/channels/${name}`)
  },

  async start(name: string): Promise<{ status: string; message: string }> {
    return post(`/api/channels/${name}/start`, {})
  },

  async stop(name: string): Promise<{ status: string; message: string }> {
    return post(`/api/channels/${name}/stop`, {})
  },
}

export const sessionApi = {
  async list(params?: { channel?: string; limit?: number }): Promise<{
    sessions: SessionInfo[]
    total: number
  }> {
    const query = new URLSearchParams()
    if (params?.channel) query.set('channel', params.channel)
    if (params?.limit) query.set('limit', params.limit.toString())
    return get(`/api/sessions?${query.toString()}`)
  },

  async get(id: string): Promise<SessionInfo> {
    return get(`/api/sessions/${id}`)
  },

  async delete(id: string): Promise<{ status: string; message: string }> {
    const { del } = await import('@/utils/request')
    return del(`/api/sessions/${id}`)
  },
}
