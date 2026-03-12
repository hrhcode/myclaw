<script setup lang="ts">
/**
 * Chat 聊天页面
 * 提供聊天功能，复用现有组件
 */
import { ref, onMounted, onUnmounted } from 'vue'
import type { Message, Session } from '@/types'
import MessageList from '@/components/chat/MessageList.vue'
import MessageInput from '@/components/input/MessageInput.vue'
import SessionList from '@/components/sidebar/SessionList.vue'
import { useKeyboard } from '@/composables/useKeyboard'
import { post, del, get, stream } from '@/utils/request'
import { API_ENDPOINTS } from '@/config/api'

const messages = ref<Message[]>([])
const isLoading = ref(false)
const sidebarOpen = ref(true)

const sessions = ref<Session[]>([])
const currentSessionId = ref<string>('')
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
    handler: createNewSession,
    description: '新建会话'
  })
  
  registerShortcut({
    key: 'b',
    ctrl: true,
    handler: () => { sidebarOpen.value = !sidebarOpen.value },
    description: '切换侧边栏'
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

async function deleteSession(sessionId: string) {
  if (!confirm('确定要删除这个会话吗？')) return

  try {
    await del(API_ENDPOINTS.SESSION_DETAIL(sessionId))

    if (sessionId === currentSessionId.value) {
      localStorage.removeItem(STORAGE_KEY)
      await initSession()
    } else {
      await loadSessions()
    }
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
    <div class="chat-sidebar" :class="{ collapsed: !sidebarOpen }">
      <SessionList
        :sessions="sessions"
        :current-session-id="currentSessionId"
        :is-loading="isLoadingSessions"
        @create="createNewSession"
        @select="switchSession"
        @delete="deleteSession"
      />
    </div>
    
    <div class="chat-main">
      <MessageList
        :messages="messages"
        :is-loading="isLoading"
        @edit="(id) => {}"
        @regenerate="(id) => {}"
      />
      
      <footer class="chat-footer">
        <MessageInput
          ref="inputRef"
          :disabled="isLoading"
          @submit="sendMessage"
        />
      </footer>
    </div>
  </div>
</template>

<style scoped>
.chat-page {
  display: flex;
  height: 100%;
  gap: 1rem;
}

.chat-sidebar {
  width: 280px;
  flex-shrink: 0;
  transition: all 0.3s ease;
}

.chat-sidebar.collapsed {
  width: 0;
  overflow: hidden;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: hsl(var(--card) / 0.5);
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.chat-footer {
  padding: 1rem;
  background: hsl(var(--background) / 0.8);
  backdrop-filter: blur(10px);
  border-top: 1px solid hsl(var(--border));
}

@media (max-width: 768px) {
  .chat-sidebar {
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    z-index: 10;
    background: hsl(var(--background));
  }
  
  .chat-sidebar.collapsed {
    transform: translateX(-100%);
  }
}
</style>
