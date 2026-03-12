<script setup lang="ts">
/**
 * ChannelCard 通道卡片组件
 * 显示单个通道的状态和控制按钮
 */
import type { ChannelStatus } from '@/api/gateway'

defineProps<{
  name: string
  status: ChannelStatus
  icon: string
  description: string
}>()

const emit = defineEmits<{
  start: []
  stop: []
}>()

function formatTime(time: string | null): string {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}
</script>

<template>
  <div class="channel-card">
    <div class="channel-header">
      <div class="channel-icon">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="icon" />
        </svg>
      </div>
      <div class="channel-title">
        <h3>{{ name }}</h3>
        <span class="channel-status" :class="{ running: status.running, connected: status.connected }">
          {{ status.running ? (status.connected ? '已连接' : '运行中') : '已停止' }}
        </span>
      </div>
    </div>

    <p class="channel-description">{{ description }}</p>

    <div class="channel-stats">
      <div class="stat-item">
        <span class="label">运行中</span>
        <span class="value" :class="{ active: status.running }">
          {{ status.running ? '是' : '否' }}
        </span>
      </div>
      <div class="stat-item">
        <span class="label">已连接</span>
        <span class="value" :class="{ active: status.connected }">
          {{ status.connected ? '是' : '否' }}
        </span>
      </div>
      <div class="stat-item">
        <span class="label">最后消息</span>
        <span class="value mono">{{ formatTime(status.last_message_at) }}</span>
      </div>
    </div>

    <div v-if="status.error" class="channel-error">
      <svg class="error-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
      {{ status.error }}
    </div>

    <div class="channel-actions">
      <button
        v-if="!status.running"
        @click="emit('start')"
        class="btn btn-primary"
      >
        <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        启动
      </button>
      <button
        v-else
        @click="emit('stop')"
        class="btn btn-danger"
      >
        <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
        </svg>
        停止
      </button>
    </div>
  </div>
</template>

<style scoped>
.channel-card {
  background: hsl(var(--card));
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.channel-header {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.channel-icon {
  width: 3rem;
  height: 3rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: hsl(var(--primary) / 0.1);
  border-radius: var(--radius-lg);
  color: hsl(var(--primary));
}

.channel-icon svg {
  width: 1.5rem;
  height: 1.5rem;
}

.channel-title {
  flex: 1;
}

.channel-title h3 {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
  text-transform: capitalize;
}

.channel-status {
  font-size: 0.75rem;
  padding: 0.125rem 0.5rem;
  background: hsl(var(--muted));
  border-radius: var(--radius-full);
  color: hsl(var(--muted-foreground));
}

.channel-status.running {
  background: hsl(var(--chart-1) / 0.2);
  color: hsl(var(--chart-1));
}

.channel-status.connected {
  background: hsl(var(--chart-2) / 0.2);
  color: hsl(var(--chart-2));
}

.channel-description {
  margin: 0;
  font-size: 0.875rem;
  color: hsl(var(--muted-foreground));
  line-height: 1.5;
}

.channel-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.5rem;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.stat-item .label {
  font-size: 0.75rem;
  color: hsl(var(--muted-foreground));
}

.stat-item .value {
  font-size: 0.875rem;
  font-weight: 500;
}

.stat-item .value.active {
  color: hsl(var(--chart-2));
}

.channel-error {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  background: hsl(var(--destructive) / 0.1);
  border-radius: var(--radius);
  font-size: 0.875rem;
  color: hsl(var(--destructive));
}

.error-icon {
  width: 1rem;
  height: 1rem;
  flex-shrink: 0;
}

.channel-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: auto;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: var(--radius);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-primary {
  background: hsl(var(--primary));
  color: hsl(var(--primary-foreground));
}

.btn-primary:hover {
  opacity: 0.9;
}

.btn-danger {
  background: hsl(var(--destructive));
  color: hsl(var(--destructive-foreground));
}

.btn-danger:hover {
  opacity: 0.9;
}

.icon {
  width: 1rem;
  height: 1rem;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.75rem;
}
</style>
