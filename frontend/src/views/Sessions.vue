<script setup lang="ts">
/**
 * Sessions 会话管理页面
 * 显示和管理所有会话记录
 * 使用科技感组件优化视觉效果
 */
import { ref, onMounted, computed } from 'vue'
import { sessionsApi, type Session } from '@/api/sessions'
import { Card, Button, Badge, Modal, Input, Select, Empty, Skeleton, GlowCard, AnimatedList, AnimatedListItem } from '@/components/ui'
import { useToast } from '@/composables/useToast'

const toast = useToast()

const sessions = ref<Session[]>([])
const loading = ref(false)
const searchQuery = ref('')
const selectedChannel = ref('')
const currentPage = ref(1)
const pageSize = 20
const total = ref(0)

const showDetailModal = ref(false)
const selectedSession = ref<Session | null>(null)
const listVisible = ref(false)

const totalPages = computed(() => Math.ceil(total.value / pageSize))

const channelOptions = computed(() => {
  const channels = new Set(sessions.value.map(s => s.channel))
  const options = [{ value: '', label: '全部通道' }]
  channels.forEach(c => {
    if (c) options.push({ value: c, label: c })
  })
  return options
})

onMounted(async () => {
  await loadSessions()
  setTimeout(() => {
    listVisible.value = true
  }, 100)
})

async function loadSessions() {
  loading.value = true
  try {
    const result = await sessionsApi.list({
      query: searchQuery.value || undefined,
      channel: selectedChannel.value || undefined,
      limit: pageSize,
      offset: (currentPage.value - 1) * pageSize,
    })
    sessions.value = result.sessions
    total.value = result.total
  } catch (error) {
    toast.error('加载会话失败')
  } finally {
    loading.value = false
  }
}

async function deleteSession(id: string) {
  if (!confirm('确定要删除这个会话吗？')) return
  
  try {
    await sessionsApi.delete(id)
    toast.success('会话已删除')
    await loadSessions()
  } catch (error) {
    toast.error('删除失败')
  }
}

function viewSessionDetail(session: Session) {
  selectedSession.value = session
  showDetailModal.value = true
}

async function prevPage() {
  if (currentPage.value > 1) {
    currentPage.value--
    await loadSessions()
  }
}

async function nextPage() {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
    await loadSessions()
  }
}

function getChannelIcon(channel: string): string {
  const icons: Record<string, string> = {
    web: 'M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9',
    qq: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z',
    wechat: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z',
  }
  return icons[channel] || icons.web
}

function getChannelLabel(channel: string): string {
  const labels: Record<string, string> = {
    web: 'Web',
    qq: 'QQ',
    wechat: '企业微信',
  }
  return labels[channel] || channel
}

function getChannelColor(channel: string): string {
  const colors: Record<string, string> = {
    web: 'rgba(59, 130, 246, 0.4)',
    qq: 'rgba(0, 170, 255, 0.4)',
    wechat: 'rgba(16, 185, 129, 0.4)',
  }
  return colors[channel] || 'rgba(59, 130, 246, 0.4)'
}

function formatTime(timestamp: string): string {
  if (!timestamp) return '-'
  return new Date(timestamp).toLocaleString('zh-CN')
}

function truncateText(text: string, maxLength: number = 100): string {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength) + '...'
}
</script>

