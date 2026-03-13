<script setup lang="ts">
import { computed } from 'vue'
import type { Message } from '../../types'
import CodeBlock from '../common/CodeBlock.vue'
import ToolCall from './ToolCall.vue'
import ThinkingProcess from './ThinkingProcess.vue'
import LoadingDots from '../common/LoadingDots.vue'
import { cn } from '@/lib/utils'

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
const isEmpty = computed(() => !props.message.content && !props.message.toolCalls?.length)

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
  <div
    :class="cn(
      'message-item',
      isUser && 'user',
      isAssistant && 'assistant'
    )"
  >
    <div class="avatar" :class="isUser ? 'user-avatar' : 'assistant-avatar'">
      <template v-if="isUser">
        <svg class="avatar-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
      </template>
      <template v-else>
        <div class="ai-avatar">
          <svg class="avatar-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        </div>
      </template>
    </div>
    
    <div class="message-body">
      <div class="message-header">
        <span v-if="isAssistant" class="role-name">MyClaw</span>
        <span class="timestamp">{{ formatTime(message.timestamp) }}</span>
      </div>
      
      <div class="message-content">
        <LoadingDots v-if="isEmpty && isAssistant" />
        
        <template v-else>
          <div v-if="message.image" class="message-image">
            <img :src="message.image" alt="用户上传的图片" />
          </div>
          
          <div v-if="message.thoughts" class="thinking-wrapper">
            <ThinkingProcess :thoughts="message.thoughts" />
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
          
          <template v-for="(part, index) in renderContent(message.content)" :key="index">
            <CodeBlock v-if="part.type === 'code'" :text="part.content" :language="part.language" />
            <div v-else class="text-content" v-html="part.content"></div>
          </template>
        </template>
      </div>
      
      <div class="message-actions">
        <button v-if="isUser" @click="emit('edit', message.id)" class="action-btn" title="编辑">
          <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
        </button>
        <button v-if="isAssistant" @click="emit('regenerate', message.id)" class="action-btn" title="重新生成">
          <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.message-item {
  display: flex;
  gap: 0.625rem;
  padding: 0.5rem 0;
}

.message-item.user {
  flex-direction: row-reverse;
  justify-content: flex-start;
}

.message-item.user .message-body {
  align-items: flex-end;
}

.avatar {
  flex-shrink: 0;
  width: 1.75rem;
  height: 1.75rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.user-avatar {
  background: linear-gradient(135deg, hsl(var(--primary)) 0%, hsl(var(--primary) / 0.7) 100%);
  box-shadow: 0 2px 8px -2px hsl(var(--primary) / 0.4);
}

.user-avatar .avatar-icon {
  width: 1rem;
  height: 1rem;
  color: hsl(var(--primary-foreground));
}

.assistant-avatar {
  background: hsl(var(--card));
  border: 1px solid hsl(var(--border));
}

.ai-avatar {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, hsl(var(--primary) / 0.1) 0%, hsl(var(--accent) / 0.1) 100%);
}

.assistant-avatar .avatar-icon {
  width: 0.875rem;
  height: 0.875rem;
  color: hsl(var(--primary));
}

.message-body {
  flex: 1;
  min-width: 0;
  max-width: calc(100% - 2.5rem);
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  height: 1rem;
}

.message-item.user .message-header {
  flex-direction: row-reverse;
}

.role-name {
  font-size: 0.625rem;
  font-weight: 600;
  color: hsl(var(--primary));
  letter-spacing: 0.02em;
}

.timestamp {
  font-size: 0.5625rem;
  color: hsl(var(--muted-foreground));
  opacity: 0.6;
}

.message-content {
  padding: 0.5rem 0.75rem;
  border-radius: 12px;
  position: relative;
  transition: all 0.2s ease;
  display: inline-block;
  width: fit-content;
  max-width: 100%;
}

.message-item.user .message-content {
  background: linear-gradient(135deg, hsl(var(--primary)) 0%, hsl(var(--primary) / 0.85) 100%);
  color: hsl(var(--primary-foreground));
  border-bottom-right-radius: 4px;
  box-shadow: 0 2px 10px -3px hsl(var(--primary) / 0.3);
}

.message-item.assistant .message-content {
  background: hsl(var(--card));
  color: hsl(var(--foreground));
  border: 1px solid hsl(var(--border));
  border-bottom-left-radius: 4px;
}

.message-item.assistant .message-content::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 2px;
  background: linear-gradient(180deg, hsl(var(--primary)), hsl(var(--primary) / 0.3));
  border-radius: 2px 0 0 2px;
}

.text-content {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.5;
  font-size: 0.875rem;
}

.message-image {
  margin-bottom: 0.5rem;
}

.message-image img {
  max-width: 100%;
  max-height: 300px;
  border-radius: 8px;
  object-fit: contain;
  display: block;
}

.tool-calls {
  margin-bottom: 0.5rem;
}

.thinking-wrapper {
  margin-bottom: 0.5rem;
}

.message-actions {
  display: flex;
  gap: 0.25rem;
  height: 1.25rem;
  opacity: 0;
  transition: opacity 0.2s;
}

.message-item.user .message-actions {
  justify-content: flex-end;
}

.message-item:hover .message-actions {
  opacity: 1;
}

.action-btn {
  padding: 0.125rem 0.25rem;
  background: transparent;
  border: none;
  cursor: pointer;
  color: hsl(var(--muted-foreground));
  border-radius: 4px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-btn:hover {
  background: hsl(var(--muted));
  color: hsl(var(--foreground));
}

.icon {
  width: 0.75rem;
  height: 0.75rem;
}
</style>
