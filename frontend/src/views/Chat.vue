<script setup lang="ts">
/**
 * Chat 聊天页面
 * 参考 OpenClaw 设计，简洁的聊天界面
 */
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import type { Message, Session, Model } from '@/types'
import MessageList from '@/components/chat/MessageList.vue'
import MessageInput from '@/components/input/MessageInput.vue'
import CustomSelect from '@/components/ui/CustomSelect.vue'
import { useKeyboard } from '@/composables/useKeyboard'
import { useSystem } from '@/composables/useSystem'
import { post, del, get, stream } from '@/utils/request'
import { API_ENDPOINTS } from '@/config/api'

const messages = ref<Message[]>([])
const isLoading = ref(false)

const sessions = ref<Session[]>([])
const currentSessionId = ref<string>('main')
const isLoadingSessions = ref(false)

const models = ref<Model[]>([])
const currentModel = ref<string>('')
const isLoadingModels = ref(false)

const { systemInfo, fetchSystemInfo } = useSystem()

const sessionOptions = computed(() => 
  sessions.value.map(s => ({
    value: s.id,
    label: s.id.slice(0, 8)
  }))
)

const modelOptions = computed(() => 
  models.value.map(m => ({
    value: m.id,
    label: m.name
  }))
)

let abortController: AbortController | null = null
const inputRef = ref<InstanceType<typeof MessageInput> | null>(null)
const STORAGE_KEY = 'myclaw_session_id'
const MODEL_STORAGE_KEY = 'myclaw_model'
const THINKING_STORAGE_KEY = 'myclaw_thinking_enabled'

const enableThinking = ref<boolean>(false)

const shouldShowThinkingToggle = computed(() => {
  return currentModel.value.toLowerCase().includes('thinking')
})

function isVisionSupported(model: string): boolean {
  return model.includes('v') || model.toLowerCase().includes('thinking')
}

const { registerShortcut } = useKeyboard()

