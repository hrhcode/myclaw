/**
 * Axios 实例封装
 * 统一处理 HTTP 请求，包括请求拦截、响应拦截、错误处理等
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios'
import { API_BASE_URL, API_TIMEOUT } from '../config/api'

/**
 * 创建 axios 实例
 */
const axiosInstance: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * 请求拦截器
 * 在发送请求之前做些什么
 */
axiosInstance.interceptors.request.use(
  (config) => {
    // 可以在这里添加 token 等认证信息
    // const token = localStorage.getItem('token')
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`
    // }

    // 设置 Connection 为 keep-alive 以支持长连接
    config.headers['Connection'] = 'keep-alive'

    return config
  },
  (error: AxiosError) => {
    // 对请求错误做些什么
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

/**
 * 响应拦截器
 * 对响应数据做点什么
 */
axiosInstance.interceptors.response.use(
  (response: AxiosResponse) => {
    // 对响应数据做点什么
    return response
  },
  (error: AxiosError) => {
    // 对响应错误做点什么
    if (error.code === 'ECONNRESET') {
      // 连接重置错误，忽略
      return Promise.reject(error)
    }

    console.error('响应错误:', error)

    // 可以根据不同的状态码做不同的处理
    if (error.response) {
      switch (error.response.status) {
        case 401:
          // 未授权，可以跳转到登录页
          console.error('未授权，请重新登录')
          break
        case 403:
          console.error('禁止访问')
          break
        case 404:
          console.error('资源不存在')
          break
        case 500:
          console.error('服务器错误')
          break
        default:
          console.error('未知错误')
      }
    } else if (error.request) {
      // 请求已发出但没有收到响应
      console.error('网络错误，请检查网络连接')
    } else {
      // 在设置请求时发生了错误
      console.error('请求配置错误')
    }

    return Promise.reject(error)
  }
)

/**
 * 封装 GET 请求
 * @param url 请求地址
 * @param config 请求配置
 * @returns Promise
 */
export function get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
  return axiosInstance.get(url, config).then((res) => res.data)
}

/**
 * 封装 POST 请求
 * @param url 请求地址
 * @param data 请求数据
 * @param config 请求配置
 * @returns Promise
 */
export function post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
  return axiosInstance.post(url, data, config).then((res) => res.data)
}

/**
 * 封装 PUT 请求
 * @param url 请求地址
 * @param data 请求数据
 * @param config 请求配置
 * @returns Promise
 */
export function put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
  return axiosInstance.put(url, data, config).then((res) => res.data)
}

/**
 * 封装 DELETE 请求
 * @param url 请求地址
 * @param config 请求配置
 * @returns Promise
 */
export function del<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
  return axiosInstance.delete(url, config).then((res) => res.data)
}

/**
 * 封装流式请求（用于 SSE）
 * @param url 请求地址
 * @param data 请求数据
 * @param onMessage 消息回调
 * @param onError 错误回调
 * @param onComplete 完成回调
 * @returns AbortController 用于取消请求
 */
export function stream(
  url: string,
  data: any,
  onMessage: (data: any) => void,
  onError?: (error: Error) => void,
  onComplete?: () => void
): AbortController {
  const abortController = new AbortController()

  fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream',
      'Connection': 'keep-alive',
    },
    body: JSON.stringify(data),
    signal: abortController.signal,
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('No reader available')
      }

      const decoder = new TextDecoder()
      let buffer = ''

      const read = async () => {
        try {
          const { done, value } = await reader.read()

          if (done) {
            onComplete?.()
            return
          }

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6)

              if (data === '[DONE]') {
                continue
              }

              try {
                const parsed = JSON.parse(data)
                onMessage(parsed)
              } catch (e) {
                // 忽略解析错误
              }
            }
          }

          read()
        } catch (error) {
          onError?.(error as Error)
        }
      }

      read()
    })
    .catch((error) => {
      if (error.name !== 'AbortError') {
        onError?.(error)
      }
    })

  return abortController
}

export default axiosInstance
