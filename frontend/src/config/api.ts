/**
 * API 配置文件
 * 统一管理 API 基础 URL 和相关配置
 */

/**
 * API 基础 URL
 * 开发环境使用相对路径，通过 Vite 代理转发到后端
 * 生产环境可以修改为完整的后端服务地址
 */
export const API_BASE_URL = import.meta.env.DEV ? '' : 'http://127.0.0.1:18790'

/**
 * API 端点配置
 */
export const API_ENDPOINTS = {
  HEALTH: '/health',
  
  SESSIONS: '/v1/sessions',
  SESSION_DETAIL: (sessionId: string) => `/v1/sessions/${sessionId}`,
  SESSION_MESSAGES: (sessionId: string) => `/v1/sessions/${sessionId}/messages`,
  
  CHAT_COMPLETIONS: '/v1/chat/completions',
}

export const API_TIMEOUT = 300000
