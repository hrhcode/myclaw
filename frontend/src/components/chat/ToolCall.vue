<script setup lang="ts">
import { computed } from 'vue'
import type { ToolCall } from '../../types'

const props = defineProps<{
  toolCall: ToolCall
}>()

const isExpanded = defineModel<boolean>('expanded', { default: false })

const statusIcon = computed(() => {
  switch (props.toolCall.status) {
    case 'pending': return '⏳'
    case 'running': return '🔄'
    case 'success': return '✅'
    case 'error': return '❌'
    default: return '❓'
  }
})

const statusClass = computed(() => {
  return `status-${props.toolCall.status}`
})

const duration = computed(() => {
  if (!props.toolCall.endTime) return null
  const ms = props.toolCall.endTime - props.toolCall.startTime
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
})
</script>

<template>
  <div class="tool-call" :class="statusClass">
    <div class="tool-header" @click="isExpanded = !isExpanded">
      <span class="status-icon">{{ statusIcon }}</span>
      <span class="tool-name">{{ toolCall.name }}</span>
      <span v-if="duration" class="duration">{{ duration }}</span>
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
    
    <div v-if="isExpanded" class="tool-body">
      <div class="section">
        <div class="section-label">参数</div>
        <pre class="section-content">{{ JSON.stringify(toolCall.arguments, null, 2) }}</pre>
      </div>
      
      <div v-if="toolCall.result !== undefined" class="section">
        <div class="section-label">结果</div>
        <pre class="section-content">{{ JSON.stringify(toolCall.result, null, 2) }}</pre>
      </div>
      
      <div v-if="toolCall.error" class="section error">
        <div class="section-label">错误</div>
        <pre class="section-content">{{ toolCall.error }}</pre>
      </div>
    </div>
  </div>
</template>

<style scoped>
.tool-call {
  margin: 0.5rem 0;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  overflow: hidden;
}

.tool-call.status-pending {
  background: var(--color-tool-pending);
}

.tool-call.status-running {
  background: var(--color-tool-pending);
}

.tool-call.status-success {
  background: var(--color-tool-success);
}

.tool-call.status-error {
  background: var(--color-tool-error);
}

.tool-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  cursor: pointer;
  user-select: none;
}

.tool-header:hover {
  background: rgba(0, 0, 0, 0.05);
}

.status-icon {
  font-size: 0.875rem;
}

.tool-name {
  flex: 1;
  font-weight: 500;
  font-size: 0.875rem;
  color: var(--color-text-primary);
}

.duration {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

.expand-icon {
  width: 1rem;
  height: 1rem;
  color: var(--color-text-tertiary);
  transition: transform 0.2s;
}

.expand-icon.expanded {
  transform: rotate(90deg);
}

.tool-body {
  padding: 0 1rem 1rem;
}

.section {
  margin-top: 0.5rem;
}

.section-label {
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--color-text-tertiary);
  margin-bottom: 0.25rem;
}

.section-content {
  margin: 0;
  padding: 0.75rem;
  background: rgba(0, 0, 0, 0.1);
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

.section.error .section-content {
  color: var(--color-error);
}
</style>
