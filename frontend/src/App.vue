<script setup lang="ts">
import { ref, nextTick, onMounted, watch } from 'vue'
import { marked } from 'marked'
import './highlight.css'

interface Message {
  id: number
  role: string
  content: string
  timestamp?: string
}

interface Session {
  id: string
  channel: string
  message_count: number
  created_at: string
  updated_at: string
}

const messages = ref<Message[]>([])
const inputMessage = ref('')
const isLoading = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)
const sidebarOpen = ref(true)

const sessions = ref<Session[]>([])
const currentSessionId = ref<string>('')
const isLoadingSessions = ref(false)

const STORAGE_KEY = 'myclaw_session_id'

/**
 * 从 localStorage 恢复或创建会话
 */
async function initSession() {
  const savedSessionId = localStorage.getItem(STORAGE_KEY)
  
  if (savedSessionId) {
    currentSessionId.value = savedSessionId
    await loadMessages()
  } else {
    await createNewSession()
  }
  
  await loadSessions()
}

/**
 * 创建新会话
 */
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

/**
 * 切换会话
 */
async function switchSession(sessionId: string) {
  if (sessionId === currentSessionId.value) return
  
  currentSessionId.value = sessionId
  localStorage.setItem(STORAGE_KEY, sessionId)
  await loadMessages()
}

/**
 * 删除会话
 */
async function deleteSession(sessionId: string, event: Event) {
  event.stopPropagation()
  
  if (!confirm('确定要删除这个会话吗？')) return
  
  try {
    await fetch(`/v1/sessions/${sessionId}`, { method: 'DELETE' })
    
    if (sessionId === currentSessionId.value) {
      localStorage.removeItem(STORAGE_KEY)
      await createNewSession()
    }
    
    await loadSessions()
  } catch (error) {
    console.error('删除会话失败:', error)
  }
}

/**
 * 加载会话列表
 */
async function loadSessions() {
  isLoadingSessions.value = true
  try {
    const response = await fetch('/v1/sessions?limit=20')
    const data = await response.json()
    sessions.value = data.sessions
  } catch (error) {
    console.error('加载会话列表失败:', error)
  } finally {
    isLoadingSessions.value = false
  }
}

/**
 * 加载当前会话的消息
 */
async function loadMessages() {
  if (!currentSessionId.value) return
  
  try {
    const response = await fetch(`/v1/sessions/${currentSessionId.value}/messages`)
    const data = await response.json()
    messages.value = data.messages.map((m: Message) => ({
      id: m.id,
      role: m.role,
      content: m.content,
      timestamp: m.timestamp,
    }))
    scrollToBottom()
  } catch (error) {
    console.error('加载消息失败:', error)
    messages.value = []
  }
}

/**
 * 发送消息
 */
async function sendMessage() {
  if (!inputMessage.value.trim() || isLoading.value) return
  
  const userMessage = inputMessage.value.trim()
  inputMessage.value = ''
  
  messages.value.push({
    id: Date.now(),
    role: 'user',
    content: userMessage,
    timestamp: new Date().toISOString(),
  })
  
  scrollToBottom()
  
  isLoading.value = true
  
  try {
    const response = await fetch('/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        messages: [{ role: 'user', content: userMessage }],
        session_id: currentSessionId.value,
      }),
    })
    
    const data = await response.json()
    const assistantMessage = data.choices[0].message.content
    
    messages.value.push({
      id: Date.now() + 1,
      role: 'assistant',
      content: assistantMessage,
      timestamp: new Date().toISOString(),
    })
    
    scrollToBottom()
    await loadSessions()
  } catch (error) {
    console.error('发送消息失败:', error)
    messages.value.push({
      id: Date.now() + 1,
      role: 'assistant',
      content: '抱歉，发生了错误，请稍后再试。',
      timestamp: new Date().toISOString(),
    })
  } finally {
    isLoading.value = false
  }
}

/**
 * 滚动到底部
 */
function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

/**
 * 格式化时间
 */
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

/**
 * 格式化会话时间
 */
function formatSessionTime(timestamp: string) {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (days === 0) {
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  } else if (days === 1) {
    return '昨天'
  } else if (days < 7) {
    return `${days}天前`
  } else {
    return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
  }
}

