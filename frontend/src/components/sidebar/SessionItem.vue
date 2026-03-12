<script setup lang="ts">
import type { Session } from '../../types'

const props = defineProps<{
  session: Session
  isActive: boolean
}>()

const emit = defineEmits<{
  (e: 'select', id: string): void
  (e: 'delete', id: string): void
}>()

function formatTime(timestamp: string) {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (days === 0) {
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  } else if (days === 1) {
    return '昨天'
  } else if (days < 7) {
    return `${days}天前`
  } else {
    return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
  }
}

function handleDelete(event: Event) {
  event.stopPropagation()
  emit('delete', props.session.id)
}
</script>

<template>
  <div
    class="session-item"
    :class="{ active: isActive }"
    @click="emit('select', session.id)"
  >
    <div class="session-info">
      <div class="session-title">
        对话 {{ session.id.slice(0, 8) }}
      </div>
      <div class="session-meta">
        {{ session.message_count }} 条消息 · {{ formatTime(session.updated_at) }}
      </div>
    </div>
    <button
      @click="handleDelete"
      class="delete-btn"
      title="删除对话"
    >
      <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
      </svg>
    </button>
  </div>
</template>

<style scoped>
.session-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  border-bottom: 1px solid var(--color-border-light);
  cursor: pointer;
  transition: background 0.2s;
}

.session-item:hover {
  background: var(--color-bg-secondary);
}

.session-item.active {
  background: rgba(59, 130, 246, 0.1);
  border-left: 2px solid var(--color-accent);
}

.session-info {
  flex: 1;
  min-width: 0;
}

.session-title {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-meta {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
  margin-top: 0.25rem;
}

.delete-btn {
  padding: 0.25rem;
  background: transparent;
  border: none;
  cursor: pointer;
  color: var(--color-text-tertiary);
  opacity: 0;
  transition: all 0.2s;
}

.session-item:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  color: var(--color-error);
}

.icon {
  width: 1rem;
  height: 1rem;
}
</style>
