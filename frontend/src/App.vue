<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import type { Message, Session } from './types'
import Sidebar from './components/sidebar/Sidebar.vue'
import MessageList from './components/chat/MessageList.vue'
import MessageInput from './components/input/MessageInput.vue'
import ThemeToggle from './components/common/ThemeToggle.vue'
import { useKeyboard } from './composables/useKeyboard'

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
    const response = await fetch('/v1/sessions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ channel: 'web' }),
    })
    const data = await response.json()
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
    await fetch(`/v1/sessions/${sessionId}`, { method: 'DELETE' })
    
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
    const response = await fetch('/v1/sessions?limit=20')
    const data = await response.json()
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
    const response = await fetch(`/v1/sessions/${currentSessionId.value}/messages`)
    
    if (!response.ok) {
      if (response.status === 404) {
        messages.value = []
        localStorage.removeItem(STORAGE_KEY)
        await initSession()
      }
      return
    }
    
    const data = await response.json()
    const processedMessages: Message[] = []
    const toolResults: Record<string, string> = {}
    
    // 第一遍：收集所有工具结果
    for (const m of data.messages || []) {
      if (m.role === 'tool' && m.tool_call_id) {
        toolResults[m.tool_call_id] = m.content
      }
    }
    
    // 第二遍：处理消息
    for (const m of data.messages || []) {
      if (m.role === 'tool') {
        // 跳过独立的 tool 消息，它们会被合并到 assistant 消息中
        continue
      }
      
      const message: Message = {
        id: m.id,
        role: m.role,
        content: m.content || '',
        timestamp: m.timestamp,
      }
      
      // 处理工具调用
      if (m.tool_calls && m.tool_calls.length > 0) {
        message.toolCalls = m.tool_calls.map((tc: any) => ({
          id: tc.id,
          name: tc.function?.name || tc.name,
          arguments: tc.function?.arguments ? JSON.parse(tc.function.arguments) : (tc.arguments || {}),
          status: toolResults[tc.id] ? 'success' : 'running',
          result: toolResults[tc.id],
          startTime: Date.now(),
          endTime: toolResults[tc.id] ? Date.now() : undefined,
        }))
      }
      
      processedMessages.push(message)
    }
    
    messages.value = processedMessages
  } catch (error) {
    console.error('加载消息失败:', error)
    messages.value = []
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
  abortController = new AbortController()
  
  const assistantMessageId = Date.now() + 1
  messages.value.push({
    id: assistantMessageId,
    role: 'assistant',
    content: '',
    timestamp: new Date().toISOString(),
  })
  
  try {
    const response = await fetch('/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify({
        messages: [{ role: 'user', content }],
        session_id: currentSessionId.value,
        stream: true,
      }),
      signal: abortController.signal,
    })
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('No reader available')
    }
    
    const decoder = new TextDecoder()
    let buffer = ''
    
    while (true) {
      const { done, value } = await reader.read()
      
      if (done) break
      
      buffer += decoder.decode(value, { stream: true })
      
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          
          if (data === '[DONE]') {
            continue
          }
          
          try {
            const parsed = JSON.parse(data)
            
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
                      startTime: Date.now(),
                    })
                  } else {
                    const existingTool = messages.value[msgIndex].toolCalls![existingToolIndex]
                    if (toolCall.status) {
                      existingTool.status = toolCall.status
                    }
                    if (toolCall.result !== undefined) {
                      existingTool.result = toolCall.result
                      existingTool.endTime = Date.now()
                    }
                  }
                }
              }
            }
          } catch {
            // 忽略解析错误
          }
        }
      }
    }
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      // 请求被中止是正常行为（用户发送新消息或组件卸载）
      // 不需要显示错误信息
    } else {
      console.error('发送消息失败:', error)
      const msgIndex = messages.value.findIndex(m => m.id === assistantMessageId)
      if (msgIndex !== -1 && !messages.value[msgIndex].content) {
        messages.value[msgIndex].content = '抱歉，发生了错误，请稍后再试。'
      }
    }
  } finally {
    isLoading.value = false
    abortController = null
    loadSessions().catch(() => {})
  }
}

function handleEdit(messageId: number) {
  const message = messages.value.find(m => m.id === messageId)
  if (message && message.role === 'user') {
    // TODO: 实现编辑功能
    console.log('编辑消息:', messageId)
  }
}

function handleRegenerate(messageId: number) {
  // TODO: 实现重新生成功能
  console.log('重新生成:', messageId)
}
</script>

<template>
  <div class="app-container">
    <Sidebar
      v-model:open="sidebarOpen"
      :sessions="sessions"
      :current-session-id="currentSessionId"
      :is-loading="isLoadingSessions"
      @create="createNewSession"
      @select="switchSession"
      @delete="deleteSession"
    />

    <div class="main-content">
      <header class="header">
        <div class="header-left">
          <button
            @click="sidebarOpen = !sidebarOpen"
            class="menu-btn"
          >
            <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <h1 class="title">MyClaw</h1>
        </div>
        <div class="header-right">
          <ThemeToggle />
        </div>
      </header>

      <MessageList
        :messages="messages"
        :is-loading="isLoading"
        @edit="handleEdit"
        @regenerate="handleRegenerate"
      />

      <footer class="footer">
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
.app-container {
  display: flex;
  height: 100vh;
  background: var(--color-bg-secondary);
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  background: var(--color-header-bg);
  border-bottom: 1px solid var(--color-border);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.menu-btn {
  padding: 0.5rem;
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--color-text-secondary);
  transition: all 0.2s;
}

.menu-btn:hover {
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
}

.icon {
  width: 1.25rem;
  height: 1.25rem;
}

.title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0;
}

.footer {
  padding: 1rem 1.5rem;
  background: var(--color-bg-primary);
  border-top: 1px solid var(--color-border);
}

@media (max-width: 768px) {
  .header {
    padding: 0.75rem 1rem;
  }
  
  .footer {
    padding: 0.75rem 1rem;
  }
  
  .subtitle {
    display: none;
  }
}
</style>