onMounted(() => {
  initSession()
})
</script>

<template>
  <div class="flex h-screen bg-gray-100">
    <aside
      :class="[
        'bg-white border-r border-gray-200 flex flex-col transition-all duration-300',
        sidebarOpen ? 'w-64' : 'w-0 overflow-hidden'
      ]"
    >
      <div class="p-4 border-b border-gray-200">
        <button
          @click="createNewSession"
          class="w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors flex items-center justify-center space-x-2"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          <span>新对话</span>
        </button>
      </div>
      
      <div class="flex-1 overflow-y-auto">
        <div v-if="isLoadingSessions" class="p-4 text-center text-gray-500">
          加载中...
        </div>
        <div v-else-if="sessions.length === 0" class="p-4 text-center text-gray-400">
          暂无对话记录
        </div>
        <div v-else>
          <div
            v-for="session in sessions"
            :key="session.id"
            @click="switchSession(session.id)"
            :class="[
              'p-4 border-b border-gray-100 cursor-pointer hover:bg-gray-50 transition-colors group',
              session.id === currentSessionId ? 'bg-blue-50 border-l-2 border-l-blue-500' : ''
            ]"
          >
            <div class="flex items-center justify-between">
              <div class="flex-1 min-w-0">
                <div class="text-sm font-medium text-gray-800 truncate">
                  对话 {{ session.id.slice(0, 8) }}
                </div>
                <div class="text-xs text-gray-500 mt-1">
                  {{ session.message_count }} 条消息 · {{ formatSessionTime(session.updated_at) }}
                </div>
              </div>
              <button
                @click="deleteSession(session.id, $event)"
                class="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500 transition-all"
                title="删除对话"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </aside>

    <div class="flex-1 flex flex-col">
      <header class="bg-white shadow-sm border-b border-gray-200 px-6 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-3">
            <button
              @click="sidebarOpen = !sidebarOpen"
              class="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <h1 class="text-xl font-bold text-gray-800">MyClaw</h1>
          </div>
          <span class="text-sm text-gray-500">AI 助手</span>
        </div>
      </header>

      <main ref="messagesContainer" class="flex-1 overflow-y-auto p-6">
        <div class="max-w-4xl mx-auto space-y-4">
          <div v-if="messages.length === 0" class="flex items-center justify-center h-full">
            <div class="text-center text-gray-400">
              <svg class="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              <p>开始一段新对话吧</p>
            </div>
          </div>
          
          <div
            v-for="message in messages"
            :key="message.id"
            :class="[
              'flex',
              message.role === 'user' ? 'justify-end' : 'justify-start'
            ]"
          >
            <div
              :class="[
                'max-w-[80%] rounded-lg px-4 py-3',
                message.role === 'user'
                  ? 'bg-blue-500 text-white'
                  : 'bg-white text-gray-800 shadow-sm border border-gray-200'
              ]"
            >
              <div
                v-if="message.role === 'assistant'"
                class="prose prose-sm max-w-none"
                v-html="marked(message.content)"
              ></div>
              <div v-else class="whitespace-pre-wrap">{{ message.content }}</div>
              <div
                :class="[
                  'text-xs mt-2',
                  message.role === 'user' ? 'text-blue-100' : 'text-gray-400'
                ]"
              >
                {{ formatTime(message.timestamp) }}
              </div>
            </div>
          </div>
          
          <div v-if="isLoading" class="flex justify-start">
            <div class="bg-white text-gray-800 shadow-sm border border-gray-200 rounded-lg px-4 py-3">
              <div class="flex items-center space-x-2">
                <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0s"></div>
                <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
              </div>
            </div>
          </div>
        </div>
      </main>

      <footer class="bg-white border-t border-gray-200 px-6 py-4">
        <div class="max-w-4xl mx-auto">
          <form @submit.prevent="sendMessage" class="flex space-x-4">
            <input
              v-model="inputMessage"
              type="text"
              placeholder="输入消息..."
              class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              :disabled="isLoading"
            />
            <button
              type="submit"
              class="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
              :disabled="isLoading || !inputMessage.trim()"
            >
              发送
            </button>
          </form>
        </div>
      </footer>
    </div>
  </div>
</template>
