<script setup lang="ts">
import type { Session } from '../../types'
import SessionItem from './SessionItem.vue'

defineProps<{
  sessions: Session[]
  currentSessionId: string
  isLoading: boolean
}>()

const emit = defineEmits<{
  (e: 'create'): void
  (e: 'select', id: string): void
  (e: 'delete', id: string): void
}>()
</script>

<template>
  <div class="session-list">
    <div class="session-header">
      <button @click="emit('create')" class="create-btn group">
        <div class="btn-glow" />
        <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        <span>新对话</span>
      </button>
    </div>
    
    <div class="sessions">
      <div v-if="isLoading" class="loading">
        <div class="loading-spinner" />
        <span>加载中...</span>
      </div>
      <div v-else-if="sessions.length === 0" class="empty">
        <svg class="empty-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
        <span>暂无对话记录</span>
      </div>
      <TransitionGroup v-else name="list" tag="div" class="session-items">
        <SessionItem
          v-for="session in sessions"
          :key="session.id"
          :session="session"
          :is-active="session.id === currentSessionId"
          @select="emit('select', $event)"
          @delete="emit('delete', $event)"
        />
      </TransitionGroup>
    </div>
  </div>
</template>

<style scoped>
.session-list {
  display: flex;
  flex-direction: column;
  height: 100%;
  position: relative;
  z-index: 1;
}

.session-header {
  padding: 1rem;
  border-bottom: 1px solid hsl(var(--border));
}

.create-btn {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  width: 100%;
  padding: 0.75rem 1rem;
  background: linear-gradient(135deg, hsl(var(--primary)) 0%, hsl(var(--primary) / 0.8) 100%);
  color: hsl(var(--primary-foreground));
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.3s ease;
  overflow: hidden;
}

.btn-glow {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
  transform: translateX(-100%);
  transition: transform 0.5s ease;
}

.create-btn:hover .btn-glow {
  transform: translateX(100%);
}

.create-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 30px -10px hsl(var(--primary) / 0.5);
}

.icon {
  width: 1.25rem;
  height: 1.25rem;
}

.sessions {
  flex: 1;
  overflow-y: auto;
}

.session-items {
  display: flex;
  flex-direction: column;
}

.loading,
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem 1rem;
  color: hsl(var(--muted-foreground));
  font-size: 0.875rem;
  gap: 0.75rem;
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 2px solid hsl(var(--border));
  border-top-color: hsl(var(--primary));
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-icon {
  width: 3rem;
  height: 3rem;
  opacity: 0.5;
}

.list-enter-active,
.list-leave-active {
  transition: all 0.3s ease;
}

.list-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

.list-leave-to {
  opacity: 0;
  transform: translateX(20px);
}
</style>
