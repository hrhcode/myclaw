<script setup lang="ts">
/**
 * 记忆管理页面
 * 提供记忆浏览、搜索和删除功能
 */
import { ref, onMounted, computed, watch } from 'vue'
import { memoriesApi, type Memory, type MemoryStats } from '@/api/settings'
import { get } from '@/utils/request'
import { Card, Button, Badge, Modal, Input, Select, Empty, Skeleton } from '@/components/ui'
import { useToast } from '@/composables/useToast'

const toast = useToast()

const memories = ref<Memory[]>([])
const stats = ref<MemoryStats | null>(null)
const sessions = ref<{ id: string; count: number }[]>([])
const loading = ref(false)
const searchQuery = ref('')
const selectedSession = ref('')
const currentPage = ref(1)
const pageSize = 20
const total = ref(0)

const showDetailModal = ref(false)
const selectedMemory = ref<Memory | null>(null)
const showClearConfirm = ref(false)

const totalPages = computed(() => Math.ceil(total.value / pageSize))

const sessionOptions = computed(() => {
  const options = [{ value: '', label: '全部会话' }]
  for (const s of sessions.value) {
    options.push({ value: s.id, label: `${s.id.slice(0, 8)}... (${s.count})` })
  }
  return options
})

onMounted(async () => {
  await Promise.all([loadMemories(), loadStats(), loadSessions()])
})

watch([searchQuery, selectedSession], () => {
  currentPage.value = 1
  loadMemories()
})

async function loadMemories() {
  loading.value = true
  try {
    const result = await memoriesApi.list({
      query: searchQuery.value || undefined,
      session_id: selectedSession.value || undefined,
      limit: pageSize,
      offset: (currentPage.value - 1) * pageSize,
    })
    memories.value = result.memories
    total.value = result.total
  } catch (error) {
    toast.error('加载记忆失败')
  } finally {
    loading.value = false
  }
}

async function loadStats() {
  try {
    stats.value = await memoriesApi.stats()
  } catch (error) {
    console.error('加载统计失败:', error)
  }
}

async function loadSessions() {
  try {
    const result = await get('/api/sessions?limit=100')
    sessions.value = (result.sessions || []).map((s: any) => ({
      id: s.id,
      count: s.message_count || 0,
    }))
  } catch (error) {
    console.error('加载会话列表失败:', error)
  }
}

async function deleteMemory(id: number) {
  if (!confirm('确定要删除这条记忆吗？')) return
  
  try {
    await memoriesApi.delete(id)
    toast.success('记忆已删除')
    await Promise.all([loadMemories(), loadStats()])
  } catch (error) {
    toast.error('删除失败')
  }
}

async function clearAllMemories() {
  try {
    await memoriesApi.clearAll()
    toast.success('所有记忆已清空')
    showClearConfirm.value = false
    await Promise.all([loadMemories(), loadStats(), loadSessions()])
  } catch (error) {
    toast.error('清空失败')
  }
}

function viewMemoryDetail(memory: Memory) {
  selectedMemory.value = memory
  showDetailModal.value = true
}

async function prevPage() {
  if (currentPage.value > 1) {
    currentPage.value--
    await loadMemories()
  }
}

async function nextPage() {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
    await loadMemories()
  }
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

function formatTime(timestamp: string): string {
  if (!timestamp) return '-'
  return new Date(timestamp).toLocaleString('zh-CN')
}

function truncateContent(content: string, maxLength: number = 200): string {
  if (!content) return ''
  if (content.length <= maxLength) return content
  return content.slice(0, maxLength) + '...'
}
</script>

