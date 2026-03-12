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
    <div class="sidebar-glow" />
    <SessionList
      :sessions="sessions"
      :current-session-id="currentSessionId"
      :is-loading="isLoading"
      @create="emit('create')"
      @select="emit('select', $event)"
      @delete="emit('delete', $event)"
    />
  </aside>
  
  <Transition name="fade">
    <div
      v-if="open"
      class="sidebar-overlay"
      @click="emit('update:open', false)"
    />
  </Transition>
</template>

<style scoped>
.sidebar {
  width: 16rem;
  background: hsl(var(--card) / 0.8);
  backdrop-filter: blur(20px);
  border-right: 1px solid hsl(var(--border));
  display: flex;
  flex-direction: column;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.sidebar::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, 
    rgba(59, 130, 246, 0.05) 0%, 
    transparent 50%,
    rgba(139, 92, 246, 0.05) 100%
  );
  pointer-events: none;
}

.sidebar-glow {
  position: absolute;
  top: 0;
  right: 0;
  width: 1px;
  height: 100%;
  background: linear-gradient(180deg, 
    transparent 0%,
    rgba(59, 130, 246, 0.5) 20%,
    rgba(139, 92, 246, 0.5) 50%,
    rgba(6, 182, 212, 0.5) 80%,
    transparent 100%
  );
  opacity: 0.6;
  animation: glow-pulse 3s ease-in-out infinite;
}

@keyframes glow-pulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.8; }
}

.sidebar:not(.open) {
  width: 0;
  overflow: hidden;
}

.sidebar-overlay {
  display: none;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
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
    backdrop-filter: blur(4px);
    z-index: 40;
  }
}
</style>
