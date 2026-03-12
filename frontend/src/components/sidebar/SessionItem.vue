<script setup lang="ts">
import type { Session } from '../../types'
import { cn } from '@/lib/utils'

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
    :class="cn(
      'session-item group',
      isActive && 'active'
    )"
    @click="emit('select', session.id)"
  >
    <div class="session-indicator" />
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
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.875rem 1rem;
  border-bottom: 1px solid hsl(var(--border) / 0.5);
  cursor: pointer;
  transition: all 0.2s ease;
}

.session-item::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, hsl(var(--primary) / 0.1) 0%, transparent 100%);
  opacity: 0;
  transition: opacity 0.2s ease;
}

.session-item:hover::before {
  opacity: 1;
}

.session-item:hover {
  background: hsl(var(--accent) / 0.5);
}

.session-indicator {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 0;
  background: linear-gradient(180deg, hsl(var(--primary)), hsl(var(--primary) / 0.5));
  border-radius: 0 2px 2px 0;
  transition: height 0.2s ease;
}

.session-item.active .session-indicator {
  height: 60%;
}

.session-item.active {
  background: hsl(var(--primary) / 0.1);
}

.session-item.active::before {
  opacity: 1;
}

.session-info {
  flex: 1;
  min-width: 0;
  position: relative;
  z-index: 1;
}

.session-title {
  font-size: 0.875rem;
  font-weight: 500;
  color: hsl(var(--foreground));
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-meta {
  font-size: 0.75rem;
  color: hsl(var(--muted-foreground));
  margin-top: 0.25rem;
}

.delete-btn {
  position: relative;
  z-index: 1;
  padding: 0.375rem;
  background: transparent;
  border: none;
  cursor: pointer;
  color: hsl(var(--muted-foreground));
  opacity: 0;
  border-radius: var(--radius);
  transition: all 0.2s ease;
}

.session-item:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  background: hsl(var(--destructive) / 0.1);
  color: hsl(var(--destructive));
}

.icon {
  width: 1rem;
  height: 1rem;
}
</style>
