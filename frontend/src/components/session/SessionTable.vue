<script setup lang="ts">
/**
 * SessionTable 会话表格组件
 * 显示会话列表的表格
 */
import type { SessionInfo } from '@/api/gateway'

defineProps<{
  sessions: SessionInfo[]
  loading: boolean
}>()

const emit = defineEmits<{
  delete: [id: string]
}>()

function formatTime(time: string): string {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

function truncateId(id: string): string {
  if (id.length > 30) {
    return id.substring(0, 30) + '...'
  }
  return id
}
</script>

<template>
  <div class="session-table">
    <div class="table-header">
      <div class="col col-id">会话 ID</div>
      <div class="col col-channel">通道</div>
      <div class="col col-count">消息数</div>
      <div class="col col-created">创建时间</div>
      <div class="col col-updated">更新时间</div>
      <div class="col col-actions">操作</div>
    </div>

    <div v-if="loading" class="table-loading">
      <svg class="spinner" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <span>加载中...</span>
    </div>

    <div v-else-if="sessions.length === 0" class="table-empty">
      暂无会话数据
    </div>

    <div v-else class="table-body">
      <div
        v-for="session in sessions"
        :key="session.id"
        class="table-row"
      >
        <div class="col col-id mono" :title="session.id">
          {{ truncateId(session.id) }}
        </div>
        <div class="col col-channel">
          <span class="channel-badge">{{ session.channel }}</span>
        </div>
        <div class="col col-count">{{ session.message_count }}</div>
        <div class="col col-created">{{ formatTime(session.created_at) }}</div>
        <div class="col col-updated">{{ formatTime(session.updated_at) }}</div>
        <div class="col col-actions">
          <button @click="emit('delete', session.id)" class="btn-delete">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.session-table {
  background: hsl(var(--card));
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.table-header {
  display: grid;
  grid-template-columns: 1fr 80px 80px 150px 150px 80px;
  gap: 1rem;
  padding: 0.75rem 1rem;
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
  grid-template-columns: 1fr 80px 80px 150px 150px 80px;
  gap: 1rem;
  padding: 0.75rem 1rem;
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

.channel-badge {
  display: inline-block;
  padding: 0.125rem 0.5rem;
  background: hsl(var(--primary) / 0.1);
  border-radius: var(--radius-full);
  font-size: 0.75rem;
  font-weight: 500;
  color: hsl(var(--primary));
  text-transform: capitalize;
}

.btn-delete {
  padding: 0.375rem;
  background: transparent;
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
  color: hsl(var(--muted-foreground));
  transition: all 0.2s;
}

.btn-delete:hover {
  background: hsl(var(--destructive) / 0.1);
  color: hsl(var(--destructive));
}

.btn-delete svg {
  width: 1rem;
  height: 1rem;
}

.table-loading,
.table-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 3rem;
  color: hsl(var(--muted-foreground));
}

.spinner {
  width: 1.5rem;
  height: 1.5rem;
  animation: spin 1s linear infinite;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
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

  .col-created,
  .col-updated {
    display: none;
  }
}
</style>
