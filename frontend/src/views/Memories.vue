<script setup lang="ts">
/**
 * 记忆管理页面
 * 提供记忆浏览、搜索和删除功能
 */
import { ref, onMounted, computed } from 'vue'
import { memoriesApi, type Memory, type MemoryStats } from '@/api/settings'

const memories = ref<Memory[]>([])
const stats = ref<MemoryStats | null>(null)
const loading = ref(false)
const searchQuery = ref('')
const selectedSession = ref('')
const currentPage = ref(1)
const pageSize = 20
const total = ref(0)
const message = ref<{ type: 'success' | 'error'; text: string } | null>(null)
const showClearConfirm = ref(false)

const totalPages = computed(() => Math.ceil(total.value / pageSize))

onMounted(async () => {
  await Promise.all([loadMemories(), loadStats()])
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
    showMessage('error', '加载记忆失败')
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

async function search() {
  currentPage.value = 1
  await loadMemories()
}

async function deleteMemory(id: number) {
  if (!confirm('确定要删除这条记忆吗？')) return
  
  try {
    await memoriesApi.delete(id)
    showMessage('success', '记忆已删除')
    await Promise.all([loadMemories(), loadStats()])
  } catch (error) {
    showMessage('error', '删除失败')
  }
}

async function clearAllMemories() {
  if (!confirm('确定要清空所有记忆吗？此操作不可恢复！')) return
  
  try {
    await memoriesApi.clearAll()
    showMessage('success', '所有记忆已清空')
    showClearConfirm.value = false
    await Promise.all([loadMemories(), loadStats()])
  } catch (error) {
    showMessage('error', '清空失败')
  }
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

function getRoleClass(role: string): string {
  return `role-${role}`
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

function showMessage(type: 'success' | 'error', text: string) {
  message.value = { type, text }
  setTimeout(() => {
    message.value = null
  }, 3000)
}
</script>

<template>
  <div class="memories-page">
    <div class="page-header">
      <h1>记忆管理</h1>
      <div class="header-stats" v-if="stats">
        <span class="stat">
          <span class="stat-value">{{ stats.total_messages }}</span>
          <span class="stat-label">条记忆</span>
        </span>
        <span class="stat">
          <span class="stat-value">{{ stats.total_sessions }}</span>
          <span class="stat-label">个会话</span>
        </span>
      </div>
    </div>

    <div v-if="message" class="message" :class="message.type">
      {{ message.text }}
    </div>

    <div class="search-bar">
      <input 
        v-model="searchQuery" 
        type="text" 
        class="form-control" 
        placeholder="搜索记忆..."
        @keyup.enter="search"
      />
      <button @click="search" class="btn btn-primary">搜索</button>
      <button @click="showClearConfirm = true" class="btn btn-danger">
        清空所有
      </button>
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else class="memories-content">
      <div v-if="memories.length === 0" class="empty-state">
        <p>暂无记忆</p>
      </div>

      <div v-else class="memories-list">
        <div 
          v-for="memory in memories" 
          :key="memory.id" 
          class="memory-card"
        >
          <div class="memory-header">
            <span class="memory-role" :class="getRoleClass(memory.role)">
              {{ getRoleLabel(memory.role) }}
            </span>
            <span class="memory-session">{{ memory.session_id?.slice(0, 8) }}</span>
            <span class="memory-time">{{ formatTime(memory.timestamp) }}</span>
            <button 
              @click="deleteMemory(memory.id)" 
              class="btn btn-icon btn-danger"
              title="删除"
            >
              删除
            </button>
          </div>
          <div class="memory-content">
            {{ truncateContent(memory.content) }}
          </div>
          <div v-if="memory.tool_calls" class="memory-tools">
            <span class="tool-badge">工具调用</span>
          </div>
        </div>
      </div>

      <div v-if="totalPages > 1" class="pagination">
        <button 
          @click="prevPage" 
          class="btn btn-secondary" 
          :disabled="currentPage === 1"
        >
          上一页
        </button>
        <span class="page-info">
          {{ currentPage }} / {{ totalPages }}
        </span>
        <button 
          @click="nextPage" 
          class="btn btn-secondary" 
          :disabled="currentPage === totalPages"
        >
          下一页
        </button>
      </div>
    </div>

    <div v-if="showClearConfirm" class="modal-overlay" @click="showClearConfirm = false">
      <div class="modal" @click.stop>
        <h3>确认清空</h3>
        <p>确定要清空所有记忆吗？此操作不可恢复！</p>
        <div class="modal-actions">
          <button @click="showClearConfirm = false" class="btn btn-secondary">
            取消
          </button>
          <button @click="clearAllMemories" class="btn btn-danger">
            确认清空
          </button>
        </div>
      </div>
    </div>
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
  align-items: center;
  margin-bottom: 1.5rem;
}

.page-header h1 {
  font-size: 1.75rem;
  font-weight: 800;
  margin: 0;
}

.header-stats {
  display: flex;
  gap: 1.5rem;
}

.stat {
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

.message {
  padding: 0.75rem 1rem;
  border-radius: var(--radius);
  margin-bottom: 1rem;
}

.message.success {
  background: hsl(var(--chart-2) / 0.1);
  color: hsl(var(--chart-2));
  border: 1px solid hsl(var(--chart-2) / 0.3);
}

.message.error {
  background: hsl(var(--destructive) / 0.1);
  color: hsl(var(--destructive));
  border: 1px solid hsl(var(--destructive) / 0.3);
}

.search-bar {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.search-bar .form-control {
  flex: 1;
}

.loading {
  text-align: center;
  padding: 2rem;
  color: hsl(var(--muted-foreground));
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: hsl(var(--muted-foreground));
}

.memories-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.memory-card {
  background: hsl(var(--card));
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius);
  padding: 1rem;
}

.memory-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.memory-role {
  padding: 0.125rem 0.5rem;
  border-radius: var(--radius);
  font-size: 0.75rem;
  font-weight: 500;
}

.memory-role.role-user {
  background: hsl(var(--primary) / 0.1);
  color: hsl(var(--primary));
}

.memory-role.role-assistant {
  background: hsl(var(--chart-2) / 0.1);
  color: hsl(var(--chart-2));
}

.memory-role.role-system {
  background: hsl(var(--muted));
  color: hsl(var(--muted-foreground));
}

.memory-role.role-tool {
  background: hsl(var(--chart-1) / 0.1);
  color: hsl(var(--chart-1));
}

.memory-session {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.75rem;
  color: hsl(var(--muted-foreground));
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

.tool-badge {
  padding: 0.125rem 0.5rem;
  background: hsl(var(--chart-1) / 0.1);
  color: hsl(var(--chart-1));
  border-radius: var(--radius);
  font-size: 0.6875rem;
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

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: hsl(var(--card));
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  max-width: 400px;
  width: 90%;
}

.modal h3 {
  margin: 0 0 0.75rem 0;
}

.modal p {
  margin: 0 0 1.5rem 0;
  color: hsl(var(--muted-foreground));
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}

.form-control {
  padding: 0.5rem 0.75rem;
  background: hsl(var(--background));
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius);
  font-size: 0.875rem;
  color: hsl(var(--foreground));
}

.form-control:focus {
  outline: none;
  border-color: hsl(var(--primary));
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
  border: 1px solid transparent;
}

.btn-primary {
  background: hsl(var(--primary));
  color: hsl(var(--primary-foreground));
}

.btn-primary:hover:not(:disabled) {
  background: hsl(var(--primary) / 0.9);
}

.btn-secondary {
  background: hsl(var(--secondary));
  color: hsl(var(--secondary-foreground));
  border-color: hsl(var(--border));
}

.btn-secondary:hover:not(:disabled) {
  background: hsl(var(--accent));
}

.btn-danger {
  background: hsl(var(--destructive));
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background: hsl(var(--destructive) / 0.9);
}

.btn-icon {
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .search-bar {
    flex-wrap: wrap;
  }
  
  .memory-header {
    flex-wrap: wrap;
  }
}
</style>