<template>
  <div class="sessions-page page-container">
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          <span class="title-text">会话管理</span>
          <span class="title-glow" />
        </h1>
        <p class="page-subtitle">查看和管理所有对话会话</p>
      </div>
      <Button variant="secondary" :loading="loading" @click="loadSessions">
        <svg class="icon" :class="{ spinning: loading }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        刷新
      </Button>
    </div>

    <div class="toolbar">
      <div class="search-filters">
        <div class="search-box">
          <svg class="search-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            v-model="searchQuery"
            type="text"
            class="search-input"
            placeholder="搜索会话..."
            @keyup.enter="loadSessions"
          />
        </div>
        <Select
          v-model="selectedChannel"
          :options="channelOptions"
          placeholder="选择通道"
          @update:model-value="loadSessions"
        />
      </div>
      <div class="stats-info">
        <span class="stats-value">{{ total }}</span>
        <span class="stats-label">个会话</span>
      </div>
    </div>

    <div v-if="loading && sessions.length === 0" class="loading-skeleton">
      <div v-for="i in 5" :key="i" class="skeleton-card">
        <div class="skeleton-header">
          <Skeleton width="44px" height="44px" radius="var(--radius)" />
          <div class="skeleton-info">
            <Skeleton width="120px" height="1rem" />
            <Skeleton width="200px" height="0.75rem" />
          </div>
        </div>
        <Skeleton :rows="2" />
      </div>
    </div>

    <Empty
      v-else-if="sessions.length === 0"
      icon="folder"
      title="暂无会话"
      :description="searchQuery ? '没有匹配的会话' : '还没有任何会话记录'"
    />

    <AnimatedList v-else class="sessions-list" :visible="listVisible" :stagger="60">
      <AnimatedListItem v-for="(session, index) in sessions" :key="session.id" :index="index" :visible="listVisible">
        <GlowCard class="session-card" :glow-color="getChannelColor(session.channel)" hover-glow>
          <div class="session-header" @click="viewSessionDetail(session)">
            <div class="session-icon" :class="`icon-${session.channel}`">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="getChannelIcon(session.channel)" />
              </svg>
            </div>
            <div class="session-info">
              <div class="session-title-row">
                <code class="session-id">{{ session.id.slice(0, 8) }}</code>
                <Badge :variant="session.channel === 'web' ? 'primary' : 'success'" size="sm">
                  {{ getChannelLabel(session.channel) }}
                </Badge>
              </div>
              <p class="session-preview">{{ truncateText(session.last_message || '暂无消息') }}</p>
            </div>
            <div class="session-meta">
              <span class="meta-time">{{ formatTime(session.updated_at || session.created_at) }}</span>
              <span class="meta-count">{{ session.message_count || 0 }} 条消息</span>
            </div>
          </div>
          <div class="session-actions">
            <Button variant="ghost" size="sm" @click="viewSessionDetail(session)">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
              查看
            </Button>
            <Button variant="ghost" size="sm" @click="deleteSession(session.id)">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              删除
            </Button>
          </div>
        </GlowCard>
      </AnimatedListItem>
    </AnimatedList>

    <div v-if="totalPages > 1" class="pagination">
      <Button
        variant="secondary"
        size="sm"
        :disabled="currentPage === 1"
        @click="prevPage"
      >
        上一页
      </Button>
      <span class="page-info">{{ currentPage }} / {{ totalPages }}</span>
      <Button
        variant="secondary"
        size="sm"
        :disabled="currentPage === totalPages"
        @click="nextPage"
      >
        下一页
      </Button>
    </div>

    <Modal v-model="showDetailModal" title="会话详情" size="lg">
      <div v-if="selectedSession" class="session-detail">
        <div class="detail-header">
          <div class="detail-item">
            <span class="detail-label">会话 ID</span>
            <code class="detail-value">{{ selectedSession.id }}</code>
          </div>
          <div class="detail-item">
            <span class="detail-label">通道</span>
            <Badge :variant="selectedSession.channel === 'web' ? 'primary' : 'success'">
              {{ getChannelLabel(selectedSession.channel) }}
            </Badge>
          </div>
          <div class="detail-item">
            <span class="detail-label">消息数</span>
            <span class="detail-value">{{ selectedSession.message_count || 0 }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">创建时间</span>
            <span class="detail-value">{{ formatTime(selectedSession.created_at) }}</span>
          </div>
        </div>

        <div class="detail-content">
          <h4>最后消息</h4>
          <pre class="content-text">{{ selectedSession.last_message || '暂无消息' }}</pre>
        </div>
      </div>

      <template #footer>
        <Button variant="secondary" @click="showDetailModal = false">关闭</Button>
        <Button variant="danger" @click="deleteSession(selectedSession!.id); showDetailModal = false">
          删除
        </Button>
      </template>
    </Modal>
  </div>
</template>

<style scoped>
.sessions-page {
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

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.search-filters {
  display: flex;
  gap: 0.75rem;
  flex: 1;
}

.search-box {
  flex: 1;
  max-width: 400px;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 1rem;
  background: hsl(var(--background));
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius);
  transition: all 0.2s;
}

.search-box:focus-within {
  border-color: hsl(var(--primary));
  box-shadow: 0 0 0 3px hsl(var(--primary) / 0.1);
}

.search-icon {
  width: 1.125rem;
  height: 1.125rem;
  color: hsl(var(--muted-foreground));
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 0.875rem;
  color: hsl(var(--foreground));
  min-width: 0;
}

.search-input:focus {
  outline: none;
}

.search-input::placeholder {
  color: hsl(var(--muted-foreground));
}

.stats-info {
  display: flex;
  align-items: baseline;
  gap: 0.375rem;
  padding: 0.5rem 1rem;
  background: linear-gradient(135deg, hsl(var(--muted) / 0.3) 0%, hsl(var(--muted) / 0.1) 100%);
  border-radius: var(--radius);
}

.stats-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: hsl(var(--foreground));
}

