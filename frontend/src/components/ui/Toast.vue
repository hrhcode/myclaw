<script setup lang="ts">
/**
 * Toast 消息提示组件
 * 提供统一的消息提示
 */
import { ref, onMounted, onUnmounted } from 'vue'

export interface ToastMessage {
  id: number
  type: 'success' | 'error' | 'warning' | 'info'
  text: string
}

const messages = ref<ToastMessage[]>([])
let idCounter = 0

function add(type: ToastMessage['type'], text: string, duration: number = 3000) {
  const id = ++idCounter
  messages.value.push({ id, type, text })
  
  if (duration > 0) {
    setTimeout(() => {
      remove(id)
    }, duration)
  }
  
  return id
}

function remove(id: number) {
  const index = messages.value.findIndex(m => m.id === id)
  if (index > -1) {
    messages.value.splice(index, 1)
  }
}

function success(text: string, duration?: number) {
  return add('success', text, duration)
}

function error(text: string, duration?: number) {
  return add('error', text, duration)
}

function warning(text: string, duration?: number) {
  return add('warning', text, duration)
}

function info(text: string, duration?: number) {
  return add('info', text, duration)
}

defineExpose({
  success,
  error,
  warning,
  info,
  add,
  remove,
})
</script>

<template>
  <Teleport to="body">
    <div class="toast-container">
      <TransitionGroup name="toast">
        <div
          v-for="msg in messages"
          :key="msg.id"
          class="toast"
          :class="msg.type"
        >
          <svg v-if="msg.type === 'success'" class="toast-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
          <svg v-else-if="msg.type === 'error'" class="toast-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
          <svg v-else-if="msg.type === 'warning'" class="toast-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <svg v-else class="toast-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span class="toast-text">{{ msg.text }}</span>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.toast-container {
  position: fixed;
  top: 1rem;
  right: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  z-index: 2000;
  pointer-events: none;
}

.toast {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: hsl(var(--card));
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius);
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  pointer-events: auto;
  min-width: 200px;
  max-width: 400px;
}

.toast.success {
  border-color: hsl(var(--chart-2) / 0.5);
  background: hsl(var(--chart-2) / 0.1);
}

.toast.success .toast-icon {
  color: hsl(var(--chart-2));
}

.toast.error {
  border-color: hsl(var(--destructive) / 0.5);
  background: hsl(var(--destructive) / 0.1);
}

.toast.error .toast-icon {
  color: hsl(var(--destructive));
}

.toast.warning {
  border-color: hsl(45 93% 47% / 0.5);
  background: hsl(45 93% 47% / 0.1);
}

.toast.warning .toast-icon {
  color: hsl(45 93% 47%);
}

.toast.info {
  border-color: hsl(var(--primary) / 0.5);
  background: hsl(var(--primary) / 0.1);
}

.toast.info .toast-icon {
  color: hsl(var(--primary));
}

.toast-icon {
  width: 1.25rem;
  height: 1.25rem;
  flex-shrink: 0;
}

.toast-text {
  font-size: 0.875rem;
  color: hsl(var(--foreground));
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}
</style>
