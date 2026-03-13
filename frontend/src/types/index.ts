export interface Message {
  id: number
  role: 'user' | 'assistant' | 'system' | 'tool'
  content: string
  timestamp?: string
  toolCalls?: ToolCall[]
  thoughts?: string
  image?: string
}

export interface Session {
  id: string
  channel: string
  message_count: number
  created_at: string
  updated_at: string
}

export interface ToolCall {
  id: string
  name: string
  arguments: Record<string, unknown>
  status: 'pending' | 'running' | 'success' | 'error'
  result?: unknown
  error?: string
  durationMs?: number
}

export interface Model {
  id: string
  name: string
  default: boolean
}
