<script setup lang="ts">
/**
 * ThinkingProcess 思考过程展示组件
 * 支持打字机效果和光标闪烁动画，增强用户体验
 * 思考结束后自动折叠
 */
import { ref, computed, watch, nextTick } from 'vue'

const props = defineProps<{
  thoughts: string
  isGenerating?: boolean
}>()

/**
 * 默认折叠状态
 * 历史消息（非生成中）默认折叠
 * 正在生成的消息默认展开
 */
const isExpanded = ref(props.isGenerating === true)

/**
 * 是否正在思考中（有思考内容且正在生成）
 */
const isActivelyThinking = computed(() => {
  return props.isGenerating === true && props.thoughts.length > 0
})

/**
 * 监听生成状态变化
 * 生成结束时自动折叠
 */
watch(() => props.isGenerating, (newValue, oldValue) => {
  console.log('[ThinkingProcess] isGenerating 变化:', oldValue, '->', newValue)
  if (oldValue === true && newValue === false) {
    isExpanded.value = false
  }
}, { flush: 'sync' })

/**
 * 监听思考内容变化
 * 当思考内容开始输出时自动展开
 */
watch(() => props.thoughts, (newValue, oldValue) => {
  console.log('[ThinkingProcess] thoughts 变化:', oldValue?.length, '->', newValue?.length)
  if (newValue && newValue.length > 0 && props.isGenerating && !isExpanded.value) {
    console.log('[ThinkingProcess] 自动展开')
    isExpanded.value = true
  }
}, { flush: 'sync' })

function toggleExpand() {
  isExpanded.value = !isExpanded.value
}
</script>

<template>
  <div class="thinking-process" :class="{ 'is-thinking': isActivelyThinking }">
    <div class="thinking-header" @click="toggleExpand">
      <div class="thinking-title">
        <svg class="thinking-icon" :class="{ 'animate-pulse': isActivelyThinking }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
        <span>思考过程</span>
        <span v-if="isActivelyThinking" class="thinking-status">思考中...</span>
      </div>
      <svg 
        class="expand-icon" 
        :class="{ expanded: isExpanded }"
        fill="none" 
        stroke="currentColor" 
        viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
      </svg>
    </div>
    
    <div v-show="isExpanded" class="thinking-body">
      <div class="thinking-content">
        <span class="thinking-text">{{ thoughts }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.thinking-process {
  margin: 0.5rem 0;
  overflow: hidden;
  transition: all 0.3s ease;
}

.thinking-process.is-thinking {
}

.thinking-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.25rem 0;
  cursor: pointer;
  user-select: none;
  transition: background 0.2s;
}

.thinking-header:hover {
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
  transition: all 0.3s ease;
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

@keyframes fade-pulse {
  0%, 100% {
    opacity: 0.5;
  }
  50% {
    opacity: 1;
  }
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
  position: relative;
  min-height: 2rem;
}

.thinking-text {
  display: inline;
}
</style>
