/**
 * System 系统信息 Composable
 * 提供系统状态的响应式管理
 */
import { ref, computed } from 'vue'
import { get } from '@/utils/request'

export interface SystemInfo {
  gateway: {
    running: boolean
    uptime_seconds: number
    started_at: string | null
    sessions_count: number
  }
  llm: {
    provider: string
    model: string
  }
  memory: {
    enabled: boolean
    total_messages: number
    total_sessions: number
  }
  channels: {
    web: { running: boolean; connected: boolean }
    qq: { running: boolean; connected: boolean }
    wechat: { running: boolean; connected: boolean }
  }
}

const systemInfo = ref<SystemInfo | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

export function useSystem() {
  async function fetchSystemInfo() {
    loading.value = true
    error.value = null
    
    try {
      const [gatewayStatus, config, channels, memoryStats] = await Promise.all([
        get('/api/gateway/status'),
        get('/api/config'),
        get('/api/channels'),
        get('/api/memories/stats'),
      ])
      
      const channelsMap: Record<string, { running: boolean; connected: boolean }> = {}
      for (const ch of channels.channels || []) {
        channelsMap[ch.name] = ch.status
      }
      
      systemInfo.value = {
        gateway: {
          running: gatewayStatus.running || false,
          uptime_seconds: gatewayStatus.uptime_seconds || 0,
          started_at: gatewayStatus.started_at || null,
          sessions_count: gatewayStatus.sessions_count || 0,
        },
        llm: {
          provider: config.llm?.provider || '',
          model: config.llm?.model || '',
        },
        memory: {
          enabled: config.memory?.enabled || false,
          total_messages: memoryStats.total_messages || 0,
          total_sessions: memoryStats.total_sessions || 0,
        },
        channels: {
          web: channelsMap.web || { running: false, connected: false },
          qq: channelsMap.qq || { running: false, connected: false },
          wechat: channelsMap.wechat || { running: false, connected: false },
        },
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e)
    } finally {
      loading.value = false
    }
  }
  
  const uptimeFormatted = computed(() => {
    const seconds = systemInfo.value?.gateway.uptime_seconds || 0
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = Math.floor(seconds % 60)
    if (hours > 0) {
      return `${hours}小时 ${minutes}分钟`
    }
    if (minutes > 0) {
      return `${minutes}分钟 ${secs}秒`
    }
    return `${secs}秒`
  })
  
  const startedAtFormatted = computed(() => {
    if (!systemInfo.value?.gateway.started_at) return '-'
    return new Date(systemInfo.value.gateway.started_at).toLocaleString('zh-CN')
  })
  
  const activeChannelsCount = computed(() => {
    if (!systemInfo.value?.channels) return 0
    return Object.values(systemInfo.value.channels).filter(ch => ch.running).length
  })
  
  const totalChannelsCount = computed(() => {
    if (!systemInfo.value?.channels) return 0
    return Object.keys(systemInfo.value.channels).length
  })
  
  return {
    systemInfo,
    loading,
    error,
    fetchSystemInfo,
    uptimeFormatted,
    startedAtFormatted,
    activeChannelsCount,
    totalChannelsCount,
  }
}
