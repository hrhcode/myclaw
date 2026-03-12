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
      containerRef.value.scrollTop = containerRef.value.scrollHeight
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
        <svg class="empty-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
        <p>开始一段新对话吧</p>
      </div>
      
      <MessageItem
        v-for="message in messages"
        :key="message.id"
        :message="message"
        v-model:expandedTools="expandedTools"
        @edit="emit('edit', $event)"
        @regenerate="emit('regenerate', $event)"
      />
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

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--color-text-tertiary);
}

.empty-icon {
  width: 4rem;
  height: 4rem;
  margin-bottom: 1rem;
}
</style>
