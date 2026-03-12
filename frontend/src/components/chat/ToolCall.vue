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
  if (props.toolCall.durationMs === undefined || props.toolCall.durationMs === null) return null
  const ms = props.toolCall.durationMs
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
        <pre class="section-content">{{ typeof toolCall.result === 'string' ? toolCall.result : JSON.stringify(toolCall.result, null, 2) }}</pre>
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
  margin: 0.25rem 0;
  border-radius: 8px;
  border: 1px solid hsl(var(--border));
  overflow: hidden;
  background: hsl(var(--card));
}

.tool-call.status-pending {
  border-color: hsl(var(--primary) / 0.3);
  background: hsl(var(--primary) / 0.05);
}

.tool-call.status-running {
  border-color: hsl(var(--primary) / 0.3);
  background: hsl(var(--primary) / 0.05);
}

.tool-call.status-success {
  border-color: hsl(var(--primary) / 0.2);
}

.tool-call.status-error {
  border-color: hsl(var(--destructive) / 0.3);
  background: hsl(var(--destructive) / 0.05);
}

.tool-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  cursor: pointer;
  user-select: none;
  transition: background 0.2s;
}

.tool-header:hover {
  background: hsl(var(--muted) / 0.3);
}

.status-icon {
  font-size: 0.75rem;
}

.tool-name {
  flex: 1;
  font-weight: 500;
  font-size: 0.75rem;
  color: hsl(var(--foreground));
  font-family: ui-monospace, monospace;
}

.duration {
  font-size: 0.625rem;
  color: hsl(var(--muted-foreground));
  font-family: ui-monospace, monospace;
}

.expand-icon {
  width: 0.875rem;
  height: 0.875rem;
  color: hsl(var(--muted-foreground));
  transition: transform 0.2s;
}

.expand-icon.expanded {
  transform: rotate(90deg);
}

.tool-body {
  padding: 0 0.75rem 0.5rem;
}

.section {
  margin-top: 0.375rem;
}

.section-label {
  font-size: 0.625rem;
  font-weight: 500;
  color: hsl(var(--muted-foreground));
  margin-bottom: 0.125rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.section-content {
  margin: 0;
  padding: 0.5rem;
  background: hsl(var(--muted) / 0.3);
  border-radius: 6px;
  font-size: 0.6875rem;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: ui-monospace, monospace;
  color: hsl(var(--foreground));
  max-height: 200px;
  overflow-y: auto;
}

.section.error .section-content {
  color: hsl(var(--destructive));
}
</style>
