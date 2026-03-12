<script setup lang="ts">
/**
 * Chat 聊天页面
 * 参考 OpenClaw 设计，简洁的聊天界面
 */
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import type { Message, Session } from '@/types'
import MessageList from '@/components/chat/MessageList.vue'
import MessageInput from '@/components/input/MessageInput.vue'
import { useKeyboard } from '@/composables/useKeyboard'
import { post, del, get, stream } from '@/utils/request'
import { API_ENDPOINTS } from '@/config/api'

const messages = ref<Message[]>([])
const isLoading = ref(false)

const sessions = ref<Session[]>([])
const currentSessionId = ref<string>('main')
const isLoadingSessions = ref(false)

let abortController: AbortController | null = null
const inputRef = ref<InstanceType<typeof MessageInput> | null>(null)
const STORAGE_KEY = 'myclaw_session_id'

const { registerShortcut } = useKeyboard()

onMounted(() => {
  initSession()
  
  registerShortcut({
    key: 'n',
    ctrl: true,
    handler: () => {
      if (inputRef.value) {
        inputRef.value.setContent('/new ')
        inputRef.value.focus()
      }
    },
    description: '新建会话'
  })
  
  registerShortcut({
    key: '/',
    ctrl: true,
    handler: () => { inputRef.value?.focus() },
    description: '聚焦输入框'
  })
})

onUnmounted(() => {
  if (abortController) {
    abortController.abort()
    abortController = null
  }
})

async function initSession() {
  await loadSessions()
  
  const savedSessionId = localStorage.getItem(STORAGE_KEY)
  
  if (savedSessionId) {
    const sessionExists = sessions.value.some(s => s.id === savedSessionId)
    if (sessionExists) {
      currentSessionId.value = savedSessionId
      await loadMessages()
      return
    }
  }
  
  if (sessions.value.length > 0) {
    const data = await post(API_ENDPOINTS.SESSIONS, { channel: 'web' })
    currentSessionId.value = data.session_id
    localStorage.setItem(STORAGE_KEY, data.session_id)
    messages.value = []
  } else {
    currentSessionId.value = sessions.value[0].id
    await loadMessages()
  }
}

async function loadSessions() {
  isLoadingSessions.value = true
  try {
    const data = await get(`${API_ENDPOINTS.SESSIONS}?limit=20`)
    sessions.value = (data.sessions || []).filter((s: Session) => s.message_count > 0)
  } catch (error) {
    console.error('加载会话列表失败:', error)
    sessions.value = []
  } finally {
    isLoadingSessions.value = false
  }
}

async function loadMessages() {
  if (!currentSessionId.value) return

  try {
    const data = await get(`${API_ENDPOINTS.SESSION_MESSAGES(currentSessionId.value)}?limit=100`)

    const processedMessages: Message[] = []
    const toolResults: Record<string, string> = {}

    for (const m of data.messages || []) {
      if (m.role === 'tool') {
        if (m.tool_call_id) {
          toolResults[m.tool_call_id] = m.content
        }
        continue
      }

      const message: Message = {
        id: m.id,
        role: m.role,
        content: m.content || '',
        timestamp: m.timestamp,
      }

      if (m.tool_calls && m.tool_calls.length > 0) {
        message.toolCalls = m.tool_calls.map((tc: any) => ({
          id: tc.id,
          name: tc.function?.name || tc.name,
          arguments: tc.function?.arguments ? JSON.parse(tc.function.arguments) : (tc.arguments || {}),
          status: toolResults[tc.id] ? 'success' : 'running',
          result: toolResults[tc.id],
          durationMs: tc.duration_ms,
        }))
      }

      processedMessages.push(message)
    }

    messages.value = processedMessages
  } catch (error) {
    if ((error as any)?.response?.status === 404) {
      messages.value = []
    } else {
      console.error('加载消息失败:', error)
      messages.value = []
    }
  }
}

async function switchSession(sessionId: string) {
  if (sessionId === currentSessionId.value) return
  
  currentSessionId.value = sessionId
  localStorage.setItem(STORAGE_KEY, sessionId)
  await loadMessages()
}

function isResetCommand(text: string): boolean {
  const trimmed = text.trim().toLowerCase()
  return trimmed === '/new' || trimmed === '/reset' || 
         trimmed.startsWith('/new ') || trimmed.startsWith('/reset ')
}

async function handleResetCommand(content: string): Promise<boolean> {
  const trimmed = content.trim()
  const normalized = trimmed.toLowerCase()
  
  let newContent = ''
  if (normalized.startsWith('/new ')) {
    newContent = trimmed.slice(5).trim()
  } else if (normalized.startsWith('/reset ')) {
    newContent = trimmed.slice(7).trim()
  }
  
  try {
    const data = await post(API_ENDPOINTS.SESSIONS, { channel: 'web' })
    currentSessionId.value = data.session_id
    localStorage.setItem(STORAGE_KEY, data.session_id)
    messages.value = []
    await loadSessions()
    
    if (newContent) {
      await sendMessageInternal(newContent)
    }
    return true
  } catch (error) {
    console.error('创建会话失败:', error)
    return false
  }
}

async function sendMessage(content: string) {
  if (!content.trim()) return
  
  if (isResetCommand(content)) {
    await handleResetCommand(content)
    return
  }
  
  await sendMessageInternal(content)
}

