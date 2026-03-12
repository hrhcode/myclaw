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
      <button @click="emit('create')" class="create-btn">
        <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        <span>新对话</span>
      </button>
    </div>
    
    <div class="sessions">
      <div v-if="isLoading" class="loading">
        加载中...
      </div>
      <div v-else-if="sessions.length === 0" class="empty">
        暂无对话记录
      </div>
      <template v-else>
        <SessionItem
          v-for="session in sessions"
          :key="session.id"
          :session="session"
          :is-active="session.id === currentSessionId"
          @select="emit('select', $event)"
          @delete="emit('delete', $event)"
        />
      </template>
    </div>
  </div>
</template>

<style scoped>
.session-list {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.session-header {
  padding: 1rem;
  border-bottom: 1px solid var(--color-border);
}

.create-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  width: 100%;
  padding: 0.5rem 1rem;
  background: var(--color-accent);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 0.875rem;
  transition: background 0.2s;
}

.create-btn:hover {
  background: var(--color-accent-hover);
}

.icon {
  width: 1.25rem;
  height: 1.25rem;
}

.sessions {
  flex: 1;
  overflow-y: auto;
}

.loading,
.empty {
  padding: 1rem;
  text-align: center;
  color: var(--color-text-tertiary);
  font-size: 0.875rem;
}
</style>
