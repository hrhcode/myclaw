/**
 * API 配置文件
 * 统一管理 API 基础 URL 和相关配置
 * 修改此文件即可更改后端服务的根路由和端口
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
  /**
   * 健康检查
   */
  HEALTH: '/health',

  /**
   * 会话管理
   */
  SESSIONS: '/v1/sessions',
  SESSION_DETAIL: (sessionId: string) => `/v1/sessions/${sessionId}`,
  SESSION_MESSAGES: (sessionId: string) => `/v1/sessions/${sessionId}/messages`,

  /**
   * 聊天完成
   */
  CHAT_COMPLETIONS: '/v1/chat/completions',
}

/**
 * API 请求超时时间（毫秒）
 */
export const API_TIMEOUT = 300000
