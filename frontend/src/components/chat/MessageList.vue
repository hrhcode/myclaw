<script setup lang="ts">
import type { Message } from '../../types'
import MessageItem from './MessageItem.vue'
import { ref, nextTick, watch } from 'vue'

const props = defineProps<{
  messages: Message[]
  isLoading: boolean
}>()

const emit = defineEmits<{
  (e: 'edit', id: number): void
  (e: 'regenerate', id: number): void
}>()

const containerRef = ref<HTMLElement | null>(null)
const expandedTools = ref<Record<string, boolean>>({})

function scrollToBottom() {
  nextTick(() => {
    if (containerRef.value) {
      containerRef.value.scrollTo({
        top: containerRef.value.scrollHeight,
        behavior: 'smooth'
      })
    }
  })
}

watch(() => props.messages.length, scrollToBottom)
watch(() => props.messages[props.messages.length - 1]?.content, scrollToBottom)
</script>

<template>
  <div ref="containerRef" class="message-list">
    <div class="messages-container">
      <div v-if="messages.length === 0" class="empty-state">
        <div class="empty-icon-wrapper">
          <svg class="empty-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
          <div class="empty-glow" />
        </div>
        <h3 class="empty-title">开始一段新对话吧</h3>
        <p class="empty-subtitle">输入您的问题，AI 将为您提供帮助</p>
      </div>
      
      <TransitionGroup name="message" tag="div" class="message-items">
        <MessageItem
          v-for="message in messages"
          :key="message.id"
          :message="message"
          v-model:expandedTools="expandedTools"
          @edit="emit('edit', $event)"
          @regenerate="emit('regenerate', $event)"
        />
      </TransitionGroup>
    </div>
  </div>
</template>

<style scoped>
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
}

.messages-container {
  max-width: 48rem;
  margin: 0 auto;
}

.message-items {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 300px;
  text-align: center;
}

.empty-icon-wrapper {
  position: relative;
  margin-bottom: 1.5rem;
}

.empty-icon {
  width: 5rem;
  height: 5rem;
  color: hsl(var(--muted-foreground));
  opacity: 0.5;
  animation: float 3s ease-in-out infinite;
}

.empty-glow {
  position: absolute;
  inset: -20px;
  background: radial-gradient(circle, hsl(var(--primary) / 0.2) 0%, transparent 70%);
  filter: blur(20px);
  animation: pulse 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

@keyframes pulse {
  0%, 100% { opacity: 0.5; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.1); }
}

.empty-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: hsl(var(--foreground));
  margin: 0 0 0.5rem 0;
}

.empty-subtitle {
  font-size: 0.875rem;
  color: hsl(var(--muted-foreground));
  margin: 0;
}

.message-enter-active {
  animation: message-in 0.4s ease-out;
}

.message-leave-active {
  animation: message-out 0.3s ease-in;
}

@keyframes message-in {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes message-out {
  from {
    opacity: 1;
    transform: translateY(0);
  }
  to {
    opacity: 0;
    transform: translateY(-20px);
  }
}
</style>
