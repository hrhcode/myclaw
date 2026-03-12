<script setup lang="ts">
/**
 * Chat 聊天页面
 * 提供聊天功能，参考 OpenClaw 设计集成会话选择器
 */
import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { Message, Session } from '@/types'
import MessageList from '@/components/chat/MessageList.vue'
import MessageInput from '@/components/input/MessageInput.vue'
import { useKeyboard } from '@/composables/useKeyboard'
import { post, del, get, stream } from '@/utils/request'
import { API_ENDPOINTS } from '@/config/api'

const messages = ref<Message[]>([])
const isLoading = ref(false)

const sessions = ref<Session[]>([])
const currentSessionId = ref<string>('')
const isLoadingSessions = ref(false)

let abortController: AbortController | null = null
const inputRef = ref<InstanceType<typeof MessageInput> | null>(null)

const STORAGE_KEY = 'myclaw_session_id'

const { registerShortcut } = useKeyboard()

const currentSession = computed(() => {
  return sessions.value.find(s => s.id === currentSessionId.value)
})

const sessionDisplayName = computed(() => {
  if (!currentSessionId.value) return '新对话'
  const session = currentSession.value
  if (session) {
    const count = session.message_count || 0
    return `对话 ${currentSessionId.value.slice(0, 8)} (${count} 条消息)`
  }
  return `对话 ${currentSessionId.value.slice(0, 8)}`
})

onMounted(() => {
  initSession()
  
  registerShortcut({
    key: 'n',
    ctrl: true,
    handler: createNewSession,
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
  
  const validSession = sessions.value.find(s => s.message_count > 0)
  if (validSession) {
    currentSessionId.value = validSession.id
    localStorage.setItem(STORAGE_KEY, validSession.id)
    await loadMessages()
  } else {
    await createNewSession()
  }
}

async function createNewSession() {
  try {
    const data = await post(API_ENDPOINTS.SESSIONS, { channel: 'web' })
    currentSessionId.value = data.session_id
    localStorage.setItem(STORAGE_KEY, data.session_id)
    messages.value = []
    await loadSessions()
  } catch (error) {
    console.error('创建会话失败:', error)
  }
}

async function switchSession(sessionId: string) {
  if (sessionId === currentSessionId.value) return
  
  currentSessionId.value = sessionId
  localStorage.setItem(STORAGE_KEY, sessionId)
  await loadMessages()
}

async function deleteCurrentSession() {
  if (!currentSessionId.value) return
  if (!confirm('确定要删除当前会话吗？')) return

  try {
    await del(API_ENDPOINTS.SESSION_DETAIL(currentSessionId.value))
    localStorage.removeItem(STORAGE_KEY)
    await initSession()
  } catch (error) {
    console.error('删除会话失败:', error)
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
      localStorage.removeItem(STORAGE_KEY)
      await initSession()
    } else {
      console.error('加载消息失败:', error)
      messages.value = []
    }
  }
}

async function sendMessage(content: string) {
  if (!content.trim()) return

  if (isLoading.value) {
    if (abortController) {
      abortController.abort()
      abortController = null
    }
    isLoading.value = false
  }

  if (!currentSessionId.value) {
    await createNewSession()
    if (!currentSessionId.value) {
      console.error('无法创建会话')
      return
    }
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
      <div class="chat-controls">
        <div class="session-selector">
          <select
            :value="currentSessionId"
            @change="switchSession(($event.target as HTMLSelectElement).value)"
            class="session-select"
          >
            <option value="" disabled>选择会话...</option>
            <option
              v-for="session in sessions"
              :key="session.id"
              :value="session.id"
            >
              对话 {{ session.id.slice(0, 8) }} ({{ session.message_count }} 条消息)
            </option>
          </select>
        </div>
        
        <button @click="createNewSession" class="btn btn-new" title="新建对话">
          <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          <span>新建</span>
        </button>
        
        <button
          v-if="currentSessionId"
          @click="deleteCurrentSession"
          class="btn btn-delete"
          title="删除当前对话"
        >
          <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
      </div>
      
      <div class="session-info">
        <span class="session-title">{{ sessionDisplayName }}</span>
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
    </footer>
  </div>
</template>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: hsl(var(--card) / 0.5);
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  background: hsl(var(--card) / 0.8);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid hsl(var(--border));
}

.chat-controls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.session-selector {
  position: relative;
}

.session-select {
  appearance: none;
  padding: 0.5rem 2rem 0.5rem 0.75rem;
  background: hsl(var(--muted) / 0.5);
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius);
  font-size: 0.875rem;
  color: hsl(var(--foreground));
  cursor: pointer;
  min-width: 200px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%236b7280'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 0.5rem center;
  background-size: 1.25rem;
}

.session-select:hover {
  border-color: hsl(var(--primary) / 0.5);
}

.session-select:focus {
  outline: none;
  border-color: hsl(var(--primary));
  box-shadow: 0 0 0 2px hsl(var(--primary) / 0.2);
}

.session-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.session-title {
  font-size: 0.75rem;
  color: hsl(var(--muted-foreground));
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 0.75rem;
  border-radius: var(--radius);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid hsl(var(--border));
}

.btn .icon {
  width: 1rem;
  height: 1rem;
}

.btn-new {
  background: hsl(var(--primary));
  color: hsl(var(--primary-foreground));
  border-color: hsl(var(--primary));
}

.btn-new:hover {
  opacity: 0.9;
}

.btn-delete {
  background: transparent;
  color: hsl(var(--muted-foreground));
}

.btn-delete:hover {
  background: hsl(var(--destructive) / 0.1);
  color: hsl(var(--destructive));
  border-color: hsl(var(--destructive) / 0.5);
}

.chat-footer {
  padding: 1rem;
  background: hsl(var(--background) / 0.8);
  backdrop-filter: blur(10px);
  border-top: 1px solid hsl(var(--border));
}

@media (max-width: 768px) {
  .chat-header {
    flex-direction: column;
    gap: 0.5rem;
    align-items: stretch;
  }
  
  .chat-controls {
    flex-wrap: wrap;
  }
  
  .session-select {
    min-width: 150px;
    flex: 1;
  }
  
  .btn-new span {
    display: none;
  }
}
</style>
