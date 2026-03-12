/**
 * Gateway 状态管理 Composable
 * 提供 Gateway 状态的响应式管理和自动轮询
 */
import { ref, onMounted, onUnmounted } from 'vue'
import { gatewayApi, type GatewayStatus } from '@/api/gateway'

export function useGateway() {
  const status = ref<GatewayStatus | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  let pollInterval: number | null = null

  async function fetchStatus() {
    try {
      loading.value = true
      status.value = await gatewayApi.getStatus()
      error.value = null
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e)
    } finally {
      loading.value = false
    }
  }

  function startPolling(interval = 5000) {
    fetchStatus()
    pollInterval = window.setInterval(fetchStatus, interval)
  }

  function stopPolling() {
    if (pollInterval) {
      clearInterval(pollInterval)
      pollInterval = null
    }
  }

  onMounted(() => startPolling())
  onUnmounted(() => stopPolling())

  return {
    status,
    loading,
    error,
    refresh: fetchStatus,
    startPolling,
    stopPolling,
  }
}
