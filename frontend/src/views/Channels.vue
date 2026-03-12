<script setup lang="ts">
/**
 * Channels 通道管理页面
 * 显示和管理所有通道
 */
import { useChannels } from '@/composables/useChannels'
import ChannelCard from '@/components/channel/ChannelCard.vue'

const { channels, loading, error, startChannel, stopChannel, refresh } = useChannels()

function getChannelIcon(name: string): string {
  const icons: Record<string, string> = {
    web: 'M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9',
    qq: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z',
    wechat: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z',
  }
  return icons[name] || icons.web
}

function getChannelDescription(name: string): string {
  const descriptions: Record<string, string> = {
    web: 'Web 端聊天接口，支持 REST API 和 SSE 流式输出',
    qq: 'QQ 机器人通道，基于 NapCat 实现',
    wechat: '企业微信机器人通道',
  }
  return descriptions[name] || '消息通道'
}
</script>

<template>
  <div class="channels-page">
    <div class="page-header">
      <h1>通道管理</h1>
      <button @click="refresh" class="btn btn-secondary" :disabled="loading">
        <svg class="icon" :class="{ spinning: loading }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        刷新
      </button>
    </div>

    <div v-if="error" class="error-message">
      {{ error }}
    </div>

    <div class="channels-grid">
      <ChannelCard
        v-for="(status, name) in channels"
        :key="name"
        :name="name"
        :status="status"
        :icon="getChannelIcon(name)"
        :description="getChannelDescription(name)"
        @start="startChannel(name)"
        @stop="stopChannel(name)"
      />
    </div>
  </div>
</template>

<style scoped>
.channels-page {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.page-header h1 {
  font-size: 1.75rem;
  font-weight: 800;
  margin: 0;
}

.error-message {
  padding: 1rem;
  background: hsl(var(--destructive) / 0.1);
  border: 1px solid hsl(var(--destructive));
  border-radius: var(--radius);
  color: hsl(var(--destructive));
  margin-bottom: 1rem;
}

.channels-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1.5rem;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: var(--radius);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary {
  background: hsl(var(--secondary));
  color: hsl(var(--secondary-foreground));
  border: 1px solid hsl(var(--border));
}

.btn-secondary:hover:not(:disabled) {
  background: hsl(var(--accent));
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.icon {
  width: 1rem;
  height: 1rem;
}

.icon.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
