<script setup lang="ts">
import { computed } from 'vue'
import type { Message } from '../../types'
import CodeBlock from '../common/CodeBlock.vue'
import ToolCall from './ToolCall.vue'
import LoadingDots from '../common/LoadingDots.vue'

const props = defineProps<{
  message: Message
}>()

const emit = defineEmits<{
  (e: 'edit', id: number): void
  (e: 'regenerate', id: number): void
  (e: 'delete', id: number): void
}>()

const isUser = computed(() => props.message.role === 'user')
const isAssistant = computed(() => props.message.role === 'assistant')
// 只有当内容为空且没有工具调用时，才显示 loading dots
const isEmpty = computed(() => !props.message.content && !props.message.toolCalls?.length)
// 是否有工具调用（用于判断是否显示工具调用区域）
const hasToolCalls = computed(() => props.message.toolCalls && props.message.toolCalls.length > 0)

const expandedTools = defineModel<Record<string, boolean>>('expandedTools', { default: () => ({}) })

function toggleTool(toolId: string) {
  expandedTools.value[toolId] = !expandedTools.value[toolId]
}

function formatTime(timestamp?: string) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function renderContent(content: string) {
  const codeBlockRegex = /```(\w*)\n([\s\S]*?)```/g
  const parts: Array<{ type: 'text' | 'code'; content: string; language?: string }> = []
  let lastIndex = 0
  let match

  while ((match = codeBlockRegex.exec(content)) !== null) {
    if (match.index > lastIndex) {
      parts.push({ type: 'text', content: content.slice(lastIndex, match.index) })
    }
    parts.push({ type: 'code', content: match[2].trim(), language: match[1] || undefined })
    lastIndex = match.index + match[0].length
  }

  if (lastIndex < content.length) {
    parts.push({ type: 'text', content: content.slice(lastIndex) })
  }

  return parts
}
</script>

<template>
  <div class="message-item" :class="{ user: isUser, assistant: isAssistant }">
    <div class="message-content">
      <div v-if="isEmpty && isAssistant" class="empty-assistant">
        <LoadingDots />
      </div>
      
      <template v-else>
        <div v-for="(part, index) in renderContent(message.content)" :key="index">
          <CodeBlock v-if="part.type === 'code'" :text="part.content" :language="part.language" />
          <div v-else class="text-content" v-html="part.content"></div>
        </div>
        
        <div v-if="message.toolCalls?.length" class="tool-calls">
          <ToolCall
            v-for="tool in message.toolCalls"
            :key="tool.id"
            :tool-call="tool"
            :expanded="!!expandedTools[tool.id]"
            @update:expanded="toggleTool(tool.id)"
          />
        </div>
      </template>
      
      <div class="message-footer">
        <span class="timestamp">{{ formatTime(message.timestamp) }}</span>
        <div v-if="isUser" class="actions">
          <button @click="emit('edit', message.id)" class="action-btn" title="编辑">
            <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </button>
        </div>
        <div v-if="isAssistant" class="actions">
          <button @click="emit('regenerate', message.id)" class="action-btn" title="重新生成">
            <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.message-item {
  display: flex;
  margin-bottom: 1rem;
}

.message-item.user {
  justify-content: flex-end;
}

.message-item.assistant {
  justify-content: flex-start;
}

.message-content {
  max-width: 80%;
  padding: 0.75rem 1rem;
  border-radius: var(--radius-lg);
}

.message-item.user .message-content {
  background: var(--color-user-bg);
  color: var(--color-user-text);
}

.message-item.assistant .message-content {
  background: var(--color-assistant-bg);
  color: var(--color-assistant-text);
  border: 1px solid var(--color-border);
}

.empty-assistant {
  padding: 0.5rem;
}

.text-content {
  white-space: pre-wrap;
  word-break: break-word;
}

.tool-calls {
  margin-top: 0.5rem;
}

.message-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 0.5rem;
  gap: 0.5rem;
}

.timestamp {
  font-size: 0.75rem;
  opacity: 0.7;
}

.actions {
  display: flex;
  gap: 0.25rem;
  opacity: 0;
  transition: opacity 0.2s;
}

.message-content:hover .actions {
  opacity: 1;
}

.action-btn {
  padding: 0.25rem;
  background: transparent;
  border: none;
  cursor: pointer;
  color: inherit;
  opacity: 0.7;
  transition: opacity 0.2s;
}

.action-btn:hover {
  opacity: 1;
}

.icon {
  width: 0.875rem;
  height: 0.875rem;
}
</style>
