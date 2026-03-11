<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { marked } from 'marked'
import 'highlight.js/styles/github.css'

interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

const messages = ref<Message[]>([])
const inputMessage = ref('')
const isLoading = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)

const sessionId = Math.random().toString(36).substring(7)

async function sendMessage() {
  if (!inputMessage.value.trim() || isLoading.value) return
  
  const userMessage = inputMessage.value.trim()
  inputMessage.value = ''
  
  messages.value.push({
    id: Date.now(),
    role: 'user',
    content: userMessage,
    timestamp: new Date(),
  })
  
  await nextTick()
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
        session_id: sessionId,
      }),
    })
    
    const data = await response.json()
    const assistantContent = data.choices[0].message.content
    
    messages.value.push({
      id: Date.now(),
      role: 'assistant',
      content: assistantContent,
      timestamp: new Date(),
    })
    
    await nextTick()
    scrollToBottom()
  } catch (error) {
    console.error('发送消息失败:', error)
    messages.value.push({
      id: Date.now(),
      role: 'assistant',
      content: '抱歉，发生了错误，请稍后再试。',
      timestamp: new Date(),
    })
  } finally {
    isLoading.value = false
  }
}

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

function renderMarkdown(content: string): string {
  return marked(content) as string
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div class="flex flex-col h-screen bg-gray-100">
    <header class="bg-white shadow-sm border-b border-gray-200 px-6 py-4">
      <div class="flex items-center justify-between max-w-4xl mx-auto">
        <h1 class="text-xl font-bold text-gray-800">MyClaw</h1>
        <span class="text-sm text-gray-500">AI 助手</span>
      </div>
    </header>
    
    <main class="flex-1 overflow-hidden max-w-4xl w-full mx-auto bg-white">
      <div 
        ref="messagesContainer"
        class="h-full overflow-y-auto p-6 space-y-4"
      >
        <div v-if="messages.length === 0" class="flex items-center justify-center h-full">
          <div class="text-center text-gray-400">
            <p class="text-lg">开始对话</p>
            <p class="text-sm mt-2">输入消息与 AI 助手交流</p>
          </div>
        </div>
        
        <div 
          v-for="message in messages" 
          :key="message.id"
          class="flex"
          :class="message.role === 'user' ? 'justify-end' : 'justify-start'"
        >
          <div 
            class="max-w-[80%] rounded-lg px-4 py-3"
            :class="message.role === 'user' 
              ? 'bg-blue-500 text-white' 
              : 'bg-gray-100 text-gray-800'"
          >
            <div 
              v-if="message.role === 'assistant'"
              class="prose prose-sm max-w-none"
              v-html="renderMarkdown(message.content)"
            ></div>
            <p v-else class="whitespace-pre-wrap">{{ message.content }}</p>
            <p 
              class="text-xs mt-2"
              :class="message.role === 'user' ? 'text-blue-100' : 'text-gray-400'"
            >
              {{ formatTime(message.timestamp) }}
            </p>
          </div>
        </div>
        
        <div v-if="isLoading" class="flex justify-start">
          <div class="bg-gray-100 rounded-lg px-4 py-3">
            <div class="flex items-center space-x-2">
              <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
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
</template>