<template>
  <div class="memories-page">
    <div class="page-header">
      <div class="header-content">
        <h1>记忆管理</h1>
        <p class="header-subtitle">浏览和搜索对话记忆</p>
      </div>
      <div v-if="stats" class="header-stats">
        <div class="stat-item">
          <span class="stat-value">{{ stats.total_messages }}</span>
          <span class="stat-label">条记忆</span>
        </div>
        <div class="stat-item">
          <span class="stat-value">{{ stats.total_sessions }}</span>
          <span class="stat-label">个会话</span>
        </div>
      </div>
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
            placeholder="搜索记忆内容..."
          />
        </div>
        <Select
          v-model="selectedSession"
          :options="sessionOptions"
          placeholder="选择会话"
        />
      </div>
      <Button variant="danger" size="sm" @click="showClearConfirm = true">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
        </svg>
        清空所有
      </Button>
    </div>

    <div v-if="loading && memories.length === 0" class="loading-skeleton">
      <div v-for="i in 5" :key="i" class="skeleton-card">
        <div class="skeleton-header">
          <Skeleton width="60px" height="1.5rem" />
          <Skeleton width="100px" height="0.75rem" />
          <Skeleton width="140px" height="0.75rem" />
        </div>
        <Skeleton :rows="2" />
      </div>
    </div>

    <Empty
      v-else-if="memories.length === 0"
      icon="folder"
      title="暂无记忆"
      :description="searchQuery ? '没有匹配的记忆' : '还没有任何记忆记录'"
    />

    <div v-else class="memories-list">
      <Card
        v-for="memory in memories"
        :key="memory.id"
        class="memory-card"
        @click="viewMemoryDetail(memory)"
      >
        <div class="memory-header">
          <Badge :variant="getRoleVariant(memory.role)" size="sm">
            {{ getRoleLabel(memory.role) }}
          </Badge>
          <code class="memory-session">{{ memory.session_id?.slice(0, 8) }}</code>
          <span class="memory-time">{{ formatTime(memory.timestamp) }}</span>
          <Button
            variant="ghost"
            size="sm"
            @click.stop="deleteMemory(memory.id)"
          >
            删除
          </Button>
        </div>
        <div class="memory-content">
          {{ truncateContent(memory.content) }}
        </div>
        <div v-if="memory.tool_calls && memory.tool_calls.length > 0" class="memory-tools">
          <Badge variant="warning" size="sm">工具调用: {{ memory.tool_calls.length }}</Badge>
        </div>
      </Card>
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

    <Modal v-model="showDetailModal" title="记忆详情" size="lg">
      <div v-if="selectedMemory" class="memory-detail">
        <div class="detail-header">
          <div class="detail-item">
            <span class="detail-label">角色</span>
            <Badge :variant="getRoleVariant(selectedMemory.role)">
              {{ getRoleLabel(selectedMemory.role) }}
            </Badge>
          </div>
          <div class="detail-item">
            <span class="detail-label">会话 ID</span>
            <code class="detail-value">{{ selectedMemory.session_id }}</code>
          </div>
          <div class="detail-item">
            <span class="detail-label">时间</span>
            <span class="detail-value">{{ formatTime(selectedMemory.timestamp) }}</span>
          </div>
          <div v-if="selectedMemory.tool_call_id" class="detail-item">
            <span class="detail-label">工具调用 ID</span>
            <code class="detail-value">{{ selectedMemory.tool_call_id }}</code>
          </div>
        </div>

        <div class="detail-content">
          <h4>内容</h4>
          <pre class="content-text">{{ selectedMemory.content }}</pre>
        </div>

        <div v-if="selectedMemory.tool_calls && selectedMemory.tool_calls.length > 0" class="detail-tools">
          <h4>工具调用</h4>
          <pre class="tools-json">{{ JSON.stringify(selectedMemory.tool_calls, null, 2) }}</pre>
        </div>
      </div>

      <template #footer>
        <Button variant="secondary" @click="showDetailModal = false">关闭</Button>
        <Button variant="danger" @click="deleteMemory(selectedMemory!.id); showDetailModal = false">
          删除
        </Button>
      </template>
    </Modal>

    <Modal v-model="showClearConfirm" title="确认清空" size="sm">
      <p class="confirm-text">确定要清空所有记忆吗？此操作不可恢复！</p>
      <template #footer>
        <Button variant="secondary" @click="showClearConfirm = false">取消</Button>
        <Button variant="danger" @click="clearAllMemories">确认清空</Button>
      </template>
    </Modal>
  </div>
</template>

<style scoped>
.memories-page {
  max-width: 900px;
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

.header-stats {
  display: flex;
  gap: 1.5rem;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: hsl(var(--primary));
}

.stat-label {
  font-size: 0.75rem;
  color: hsl(var(--muted-foreground));
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
  max-width: 300px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: hsl(var(--background));
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius);
}

.search-icon {
  width: 1rem;
  height: 1rem;
  color: hsl(var(--muted-foreground));
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 0.875rem;
  color: hsl(var(--foreground));
}

.search-input:focus {
  outline: none;
}

.loading-skeleton {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.skeleton-card {
  background: hsl(var(--card));
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius);
  padding: 1rem;
}

.skeleton-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.memories-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.memory-card {
  padding: 1rem;
  cursor: pointer;
  transition: all 0.2s;
}

.memory-card:hover {
  border-color: hsl(var(--primary) / 0.3);
}

.memory-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.memory-session {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.75rem;
  background: hsl(var(--muted) / 0.5);
  padding: 0.125rem 0.5rem;
  border-radius: var(--radius);
}

.memory-time {
  font-size: 0.75rem;
  color: hsl(var(--muted-foreground));
  margin-left: auto;
}

.memory-content {
  font-size: 0.875rem;
  line-height: 1.5;
  color: hsl(var(--foreground));
  white-space: pre-wrap;
  word-break: break-word;
}

.memory-tools {
  margin-top: 0.5rem;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin-top: 1.5rem;
}

.page-info {
  font-size: 0.875rem;
  color: hsl(var(--muted-foreground));
}

.memory-detail {
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

.detail-content h4,
.detail-tools h4 {
  font-size: 0.875rem;
  font-weight: 600;
  margin: 0 0 0.5rem 0;
  color: hsl(var(--muted-foreground));
}

.content-text,
.tools-json {
  margin: 0;
  padding: 1rem;
  background: hsl(var(--muted) / 0.3);
  border-radius: var(--radius);
  font-size: 0.8125rem;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  overflow-x: auto;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

.confirm-text {
  margin: 0;
  color: hsl(var(--muted-foreground));
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 1rem;
  }
  
  .header-stats {
    width: 100%;
    justify-content: flex-start;
  }
  
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
  
  .detail-header {
    grid-template-columns: 1fr;
  }
}
</style>
