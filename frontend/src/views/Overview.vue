<script setup lang="ts">
/**
 * Overview 概览页面
 * 显示 Gateway 运行状态和整体信息
 * 使用科技感组件优化视觉效果
 */
import { onMounted, onUnmounted, ref } from 'vue'
import { useSystem } from '@/composables/useSystem'
import { Card, Button, Badge, Skeleton, GlowCard, StatsCard, AnimatedList, AnimatedListItem } from '@/components/ui'

const {
  systemInfo,
  loading,
  error,
  fetchSystemInfo,
  uptimeFormatted,
  startedAtFormatted,
  activeChannelsCount,
  totalChannelsCount,
} = useSystem()

let refreshInterval: number | null = null
const listVisible = ref(false)

onMounted(async () => {
  await fetchSystemInfo()
  refreshInterval = window.setInterval(fetchSystemInfo, 30000)
  setTimeout(() => {
    listVisible.value = true
  }, 100)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})

function getChannelIcon(name: string): string {
  const icons: Record<string, string> = {
    web: 'M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9',
    qq: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z',
    wechat: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z',
  }
  return icons[name] || icons.web
}

function getChannelLabel(name: string): string {
  const labels: Record<string, string> = {
    web: 'Web',
    qq: 'QQ',
    wechat: '企业微信',
  }
  return labels[name] || name
}

const statIcons = {
  gateway: 'M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01',
  channel: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z',
  llm: 'M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z',
  memory: 'M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4',
}
</script>

