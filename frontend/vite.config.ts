import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      '/v1': {
        target: 'http://127.0.0.1:18789',
        changeOrigin: true,
        timeout: 300000, // 5分钟超时
        proxyTimeout: 300000, // 代理超时
        configure: (proxy) => {
          proxy.on('proxyReq', (proxyReq, req) => {
            proxyReq.setHeader('Connection', 'keep-alive')
          })
          proxy.on('error', (err, req, res) => {
            // 忽略 ECONNRESET 错误（客户端断开连接）
            if (err.code === 'ECONNRESET') {
              return
            }
            console.error('代理错误:', err)
          })
        },
      },
      '/health': {
        target: 'http://127.0.0.1:18789',
        changeOrigin: true,
      },
    },
  },
})
