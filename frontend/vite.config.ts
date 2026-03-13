import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:18790',
        changeOrigin: true,
      },
      '/v1': {
        target: 'http://127.0.0.1:18790',
        changeOrigin: true,
        timeout: 300000,
        proxyTimeout: 300000,
        configure: (proxy) => {
          proxy.on('proxyReq', (proxyReq, req) => {
            proxyReq.setHeader('Connection', 'keep-alive')
            proxyReq.setHeader('Accept', 'text/event-stream')
            proxyReq.setHeader('Cache-Control', 'no-cache')
          })
          proxy.on('proxyRes', (proxyRes, req, res) => {
            proxyRes.headers['cache-control'] = 'no-cache'
            proxyRes.headers['x-accel-buffering'] = 'no'
          })
          proxy.on('error', (err, req, res) => {
            if (err.code === 'ECONNRESET') {
              return
            }
            console.error('代理错误:', err)
          })
        },
      },
      '/health': {
        target: 'http://127.0.0.1:18790',
        changeOrigin: true,
      },
    },
  },
})
