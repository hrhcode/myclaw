/**
 * Session 状态管理 Composable
 * 提供 Session 数据的响应式管理
 */
import { ref, watch, onMounted } from 'vue'
import { sessionApi, type SessionInfo } from '@/api/gateway'

export function useSessions() {
  const sessions = ref<SessionInfo[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const filters = ref({
    channel: '',
    limit: 50,
  })

  async function fetchSessions() {
    loading.value = true
    try {
      const params: { channel?: string; limit?: number } = {}
      if (filters.value.channel) params.channel = filters.value.channel
      params.limit = filters.value.limit

      const result = await sessionApi.list(params)
      sessions.value = result.sessions
      error.value = null
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e)
    } finally {
      loading.value = false
    }
  }

  async function deleteSession(id: string) {
    try {
      await sessionApi.delete(id)
      await fetchSessions()
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e)
    }
  }

  watch(filters, fetchSessions, { deep: true })
  onMounted(fetchSessions)

  return {
    sessions,
    loading,
    error,
    filters,
    refresh: fetchSessions,
    deleteSession,
  }
}
