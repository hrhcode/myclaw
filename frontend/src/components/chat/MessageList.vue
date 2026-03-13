<script setup lang="ts">
/**
 * MessageList 消息列表组件
 * 支持智能滚动：当用户向上滚动时暂停自动滚动，滚动到底部时恢复
 */
import type { Message } from '../../types'
import MessageItem from './MessageItem.vue'
import { ref, nextTick, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps<{
  messages: Message[]
  isLoading: boolean
}>()

const emit = defineEmits<{
  (e: 'edit', id: number): void
  (e: 'regenerate', id: number): void
}>()

const containerRef = ref<HTMLElement | null>(null)
const expandedTools = ref<Record<string, boolean>>({})

/**
 * 是否应该自动滚动到底部
 * 当用户向上滚动时设为false，滚动到底部时设为true
 */
const shouldAutoScroll = ref(true)

/**
 * 是否是初始加载（用于区分初始滚动和后续滚动）
 */
const isInitialLoad = ref(true)

/**
 * 滚动阈值（距离底部多少像素内认为是"到底部"）
 */
const SCROLL_THRESHOLD = 100

/**
 * 检查是否滚动到底部
 */
function isScrolledToBottom(): boolean {
  if (!containerRef.value) return true
  
  const { scrollTop, scrollHeight, clientHeight } = containerRef.value
  return scrollHeight - scrollTop - clientHeight < SCROLL_THRESHOLD
}

/**
 * 滚动到底部
 * @param instant 是否立即滚动（无动画）
 */
function scrollToBottom(instant: boolean = false) {
  if (!shouldAutoScroll.value) return
  
  nextTick(() => {
    if (containerRef.value) {
      containerRef.value.scrollTo({
        top: containerRef.value.scrollHeight,
        behavior: instant ? 'instant' : 'smooth'
      })
    }
  })
}

/**
 * 处理滚动事件
 * 检测用户是否手动滚动，并更新自动滚动状态
 */
function handleScroll() {
  if (!containerRef.value) return
  
  const isAtBottom = isScrolledToBottom()
  
  // 如果用户滚动到了底部，恢复自动滚动
  if (isAtBottom) {
    shouldAutoScroll.value = true
  }
}

/**
 * 处理鼠标滚轮事件
 * 当用户向上滚动时，暂停自动滚动
 */
function handleWheel(event: WheelEvent) {
  if (!containerRef.value) return
  
  // 如果向上滚动（deltaY < 0），暂停自动滚动
  if (event.deltaY < 0) {
    shouldAutoScroll.value = false
  }
}

/**
 * 监听消息变化，自动滚动到底部
 */
watch(() => props.messages.length, () => {
  if (isInitialLoad.value && props.messages.length > 0) {
    scrollToBottom(true)
    isInitialLoad.value = false
  } else {
    scrollToBottom()
  }
})
watch(() => props.messages[props.messages.length - 1]?.content, scrollToBottom)

/**
 * 添加滚动事件监听
 */
onMounted(() => {
  if (containerRef.value) {
    containerRef.value.addEventListener('scroll', handleScroll, { passive: true })
    containerRef.value.addEventListener('wheel', handleWheel, { passive: true })
  }
})

/**
 * 移除滚动事件监听
 */
onUnmounted(() => {
  if (containerRef.value) {
    containerRef.value.removeEventListener('scroll', handleScroll)
    containerRef.value.removeEventListener('wheel', handleWheel)
  }
})
</script>

<template>
  <div ref="containerRef" class="message-list">
    <div class="messages-container">
      <div v-if="messages.length === 0" class="empty-state">
        <div class="empty-icon-wrapper">
          <svg class="empty-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
          <div class="empty-glow" />
        </div>
        <h3 class="empty-title">开始一段新对话吧</h3>
        <p class="empty-subtitle">输入您的问题，AI 将为您提供帮助</p>
      </div>
      
      <TransitionGroup name="message" tag="div" class="message-items">
        <MessageItem
          v-for="(message, index) in messages"
          :key="message.id"
          :message="message"
          :is-generating="isLoading && index === messages.length - 1"
          v-model:expandedTools="expandedTools"
          @edit="emit('edit', $event)"
          @regenerate="emit('regenerate', $event)"
        />
      </TransitionGroup>
    </div>
  </div>
</template>

<style scoped>
.message-list {
  flex: 1 1 0;
  min-height: 0;
  overflow-y: auto;
  padding: 1.5rem;
}

.messages-container {
  max-width: 48rem;
  margin: 0 auto;
}

.message-items {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 300px;
  text-align: center;
}

.empty-icon-wrapper {
  position: relative;
  margin-bottom: 1.5rem;
}

.empty-icon {
  width: 5rem;
  height: 5rem;
  color: hsl(var(--muted-foreground));
  opacity: 0.5;
  animation: float 3s ease-in-out infinite;
}

.empty-glow {
  position: absolute;
  inset: -20px;
  background: radial-gradient(circle, hsl(var(--primary) / 0.2) 0%, transparent 70%);
  filter: blur(20px);
  animation: pulse 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

@keyframes pulse {
  0%, 100% { opacity: 0.5; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.1); }
}

.empty-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: hsl(var(--foreground));
  margin: 0 0 0.5rem 0;
}

.empty-subtitle {
  font-size: 0.875rem;
  color: hsl(var(--muted-foreground));
  margin: 0;
}

.message-enter-active {
  animation: message-in 0.4s ease-out;
}

.message-leave-active {
  animation: message-out 0.3s ease-in;
}

@keyframes message-in {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes message-out {
  from {
    opacity: 1;
    transform: translateY(0);
  }
  to {
    opacity: 0;
    transform: translateY(-20px);
  }
}
</style>
