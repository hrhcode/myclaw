<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { Message } from '../../types'
import CodeBlock from '../common/CodeBlock.vue'
import ToolCall from './ToolCall.vue'
import LoadingDots from '../common/LoadingDots.vue'
import { cn } from '@/lib/utils'

const props = defineProps<{
  message: Message
  isGenerating?: boolean
}>()

const emit = defineEmits<{
  (e: 'edit', id: number): void
  (e: 'regenerate', id: number): void
  (e: 'delete', id: number): void
}>()

const isUser = computed(() => props.message.role === 'user')
const isAssistant = computed(() => props.message.role === 'assistant')
const isEmpty = computed(() => !props.message.content && !props.message.toolCalls?.length && !props.message.thoughts)

/**
 * 是否正在思考中
 * 条件：正在生成中 && 有思考内容 && 正文内容为空
 * 当正文开始输出时，思考过程就结束了
 */
const isThinking = computed(() => {
  return props.isGenerating && props.message.thoughts && !props.message.content
})

/**
 * 思考内容是否展开
 * 思考中时展开，思考结束后折叠
 */
const isThoughtsExpanded = ref(false)

/**
 * 监听思考状态变化
 * 思考开始时展开，思考结束时折叠
 */
watch(isThinking, (newValue, oldValue) => {
  if (newValue && !oldValue) {
    // 思考开始，展开
    isThoughtsExpanded.value = true
  } else if (!newValue && oldValue) {
    // 思考结束，折叠
    isThoughtsExpanded.value = false
  }
}, { immediate: true })

/**
 * 切换思考内容展开/折叠
 */
function toggleThoughts() {
  isThoughtsExpanded.value = !isThoughtsExpanded.value
}

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
          
          <div v-if="message.thoughts || isGenerating" class="thinking-wrapper">
            <div class="thinking-process" :class="{ 'is-thinking': isThinking }">
              <div class="thinking-header" @click="toggleThoughts">
                <div class="thinking-title">
                  <svg class="thinking-icon" :class="{ 'animate-pulse': isThinking }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                  <span>思考过程</span>
                  <span v-if="isThinking" class="thinking-status">思考中...</span>
                </div>
                <svg 
                  class="expand-icon" 
                  :class="{ expanded: isThoughtsExpanded }"
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                </svg>
              </div>
              <div v-if="isThoughtsExpanded && message.thoughts" class="thinking-body">
                <div class="thinking-content" v-html="message.thoughts"></div>
              </div>
            </div>
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
  background: transparent;
  color: hsl(var(--foreground));
  border: none;
  border-radius: 0;
  padding: 0;
  box-shadow: none;
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

.thinking-process {
  margin: 0.5rem 0;
  overflow: hidden;
}

.thinking-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.25rem 0;
  cursor: pointer;
  user-select: none;
}

.thinking-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.thinking-icon {
  width: 1rem;
  height: 1rem;
  color: hsl(var(--primary));
}

.thinking-icon.animate-pulse {
  animation: pulse-glow 2s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% {
    opacity: 1;
    filter: drop-shadow(0 0 0px transparent);
  }
  50% {
    opacity: 0.8;
    filter: drop-shadow(0 0 4px hsl(var(--primary) / 0.6));
  }
}

.thinking-title span {
  font-size: 0.75rem;
  font-weight: 500;
  color: hsl(var(--primary));
}

.thinking-status {
  font-size: 0.625rem;
  color: hsl(var(--primary) / 0.7);
  animation: fade-pulse 1.5s ease-in-out infinite;
}

.expand-icon {
  width: 0.875rem;
  height: 0.875rem;
  color: hsl(var(--muted-foreground));
  transition: transform 0.2s;
  flex-shrink: 0;
}

.expand-icon.expanded {
  transform: rotate(90deg);
}

@keyframes fade-pulse {
  0%, 100% {
    opacity: 0.5;
  }
  50% {
    opacity: 1;
  }
}

.thinking-body {
  padding: 0.25rem 0;
}

.thinking-content {
  font-size: 0.75rem;
  line-height: 1.6;
  color: hsl(var(--muted-foreground));
  white-space: pre-wrap;
  word-break: break-word;
  font-family: ui-monospace, 'Cascadia Code', 'Fira Code', monospace;
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