async function sendMessageInternal(content: string) {
  if (!content.trim()) return
  
  if (isLoading.value) {
    if (abortController) {
      abortController.abort()
      abortController = null
    }
    isLoading.value = false
  }
  
  if (!currentSessionId.value) {
    const data = await post(API_ENDPOINTS.SESSIONS, { channel: 'web' })
    currentSessionId.value = data.session_id
    localStorage.setItem(STORAGE_KEY, data.session_id)
    messages.value = []
    await loadSessions()
  }

  messages.value.push({
    id: Date.now(),
    role: 'user',
    content: content,
    timestamp: new Date().toISOString(),
  })

  isLoading.value = true

  const assistantMessageId = Date.now() + 1
  messages.value.push({
    id: assistantMessageId,
    role: 'assistant',
    content: '',
    timestamp: new Date().toISOString(),
  })

  const handleStreamError = (error: Error) => {
    if (error.name !== 'AbortError') {
      console.error('发送消息失败:', error)
      const msgIndex = messages.value.findIndex(m => m.id === assistantMessageId)
      if (msgIndex !== -1 && !messages.value[msgIndex].content) {
        messages.value[msgIndex].content = '抱歉，发生了错误，请稍后再试。'
      }
    }
  }

  const handleStreamComplete = () => {
    isLoading.value = false
    abortController = null
    loadSessions().catch(() => {})
  }

  try {
    abortController = stream(
      API_ENDPOINTS.CHAT_COMPLETIONS,
      {
        messages: [{ role: 'user', content }],
        session_id: currentSessionId.value,
        stream: true,
      },
      (parsed) => {
        if (parsed.choices && parsed.choices[0]?.delta) {
          const delta = parsed.choices[0].delta
          const msgIndex = messages.value.findIndex(m => m.id === assistantMessageId)

          if (delta.content) {
            if (msgIndex !== -1) {
              messages.value[msgIndex].content += delta.content
            }
          }

          if (delta.tool_calls && delta.tool_calls.length > 0) {
            const toolCall = delta.tool_calls[0]

            if (msgIndex !== -1) {
              if (!messages.value[msgIndex].toolCalls) {
                messages.value[msgIndex].toolCalls = []
              }

              const existingToolIndex = messages.value[msgIndex].toolCalls!.findIndex(
                t => t.id === toolCall.id
              )

              if (existingToolIndex === -1) {
                messages.value[msgIndex].toolCalls!.push({
                  id: toolCall.id,
                  name: toolCall.name,
                  arguments: toolCall.arguments || {},
                  status: toolCall.status || 'running',
                  result: toolCall.result,
                  durationMs: toolCall.duration_ms,
                })
              } else {
                const existingTool = messages.value[msgIndex].toolCalls![existingToolIndex]
                if (toolCall.status) {
                  existingTool.status = toolCall.status
                }
                if (toolCall.result !== undefined) {
                  existingTool.result = toolCall.result
                }
                if (toolCall.duration_ms !== undefined) {
                  existingTool.durationMs = toolCall.duration_ms
                }
              }
            }
          }
        }
      },
      handleStreamError,
      handleStreamComplete
    )
  } catch (error) {
    handleStreamError(error as Error)
    handleStreamComplete()
  }
}
</script>

<template>
  <div class="chat-page">
    <div class="chat-header">
      <div class="session-selector">
        <select
          :value="currentSessionId"
          @change="switchSession(($event.target as HTMLSelectElement).value)"
          class="session-select"
        >
          <option
            v-for="session in sessions"
            :key="session.id"
            :value="session.id"
          >
            对话 {{ session.id.slice(0, 8) }} ({{ session.message_count }} 条消息)
          </option>
        </select>
      </div>
    </div>
    
    <MessageList
      :messages="messages"
      :is-loading="isLoading"
      @edit="() => {}"
      @regenerate="() => {}"
    />
    
    <footer class="chat-footer">
      <MessageInput
        ref="inputRef"
        :disabled="isLoading"
        @submit="sendMessage"
      />
      <div class="input-hint">
        <span>输入 /new 创建新会话</span>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  flex: 1 1 0;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  background: hsl(var(--card) / 0.5);
  border-radius: var(--radius-lg);
}

.chat-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 1rem;
  background: hsl(var(--card) / 0.8);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid hsl(var(--border));
  flex-shrink: 0;
}

.session-selector {
  position: relative;
}

.session-select {
  appearance: none;
  padding: 0.375rem 1.75rem 0.375rem 0.625rem;
  background: hsl(var(--muted) / 0.5);
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius);
  font-size: 0.8125rem;
  color: hsl(var(--foreground));
  cursor: pointer;
  min-width: 160px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%236b7280'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 0.375rem center;
  background-size: 1rem;
}

.session-select:hover {
  border-color: hsl(var(--primary) / 0.5);
}

.session-select:focus {
  outline: none;
  border-color: hsl(var(--primary));
  box-shadow: 0 0 0 2px hsl(var(--primary) / 0.2);
}

.chat-footer {
  padding: 0.75rem 1rem;
  background: linear-gradient(to bottom, transparent, hsl(var(--background)) 20%);
  border-top: 1px solid hsl(var(--border));
  flex-shrink: 0;
}

.input-hint {
  display: flex;
  justify-content: center;
  margin-top: 0.375rem;
}

.input-hint span {
  font-size: 0.6875rem;
  color: hsl(var(--muted-foreground));
}

@media (max-width: 768px) {
  .chat-header {
    padding: 0.375rem 0.75rem;
  }
  
  .session-select {
    min-width: 120px;
    font-size: 0.75rem;
  }
  
  .session-title {
    display: none;
  }
}
</style>