<template>
  <div class="overview-page page-container">
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          <span class="title-text">概览</span>
          <span class="title-glow" />
        </h1>
        <p class="page-subtitle">系统运行状态和关键指标</p>
      </div>
      <Button variant="secondary" :loading="loading" @click="fetchSystemInfo">
        <svg class="icon" :class="{ spinning: loading }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        刷新
      </Button>
    </div>

    <div v-if="error" class="error-alert">
      <div class="error-icon">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>
      <div class="error-content">
        <h4>加载失败</h4>
        <p>{{ error }}</p>
      </div>
    </div>

    <AnimatedList class="stats-grid" :visible="listVisible" :stagger="80">
      <AnimatedListItem :index="0" :visible="listVisible">
        <GlowCard class="stat-card" glow-color="rgba(59, 130, 246, 0.4)">
          <div class="stat-content">
            <div class="stat-icon icon-box icon-box-primary">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="statIcons.gateway" />
              </svg>
            </div>
            <div class="stat-info">
              <span class="stat-label">Gateway 状态</span>
              <div v-if="loading" class="stat-skeleton">
                <Skeleton width="60px" height="1.5rem" />
              </div>
              <div v-else class="stat-value">
                <Badge :variant="systemInfo?.gateway.running ? 'success' : 'danger'" size="md">
                  {{ systemInfo?.gateway.running ? '运行中' : '已停止' }}
                </Badge>
              </div>
            </div>
          </div>
          <div class="stat-meta">
            <div class="meta-item">
              <span class="meta-label">运行时长</span>
              <span class="meta-value mono">{{ uptimeFormatted }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">启动时间</span>
              <span class="meta-value mono">{{ startedAtFormatted }}</span>
            </div>
          </div>
        </GlowCard>
      </AnimatedListItem>

      <AnimatedListItem :index="1" :visible="listVisible">
        <GlowCard class="stat-card" glow-color="rgba(16, 185, 129, 0.4)">
          <div class="stat-content">
            <div class="stat-icon icon-box icon-box-success">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="statIcons.channel" />
              </svg>
            </div>
            <div class="stat-info">
              <span class="stat-label">活跃通道</span>
              <div v-if="loading" class="stat-skeleton">
                <Skeleton width="40px" height="2rem" />
              </div>
              <div v-else class="stat-value">
                <span class="stat-number">{{ activeChannelsCount }}</span>
                <span class="stat-total">/ {{ totalChannelsCount }}</span>
              </div>
            </div>
          </div>
          <div class="stat-meta">
            <div class="meta-item">
              <span class="meta-label">活跃会话</span>
              <span class="meta-value">{{ systemInfo?.gateway.sessions_count || 0 }}</span>
            </div>
          </div>
        </GlowCard>
      </AnimatedListItem>

      <AnimatedListItem :index="2" :visible="listVisible">
        <GlowCard class="stat-card" glow-color="rgba(139, 92, 246, 0.4)">
          <div class="stat-content">
            <div class="stat-icon icon-box icon-box-purple">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="statIcons.llm" />
              </svg>
            </div>
            <div class="stat-info">
              <span class="stat-label">LLM 模型</span>
              <div v-if="loading" class="stat-skeleton">
                <Skeleton width="100px" height="1.5rem" />
              </div>
              <div v-else class="stat-value">
                <span class="stat-model">{{ systemInfo?.llm.model || '-' }}</span>
              </div>
            </div>
          </div>
          <div class="stat-meta">
            <div class="meta-item">
              <span class="meta-label">提供商</span>
              <span class="meta-value">{{ systemInfo?.llm.provider || '-' }}</span>
            </div>
          </div>
        </GlowCard>
      </AnimatedListItem>

      <AnimatedListItem :index="3" :visible="listVisible">
        <GlowCard class="stat-card" glow-color="rgba(245, 158, 11, 0.4)">
          <div class="stat-content">
            <div class="stat-icon icon-box icon-box-warning">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="statIcons.memory" />
              </svg>
            </div>
            <div class="stat-info">
              <span class="stat-label">记忆系统</span>
              <div v-if="loading" class="stat-skeleton">
                <Skeleton width="60px" height="1.5rem" />
              </div>
              <div v-else class="stat-value">
                <Badge :variant="systemInfo?.memory.enabled ? 'success' : 'default'" size="md">
                  {{ systemInfo?.memory.enabled ? '已启用' : '已禁用' }}
                </Badge>
              </div>
            </div>
          </div>
          <div class="stat-meta">
            <div class="meta-item">
              <span class="meta-label">记忆条数</span>
              <span class="meta-value">{{ systemInfo?.memory.total_messages || 0 }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">会话数</span>
              <span class="meta-value">{{ systemInfo?.memory.total_sessions || 0 }}</span>
            </div>
          </div>
        </GlowCard>
      </AnimatedListItem>
    </AnimatedList>

    <Card title="通道状态" class="channels-section">
      <template #actions>
        <router-link to="/channels">
          <Button variant="ghost" size="sm">管理通道</Button>
        </router-link>
      </template>
      
      <div v-if="loading" class="channels-skeleton">
        <div v-for="i in 3" :key="i" class="channel-skeleton-item">
          <Skeleton width="48px" height="48px" radius="var(--radius)" />
          <div class="skeleton-text">
            <Skeleton width="80px" height="1rem" />
            <Skeleton width="120px" height="0.75rem" />
          </div>
        </div>
      </div>
      
      <div v-else class="channels-grid">
        <div
          v-for="(status, name) in systemInfo?.channels"
          :key="name"
          class="channel-card"
          :class="{ active: status.running }"
        >
          <div class="channel-glow" />
          <div class="channel-icon">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="getChannelIcon(name)" />
            </svg>
          </div>
          <div class="channel-info">
            <h4 class="channel-name">{{ getChannelLabel(name) }}</h4>
            <div class="channel-status">
              <span class="status-dot" :class="{ active: status.running }"></span>
              <span>{{ status.running ? '运行中' : '已停止' }}</span>
            </div>
          </div>
          <div class="channel-connection">
            <Badge :variant="status.connected ? 'success' : 'default'" size="sm">
              {{ status.connected ? '已连接' : '未连接' }}
            </Badge>
          </div>
        </div>
      </div>
    </Card>

    <Card title="快速操作" class="quick-actions-section">
      <div class="quick-actions">
        <router-link to="/sessions" class="quick-action">
          <div class="action-glow" />
          <div class="action-icon icon-box icon-box-primary">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="statIcons.channel" />
            </svg>
          </div>
          <div class="action-content">
            <h4>会话管理</h4>
            <p>查看和管理所有会话</p>
          </div>
          <svg class="action-arrow" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </router-link>
        
        <router-link to="/memories" class="quick-action">
          <div class="action-glow" />
          <div class="action-icon icon-box icon-box-success">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="statIcons.memory" />
            </svg>
          </div>
          <div class="action-content">
            <h4>记忆管理</h4>
            <p>浏览和搜索对话记忆</p>
          </div>
          <svg class="action-arrow" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </router-link>
        
        <router-link to="/tools" class="quick-action">
          <div class="action-glow" />
          <div class="action-icon icon-box icon-box-purple">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </div>
          <div class="action-content">
            <h4>工具管理</h4>
            <p>配置 AI 可用工具</p>
          </div>
          <svg class="action-arrow" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </router-link>
        
        <router-link to="/settings" class="quick-action">
          <div class="action-glow" />
          <div class="action-icon icon-box icon-box-orange">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
            </svg>
          </div>
          <div class="action-content">
            <h4>系统设置</h4>
            <p>配置 LLM、记忆系统等</p>
          </div>
          <svg class="action-arrow" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </router-link>
      </div>
    </Card>
  </div>
</template>

<style scoped>
.overview-page {
  width: 100%;
}

.page-title {
  position: relative;
  display: inline-block;
}

.title-text {
  background: linear-gradient(135deg, hsl(var(--foreground)) 0%, hsl(var(--foreground) / 0.7) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.title-glow {
  position: absolute;
  inset: -10px -20px;
  background: radial-gradient(ellipse at center, hsl(var(--primary) / 0.1) 0%, transparent 70%);
  pointer-events: none;
}

.error-alert {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1rem 1.25rem;
  background: linear-gradient(135deg, hsl(var(--destructive) / 0.1) 0%, hsl(var(--destructive) / 0.05) 100%);
  border: 1px solid hsl(var(--destructive) / 0.3);
  border-radius: var(--radius-lg);
  margin-bottom: 1rem;
}

.error-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: hsl(var(--destructive) / 0.1);
  border-radius: var(--radius);
  flex-shrink: 0;
}

.error-icon svg {
  width: 20px;
  height: 20px;
  color: hsl(var(--destructive));
}

.error-content h4 {
  font-size: 0.875rem;
  font-weight: 600;
  margin: 0 0 0.25rem 0;
  color: hsl(var(--destructive));
}

.error-content p {
  font-size: 0.8125rem;
  margin: 0;
  color: hsl(var(--muted-foreground));
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  margin-bottom: 0;
}

.stat-card {
  padding: 0;
}

.stat-content {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1.5rem;
}

.stat-icon {
  width: 48px;
  height: 48px;
}

.stat-icon svg {
  width: 24px;
  height: 24px;
}

.stat-info {
  flex: 1;
  min-width: 0;
}

.stat-label {
  display: block;
  font-size: 0.8125rem;
  color: hsl(var(--muted-foreground));
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.stat-value {
  display: flex;
  align-items: baseline;
  gap: 0.25rem;
}

.stat-number {
  font-size: 2rem;
  font-weight: 700;
  color: hsl(var(--foreground));
  letter-spacing: -0.02em;
}

.stat-total {
  font-size: 1rem;
  color: hsl(var(--muted-foreground));
}

.stat-model {
  font-size: 1.125rem;
  font-weight: 600;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

.stat-skeleton {
  margin-top: 0.25rem;
}

.stat-meta {
  display: flex;
  gap: 2rem;
  padding: 1rem 1.5rem;
  background: hsl(var(--muted) / 0.3);
  border-top: 1px solid hsl(var(--border));
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.meta-label {
  font-size: 0.75rem;
  color: hsl(var(--muted-foreground));
  font-weight: 500;
}

.meta-value {
  font-size: 0.875rem;
  font-weight: 500;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

.channels-section,
.quick-actions-section {
  margin-top: 1.5rem;
}

.channels-skeleton {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}

.channel-skeleton-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: hsl(var(--muted) / 0.3);
  border-radius: var(--radius);
}

.skeleton-text {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.channels-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}

.channel-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.25rem;
  background: hsl(var(--muted) / 0.3);
  border-radius: var(--radius);
  border: 1px solid transparent;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.channel-glow {
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 30% 50%, hsl(var(--primary) / 0.1) 0%, transparent 50%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.channel-card:hover {
  background: hsl(var(--muted) / 0.5);
  border-color: hsl(var(--border));
  transform: translateY(-2px);
}

.channel-card:hover .channel-glow {
  opacity: 1;
}

.channel-card.active {
  background: linear-gradient(135deg, hsl(var(--chart-2) / 0.08) 0%, hsl(var(--chart-2) / 0.04) 100%);
  border-color: hsl(var(--chart-2) / 0.3);
}

.channel-card.active .channel-glow {
  background: radial-gradient(circle at 30% 50%, hsl(var(--chart-2) / 0.15) 0%, transparent 50%);
  opacity: 1;
}

.channel-icon {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: hsl(var(--muted) / 0.5);
  border-radius: var(--radius);
  flex-shrink: 0;
  position: relative;
  z-index: 1;
}

.channel-icon svg {
  width: 22px;
  height: 22px;
  color: hsl(var(--primary));
}

.channel-info {
  flex: 1;
  min-width: 0;
  position: relative;
  z-index: 1;
}

.channel-name {
  font-size: 0.9375rem;
  font-weight: 600;
  margin: 0 0 0.375rem 0;
}

.channel-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8125rem;
  color: hsl(var(--muted-foreground));
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: hsl(var(--destructive));
  box-shadow: 0 0 8px hsl(var(--destructive) / 0.5);
}

.status-dot.active {
  background: hsl(var(--chart-2));
  box-shadow: 0 0 8px hsl(var(--chart-2) / 0.5);
  animation: dot-pulse 2s ease-in-out infinite;
}

@keyframes dot-pulse {
  0%, 100% { 
    box-shadow: 0 0 8px hsl(var(--chart-2) / 0.5);
    transform: scale(1);
  }
  50% { 
    box-shadow: 0 0 12px hsl(var(--chart-2) / 0.8);
    transform: scale(1.2);
  }
}

.channel-connection {
  flex-shrink: 0;
  position: relative;
  z-index: 1;
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
}

.quick-action {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.25rem;
  background: hsl(var(--muted) / 0.3);
  border-radius: var(--radius);
  border: 1px solid transparent;
  text-decoration: none;
  color: inherit;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.action-glow {
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 30% 50%, hsl(var(--primary) / 0.1) 0%, transparent 50%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.quick-action:hover {
  background: hsl(var(--muted) / 0.5);
  border-color: hsl(var(--border));
  transform: translateY(-2px);
}

.quick-action:hover .action-glow {
  opacity: 1;
}

.action-icon {
  flex-shrink: 0;
  position: relative;
  z-index: 1;
}

.action-content {
  flex: 1;
  min-width: 0;
  position: relative;
  z-index: 1;
}

.action-content h4 {
  font-size: 0.9375rem;
  font-weight: 600;
  margin: 0 0 0.25rem 0;
}

.action-content p {
  font-size: 0.8125rem;
  color: hsl(var(--muted-foreground));
  margin: 0;
}

.action-arrow {
  width: 1rem;
  height: 1rem;
  color: hsl(var(--muted-foreground));
  flex-shrink: 0;
  transition: transform 0.2s, color 0.2s;
  position: relative;
  z-index: 1;
}

.quick-action:hover .action-arrow {
  transform: translateX(4px);
  color: hsl(var(--primary));
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

@media (max-width: 1280px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 1024px) {
  .channels-grid,
  .quick-actions {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .channels-grid,
  .quick-actions {
    grid-template-columns: 1fr;
  }
  
  .page-header {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }
}
</style>