.stats-label {
  font-size: 0.75rem;
  color: hsl(var(--muted-foreground));
}

.loading-skeleton {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.skeleton-card {
  background: hsl(var(--card));
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius-lg);
  padding: 1.25rem;
}

.skeleton-header {
  display: flex;
  gap: 1rem;
  margin-bottom: 0.75rem;
}

.skeleton-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.sessions-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.session-card {
  padding: 0;
}

.session-header {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1.25rem;
  cursor: pointer;
}

.session-icon {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius);
  flex-shrink: 0;
}

.session-icon svg {
  width: 22px;
  height: 22px;
}

.icon-web {
  background: hsl(var(--primary) / 0.1);
  color: hsl(var(--primary));
}

.icon-qq {
  background: hsl(200 100% 47% / 0.1);
  color: hsl(200 100% 47%);
}

.icon-wechat {
  background: hsl(var(--chart-2) / 0.1);
  color: hsl(var(--chart-2));
}

.session-info {
  flex: 1;
  min-width: 0;
}

.session-title-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.375rem;
}

.session-id {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.875rem;
  background: hsl(var(--muted) / 0.5);
  padding: 0.25rem 0.5rem;
  border-radius: var(--radius);
}

.session-preview {
  font-size: 0.8125rem;
  color: hsl(var(--muted-foreground));
  margin: 0;
  line-height: 1.4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.25rem;
  flex-shrink: 0;
}

.meta-time {
  font-size: 0.75rem;
  color: hsl(var(--muted-foreground));
}

.meta-count {
  font-size: 0.6875rem;
  color: hsl(var(--muted-foreground));
  background: hsl(var(--muted) / 0.5);
  padding: 0.125rem 0.5rem;
  border-radius: var(--radius);
}

.session-actions {
  display: flex;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  border-top: 1px solid hsl(var(--border));
  background: hsl(var(--muted) / 0.2);
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin-top: 1.5rem;
  padding: 1rem;
  background: linear-gradient(135deg, hsl(var(--muted) / 0.3) 0%, hsl(var(--muted) / 0.1) 100%);
  border-radius: var(--radius-lg);
}

.page-info {
  font-size: 0.875rem;
  color: hsl(var(--muted-foreground));
  font-weight: 500;
}

.session-detail {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.detail-header {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  padding: 1.25rem;
  background: linear-gradient(135deg, hsl(var(--muted) / 0.3) 0%, hsl(var(--muted) / 0.1) 100%);
  border-radius: var(--radius);
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.detail-label {
  font-size: 0.75rem;
  color: hsl(var(--muted-foreground));
  font-weight: 500;
}

.detail-value {
  font-size: 0.875rem;
  font-weight: 500;
}

.detail-content h4 {
  font-size: 0.875rem;
  font-weight: 600;
  margin: 0 0 0.5rem 0;
  color: hsl(var(--muted-foreground));
}

.content-text {
  margin: 0;
  padding: 1rem;
  background: linear-gradient(135deg, hsl(var(--muted) / 0.3) 0%, hsl(var(--muted) / 0.2) 100%);
  border-radius: var(--radius);
  font-size: 0.8125rem;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  overflow-x: auto;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
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
  .toolbar {
    flex-direction: column;
    align-items: stretch;
  }
  
  .search-filters {
    flex-direction: column;
  }
  
  .search-box {
    max-width: none;
  }
  
  .stats-info {
    justify-content: center;
  }
  
  .session-header {
    flex-direction: column;
  }
  
  .session-meta {
    flex-direction: row;
    align-items: center;
    width: 100%;
    justify-content: space-between;
  }
  
  .detail-header {
    grid-template-columns: 1fr;
  }
}
</style>