onMounted(() => {
  initSession()
  fetchSystemInfo()
  loadModels()
  
  const savedThinkingEnabled = localStorage.getItem(THINKING_STORAGE_KEY)
  if (savedThinkingEnabled !== null) {
    enableThinking.value = savedThinkingEnabled === 'true'
  }
  
  const savedModel = localStorage.getItem(MODEL_STORAGE_KEY)
  if (savedModel) {
    currentModel.value = savedModel
  }
  
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

watch(enableThinking, (newValue) => {
  localStorage.setItem(THINKING_STORAGE_KEY, String(newValue))
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
  
  const mainSession = sessions.value.find(s => s.id === 'main')
  if (mainSession) {
    currentSessionId.value = 'main'
    localStorage.setItem(STORAGE_KEY, 'main')
    await loadMessages()
  } else {
    currentSessionId.value = 'main'
    localStorage.setItem(STORAGE_KEY, 'main')
    messages.value = []
  }
}

async function loadSessions() {
  isLoadingSessions.value = true
  try {
    const data = await get(`${API_ENDPOINTS.SESSIONS}?limit=20`)
    sessions.value = (data.sessions || []).filter((s: Session) => s.id === 'main' || s.message_count > 0)
  } catch (error) {
    console.error('加载会话列表失败:', error)
    sessions.value = []
  } finally {
    isLoadingSessions.value = false
  }
}

async function loadModels() {
  isLoadingModels.value = true
  try {
    const data = await get(API_ENDPOINTS.MODELS)
    models.value = data.models || []
    
    if (!currentModel.value && data.default_model) {
      currentModel.value = data.default_model
    }
    
    if (currentModel.value && !models.value.find(m => m.id === currentModel.value)) {
      currentModel.value = data.default_model || ''
    }
  } catch (error) {
    console.error('加载模型列表失败:', error)
    models.value = []
  } finally {
    isLoadingModels.value = false
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

      if (m.thoughts) {
        message.thoughts = m.thoughts
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

async function switchModel(modelId: string) {
  if (modelId === currentModel.value) return
  
  currentModel.value = modelId
  localStorage.setItem(MODEL_STORAGE_KEY, modelId)
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

async function sendMessage(content: string, image?: string) {
  if (!content.trim() && !image) return
  
  if (isResetCommand(content)) {
    await handleResetCommand(content)
    return
  }
  
  await sendMessageInternal(content, image)
}

async function sendMessageInternal(content: string, image?: string) {
  if (!content.trim() && !image) return
  
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

  const userMessage: Message = {
    id: Date.now(),
    role: 'user',
    content: content,
    timestamp: new Date().toISOString(),
  }
  
  if (image) {
    userMessage.image = image
  }
  
  messages.value.push(userMessage)

  isLoading.value = true

  const assistantMessageId = Date.now() + 1
  messages.value.push({
    id: assistantMessageId,
    role: 'assistant',
    content: '',
    timestamp: new Date().toISOString(),
    thoughts: '',
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
    const modelToUse = currentModel.value || systemInfo.value?.llm?.model || ''
    const isVisionCapable = isVisionSupported(modelToUse)
    
    const requestBody: any = {
      messages: [{ role: 'user', content }],
      session_id: currentSessionId.value,
      model: currentModel.value,
      stream: true,
      enable_thinking: enableThinking.value,
    }
    
    if (image && isVisionCapable) {
      requestBody.image = image
    }
    
    abortController = stream(
      API_ENDPOINTS.CHAT_COMPLETIONS,
      requestBody,
      (parsed) => {
        if (parsed.choices && parsed.choices[0]?.delta) {
          const delta = parsed.choices[0].delta
          const msgIndex = messages.value.findIndex(m => m.id === assistantMessageId)

          if (msgIndex === -1) return
          
          const msg = messages.value[msgIndex]

          if (delta.content) {
            console.log('[流式内容]', delta.content)
            msg.content += delta.content
          }

          if (delta.thoughts) {
            console.log('[流式思考]', delta.thoughts)
            // 使用与正文相同的方式更新
            msg.thoughts = (msg.thoughts || '') + delta.thoughts
          }

          if (delta.tool_calls && delta.tool_calls.length > 0) {
            const toolCall = delta.tool_calls[0]

            if (!msg.toolCalls) {
              msg.toolCalls = []
            }

            const existingToolIndex = msg.toolCalls.findIndex(
              t => t.id === toolCall.id
            )

            if (existingToolIndex === -1) {
              msg.toolCalls.push({
                id: toolCall.id,
                name: toolCall.name,
                arguments: toolCall.arguments || {},
                status: toolCall.status || 'running',
                result: toolCall.result,
                durationMs: toolCall.duration_ms,
              })
            } else {
              const existingTool = msg.toolCalls[existingToolIndex]
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
        <CustomSelect
          v-model="currentSessionId"
          :options="sessionOptions"
          @update:model-value="switchSession"
        />
      </div>
      <div class="model-selector">
        <CustomSelect
          v-model="currentModel"
          :options="modelOptions"
          placeholder="选择模型"
          @update:model-value="switchModel"
        />
      </div>
      <button
        v-if="shouldShowThinkingToggle"
        class="thinking-btn"
        :class="{ active: enableThinking }"
        @click="enableThinking = !enableThinking"
        title="深度思考"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 2a7 7 0 0 1 7 7c0 2.38-1.19 4.47-3 5.74V17a2 2 0 0 1-2 2H10a2 2 0 0 1-2-2v-2.26C6.19 13.47 5 11.38 5 9a7 7 0 0 1 7-7z"/>
          <path d="M9 21h6"/>
          <path d="M12 17v4"/>
        </svg>
      </button>
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
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 1rem;
  background: hsl(var(--card) / 0.8);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid hsl(var(--border));
  flex-shrink: 0;
  z-index: 100;
}

.session-selector {
  position: relative;
}

.model-selector {
  position: relative;
}

.thinking-toggle {
  margin-left: auto;
}

.thinking-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  padding: 0;
  margin-left: auto;
  background: hsl(var(--background));
  border: 1px solid hsl(var(--border));
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
  color: hsl(var(--muted-foreground));
}

.thinking-btn:hover {
  background: hsl(var(--muted) / 0.5);
  border-color: hsl(var(--muted-foreground) / 0.3);
  color: hsl(var(--foreground));
}

.thinking-btn.active {
  background: hsl(var(--primary) / 0.1);
  border-color: hsl(var(--primary) / 0.5);
  color: hsl(var(--primary));
  box-shadow: 0 0 0 3px hsl(var(--primary) / 0.1);
}

.thinking-btn svg {
  width: 18px;
  height: 18px;
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
  
  .session-title {
    display: none;
  }
}
</style>
