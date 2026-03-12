/**
 * Channel 状态管理 Composable
 * 提供 Channel 数据的响应式管理
 */
import { ref, onMounted } from 'vue'
import { channelApi, type ChannelStatus } from '@/api/gateway'

export function useChannels() {
  const channels = ref<Record<string, ChannelStatus>>({})
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchChannels() {
    loading.value = true
    try {
      const result = await channelApi.list()
      channels.value = Object.fromEntries(
        result.channels.map((ch) => [ch.name, ch.status])
      )
      error.value = null
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e)
    } finally {
      loading.value = false
    }
  }

  async function startChannel(name: string) {
    try {
      await channelApi.start(name)
      await fetchChannels()
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e)
    }
  }

  async function stopChannel(name: string) {
    try {
      await channelApi.stop(name)
      await fetchChannels()
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e)
    }
  }

  onMounted(fetchChannels)

  return {
    channels,
    loading,
    error,
    refresh: fetchChannels,
    startChannel,
    stopChannel,
  }
}
