<script setup lang="ts">
/**
 * Sessions 会话管理页面
 * 显示和管理所有会话
 */
import { ref, computed, onMounted, watch } from 'vue'
import { get, del } from '@/utils/request'
import { Card, Button, Badge, Modal, Select, Empty, Skeleton } from '@/components/ui'
import { useToast } from '@/composables/useToast'

interface SessionInfo {
  id: string
  channel: string
  message_count: number
  created_at: string
  updated_at: string
}

interface Message {
  id: number
  role: string
  content: string
  timestamp: string
  tool_calls: any[] | null
}

const toast = useToast()

const sessions = ref<SessionInfo[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const total = ref(0)
const currentPage = ref(1)
const pageSize = 20

const filters = ref({
  channel: '',
})

const selectedSession = ref<SessionInfo | null>(null)
const sessionMessages = ref<Message[]>([])
const messagesLoading = ref(false)
const showDetailModal = ref(false)

const totalPages = computed(() => Math.ceil(total.value / pageSize))

const channelOptions = [
  { value: '', label: '全部通道' },
  { value: 'web', label: 'Web' },
  { value: 'qq', label: 'QQ' },
  { value: 'wechat', label: '企业微信' },
]

onMounted(async () => {
  await loadSessions()
})

watch(filters, () => {
  currentPage.value = 1
  loadSessions()
}, { deep: true })

async function loadSessions() {
  loading.value = true
  error.value = null
  
  try {
    const params = new URLSearchParams()
    params.set('limit', pageSize.toString())
    params.set('offset', ((currentPage.value - 1) * pageSize).toString())
    if (filters.value.channel) {
      params.set('channel', filters.value.channel)
    }
    
    const result = await get(`/api/sessions?${params.toString()}`)
    sessions.value = result.sessions || []
    total.value = result.total || 0
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

async function loadSessionMessages(sessionId: string) {
  messagesLoading.value = true
  
  try {
    const result = await get(`/v1/sessions/${sessionId}/messages?limit=50`)
    sessionMessages.value = result.messages || []
  } catch (e) {
    toast.error('加载消息失败')
    sessionMessages.value = []
  } finally {
    messagesLoading.value = false
  }
}

async function deleteSession(sessionId: string) {
  if (!confirm('确定要删除这个会话吗？')) return
  
  try {
    await del(`/api/sessions/${sessionId}`)
    toast.success('会话已删除')
    await loadSessions()
  } catch (e) {
    toast.error('删除失败')
  }
}

function viewSessionDetail(session: SessionInfo) {
  selectedSession.value = session
  showDetailModal.value = true
  loadSessionMessages(session.id)
}

function formatTime(time: string): string {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

function truncateId(id: string): string {
  if (id.length > 20) {
    return id.substring(0, 20) + '...'
  }
  return id
}

function truncateContent(content: string, maxLength: number = 100): string {
  if (!content) return ''
  if (content.length <= maxLength) return content
  return content.slice(0, maxLength) + '...'
}

function getRoleLabel(role: string): string {
  const labels: Record<string, string> = {
    user: '用户',
    assistant: 'AI',
    system: '系统',
    tool: '工具',
  }
  return labels[role] || role
}

function getRoleVariant(role: string): 'default' | 'primary' | 'success' | 'warning' {
  const variants: Record<string, 'default' | 'primary' | 'success' | 'warning'> = {
    user: 'primary',
    assistant: 'success',
    system: 'default',
    tool: 'warning',
  }
  return variants[role] || 'default'
}

function getChannelVariant(channel: string): 'default' | 'primary' | 'success' | 'warning' {
  const variants: Record<string, 'default' | 'primary' | 'success' | 'warning'> = {
    web: 'primary',
    qq: 'success',
    wechat: 'warning',
  }
  return variants[channel] || 'default'
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
</script>

<template>
  <div class="sessions-page">
    <div class="page-header">
      <div class="header-content">
        <h1>会话管理</h1>
        <p class="header-subtitle">查看和管理所有对话会话</p>
      </div>
      <Button variant="secondary" :loading="loading" @click="loadSessions">
        <svg class="icon" :class="{ spinning: loading }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        刷新
      </Button>
    </div>

    <div class="filters-bar">
      <div class="filter-item">
        <label class="filter-label">通道筛选</label>
        <Select
          v-model="filters.channel"
          :options="channelOptions"
          placeholder="选择通道"
        />
      </div>
      <div class="filter-stats">
        <span class="stats-text">共 {{ total }} 个会话</span>
      </div>
    </div>

    <div v-if="error" class="error-message">
      <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <span>{{ error }}</span>
    </div>

    <Card no-padding>
      <div v-if="loading && sessions.length === 0" class="loading-skeleton">
        <div v-for="i in 5" :key="i" class="skeleton-row">
          <Skeleton width="200px" height="1rem" />
          <Skeleton width="60px" height="1.5rem" />
          <Skeleton width="40px" height="1rem" />
          <Skeleton width="140px" height="1rem" />
          <Skeleton width="80px" height="2rem" />
        </div>
      </div>

      <Empty
        v-else-if="sessions.length === 0"
        icon="chat"
        title="暂无会话"
        description="还没有任何会话记录"
      />

      <template v-else>
        <div class="table-header">
          <div class="col col-id">会话 ID</div>
          <div class="col col-channel">通道</div>
          <div class="col col-count">消息数</div>
          <div class="col col-time">更新时间</div>
          <div class="col col-actions">操作</div>
        </div>

        <div class="table-body">
          <div
            v-for="session in sessions"
            :key="session.id"
            class="table-row"
          >
            <div class="col col-id">
              <code class="session-id" :title="session.id">{{ truncateId(session.id) }}</code>
            </div>
            <div class="col col-channel">
              <Badge :variant="getChannelVariant(session.channel)" size="sm">
                {{ session.channel }}
              </Badge>
            </div>
            <div class="col col-count">
              <span class="count-value">{{ session.message_count }}</span>
            </div>
            <div class="col col-time">
              <span class="time-value">{{ formatTime(session.updated_at) }}</span>
            </div>
            <div class="col col-actions">
              <Button variant="ghost" size="sm" @click="viewSessionDetail(session)">
                查看
              </Button>
              <Button variant="danger" size="sm" @click="deleteSession(session.id)">
                删除
              </Button>
            </div>
          </div>
        </div>

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
      </template>
    </Card>

    <Modal v-model="showDetailModal" title="会话详情" size="lg">
      <div v-if="selectedSession" class="session-detail">
        <div class="detail-header">
          <div class="detail-item">
            <span class="detail-label">会话 ID</span>
            <code class="detail-value">{{ selectedSession.id }}</code>
          </div>
          <div class="detail-item">
            <span class="detail-label">通道</span>
            <Badge :variant="getChannelVariant(selectedSession.channel)">
              {{ selectedSession.channel }}
            </Badge>
          </div>
          <div class="detail-item">
            <span class="detail-label">消息数</span>
            <span class="detail-value">{{ selectedSession.message_count }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">创建时间</span>
            <span class="detail-value">{{ formatTime(selectedSession.created_at) }}</span>
          </div>
        </div>

        <div class="messages-section">
          <h4>消息记录</h4>
          
          <div v-if="messagesLoading" class="messages-loading">
            <Skeleton :rows="3" />
          </div>
          
          <div v-else-if="sessionMessages.length === 0" class="messages-empty">
            暂无消息记录
          </div>
          
          <div v-else class="messages-list">
            <div
              v-for="msg in sessionMessages"
              :key="msg.id"
              class="message-item"
            >
              <div class="message-header">
                <Badge :variant="getRoleVariant(msg.role)" size="sm">
                  {{ getRoleLabel(msg.role) }}
                </Badge>
                <span class="message-time">{{ formatTime(msg.timestamp) }}</span>
              </div>
              <div class="message-content">
                {{ truncateContent(msg.content, 300) }}
              </div>
              <div v-if="msg.tool_calls && msg.tool_calls.length > 0" class="message-tools">
                <Badge variant="warning" size="sm">工具调用: {{ msg.tool_calls.length }}</Badge>
              </div>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <Button variant="secondary" @click="showDetailModal = false">关闭</Button>
      </template>
    </Modal>
  </div>
</template>

<style scoped>
.sessions-page {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
}

.header-content h1 {
  font-size: 1.75rem;
  font-weight: 800;
  margin: 0;
}

.header-subtitle {
  font-size: 0.875rem;
  color: hsl(var(--muted-foreground));
  margin: 0.25rem 0 0 0;
}

.filters-bar {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 1rem;
  gap: 1rem;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.filter-label {
  font-size: 0.75rem;
  color: hsl(var(--muted-foreground));
}

.filter-stats {
  display: flex;
  align-items: center;
}

.stats-text {
  font-size: 0.875rem;
  color: hsl(var(--muted-foreground));
}

.error-message {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem;
  background: hsl(var(--destructive) / 0.1);
  border: 1px solid hsl(var(--destructive));
  border-radius: var(--radius);
  color: hsl(var(--destructive));
  margin-bottom: 1rem;
}

.error-message svg {
  width: 1.25rem;
  height: 1.25rem;
  flex-shrink: 0;
}

.loading-skeleton {
  padding: 1rem;
}

.skeleton-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 0;
  border-bottom: 1px solid hsl(var(--border));
}

.skeleton-row:last-child {
  border-bottom: none;
}

.table-header {
  display: grid;
  grid-template-columns: 1fr 100px 80px 160px 140px;
  gap: 1rem;
  padding: 0.75rem 1.25rem;
  background: hsl(var(--muted) / 0.5);
  font-size: 0.75rem;
  font-weight: 600;
  color: hsl(var(--muted-foreground));
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.table-body {
  max-height: 600px;
  overflow-y: auto;
}

.table-row {
  display: grid;
  grid-template-columns: 1fr 100px 80px 160px 140px;
  gap: 1rem;
  padding: 0.75rem 1.25rem;
  border-bottom: 1px solid hsl(var(--border));
  align-items: center;
  transition: background 0.2s;
}

.table-row:last-child {
  border-bottom: none;
}

.table-row:hover {
  background: hsl(var(--muted) / 0.3);
}

.col {
  font-size: 0.875rem;
}

.col-id {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-id {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.8125rem;
  background: hsl(var(--muted) / 0.5);
  padding: 0.25rem 0.5rem;
  border-radius: var(--radius);
}

.count-value {
  font-weight: 600;
}

.time-value {
  font-size: 0.8125rem;
  color: hsl(var(--muted-foreground));
}

.col-actions {
  display: flex;
  gap: 0.5rem;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.25rem;
  border-top: 1px solid hsl(var(--border));
}

.page-info {
  font-size: 0.875rem;
  color: hsl(var(--muted-foreground));
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
  padding: 1rem;
  background: hsl(var(--muted) / 0.3);
  border-radius: var(--radius);
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.detail-label {
  font-size: 0.75rem;
  color: hsl(var(--muted-foreground));
}

.detail-value {
  font-size: 0.875rem;
  font-weight: 500;
}

.messages-section h4 {
  font-size: 0.875rem;
  font-weight: 600;
  margin: 0 0 0.75rem 0;
  color: hsl(var(--muted-foreground));
}

.messages-loading {
  padding: 1rem;
}

.messages-empty {
  text-align: center;
  padding: 2rem;
  color: hsl(var(--muted-foreground));
}

.messages-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-height: 400px;
  overflow-y: auto;
}

.message-item {
  padding: 0.75rem;
  background: hsl(var(--muted) / 0.3);
  border-radius: var(--radius);
}

.message-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.message-time {
  font-size: 0.6875rem;
  color: hsl(var(--muted-foreground));
}

.message-content {
  font-size: 0.8125rem;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

.message-tools {
  margin-top: 0.5rem;
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
  .table-header,
  .table-row {
    grid-template-columns: 1fr 80px 80px;
  }
  
  .col-time {
    display: none;
  }
  
  .filters-bar {
    flex-direction: column;
    align-items: stretch;
  }
  
  .detail-header {
    grid-template-columns: 1fr;
  }
}
</style>
