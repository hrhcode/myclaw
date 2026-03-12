<script setup lang="ts">
import type { Session } from '../../types'
import SessionList from './SessionList.vue'

defineProps<{
  open: boolean
  sessions: Session[]
  currentSessionId: string
  isLoading: boolean
}>()

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
  (e: 'create'): void
  (e: 'select', id: string): void
  (e: 'delete', id: string): void
}>()
</script>

<template>
  <aside
    class="sidebar"
    :class="{ open }"
  >
    <SessionList
      :sessions="sessions"
      :current-session-id="currentSessionId"
      :is-loading="isLoading"
      @create="emit('create')"
      @select="emit('select', $event)"
      @delete="emit('delete', $event)"
    />
  </aside>
  
  <div
    v-if="open"
    class="sidebar-overlay"
    @click="emit('update:open', false)"
  ></div>
</template>

<style scoped>
.sidebar {
  width: 16rem;
  background: var(--color-sidebar-bg);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  transition: all 0.3s;
}

.sidebar:not(.open) {
  width: 0;
  overflow: hidden;
}

.sidebar-overlay {
  display: none;
}

@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    z-index: 50;
    width: 16rem;
    transform: translateX(-100%);
  }
  
  .sidebar.open {
    transform: translateX(0);
  }
  
  .sidebar-overlay {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 40;
  }
}
</style>
