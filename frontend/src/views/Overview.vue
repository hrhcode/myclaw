<script setup lang="ts">
/**
 * Overview 概览页面
 * 显示 Gateway 运行状态和整体信息
 */
import { computed } from 'vue'
import { useGateway } from '@/composables/useGateway'
import { useChannels } from '@/composables/useChannels'

const { status: gatewayStatus, loading: gatewayLoading, refresh } = useGateway()
const { channels, loading: channelsLoading } = useChannels()

const uptimeFormatted = computed(() => {
  const seconds = gatewayStatus.value?.uptime_seconds || 0
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
  if (!gatewayStatus.value?.started_at) return '-'
  return new Date(gatewayStatus.value.started_at).toLocaleString('zh-CN')
})

const activeChannelsCount = computed(() => {
  return Object.values(channels.value).filter((ch) => ch.running).length
})
</script>

<template>
  <div class="overview-page">
    <div class="page-header">
      <h1>概览</h1>
      <button @click="refresh" class="btn btn-secondary" :disabled="gatewayLoading">
        <svg class="icon" :class="{ spinning: gatewayLoading }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        刷新
      </button>
    </div>

    <div class="grid grid-cols-2 gap-4">
      <div class="card">
        <h2>Gateway 状态</h2>
        <div class="status-list">
          <div class="status-item">
            <span class="label">运行状态</span>
            <span class="value">
              <span class="status-dot" :class="{ ok: gatewayStatus?.running }"></span>
              {{ gatewayStatus?.running ? '运行中' : '已停止' }}
            </span>
          </div>
          <div class="status-item">
            <span class="label">启动时间</span>
            <span class="value mono">{{ startedAtFormatted }}</span>
          </div>
          <div class="status-item">
            <span class="label">运行时长</span>
            <span class="value mono">{{ uptimeFormatted }}</span>
          </div>
        </div>
      </div>

      <div class="card">
        <h2>系统快照</h2>
        <div class="status-list">
          <div class="status-item">
            <span class="label">活跃通道</span>
            <span class="value">
              <span class="count">{{ activeChannelsCount }}</span>
              <span class="muted">/ {{ Object.keys(channels).length }}</span>
            </span>
          </div>
          <div class="status-item">
            <span class="label">活跃会话</span>
            <span class="value">
              <span class="count">{{ gatewayStatus?.sessions_count || 0 }}</span>
            </span>
          </div>
        </div>
      </div>
    </div>

    <div class="card">
      <h2>通道状态</h2>
      <div class="channel-grid">
        <div
          v-for="(status, name) in channels"
          :key="name"
          class="channel-mini-card"
        >
          <div class="channel-info">
            <span class="channel-name">{{ name }}</span>
            <span class="status-dot" :class="{ ok: status.connected }"></span>
          </div>
          <div class="channel-meta">
            <span class="meta-item" :class="{ active: status.running }">
              {{ status.running ? '运行中' : '已停止' }}
            </span>
            <span class="meta-item" :class="{ active: status.connected }">
              {{ status.connected ? '已连接' : '未连接' }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.overview-page {
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

.grid {
  display: grid;
}

.grid-cols-2 {
  grid-template-columns: repeat(2, 1fr);
}

.gap-4 {
  gap: 1rem;
}

.card {
  background: hsl(var(--card));
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius-lg);
  padding: 1.5rem;
}

.card h2 {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 1rem 0;
  color: hsl(var(--muted-foreground));
}

.status-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-item .label {
  color: hsl(var(--muted-foreground));
  font-size: 0.875rem;
}

.status-item .value {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: hsl(var(--destructive));
  box-shadow: 0 0 8px hsl(var(--destructive) / 0.5);
}

.status-dot.ok {
  background: hsl(var(--chart-2));
  box-shadow: 0 0 8px hsl(var(--chart-2) / 0.5);
}

.count {
  font-size: 1.5rem;
  font-weight: 700;
}

.muted {
  color: hsl(var(--muted-foreground));
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

.channel-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}

.channel-mini-card {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1rem;
  background: hsl(var(--muted) / 0.3);
  border-radius: var(--radius);
}

.channel-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.channel-name {
  font-weight: 600;
  text-transform: capitalize;
}

.channel-meta {
  display: flex;
  gap: 0.5rem;
}

.meta-item {
  font-size: 0.75rem;
  padding: 0.125rem 0.5rem;
  background: hsl(var(--muted));
  border-radius: var(--radius-full);
  color: hsl(var(--muted-foreground));
}

.meta-item.active {
  background: hsl(var(--chart-2) / 0.2);
  color: hsl(var(--chart-2));
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

@media (max-width: 768px) {
  .grid-cols-2 {
    grid-template-columns: 1fr;
  }
}
</style>
