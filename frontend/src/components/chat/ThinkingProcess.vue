<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  thoughts: string
}>()

const isExpanded = ref(true)

function toggleExpand() {
  isExpanded.value = !isExpanded.value
}
</script>

<template>
  <div class="thinking-process">
    <div class="thinking-header" @click="toggleExpand">
      <div class="thinking-title">
        <svg class="thinking-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
        <span>思考过程</span>
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
    
    <Transition name="thinking-content">
      <div v-if="isExpanded" class="thinking-body">
        <div class="thinking-content">{{ thoughts }}</div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.thinking-process {
  margin: 0.5rem 0;
  border-radius: 8px;
  border: 1px solid hsl(var(--primary) / 0.3);
  background: hsl(var(--primary) / 0.05);
  overflow: hidden;
}

.thinking-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  cursor: pointer;
  user-select: none;
  transition: background 0.2s;
}

.thinking-header:hover {
  background: hsl(var(--primary) / 0.1);
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
}

.thinking-title span {
  font-size: 0.75rem;
  font-weight: 500;
  color: hsl(var(--primary));
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
  padding: 0 0.75rem 0.5rem;
}

.thinking-content {
  padding: 0.5rem;
  background: hsl(var(--muted) / 0.3);
  border-radius: 6px;
  font-size: 0.75rem;
  line-height: 1.6;
  color: hsl(var(--foreground));
  white-space: pre-wrap;
  word-break: break-word;
  font-family: ui-monospace, monospace;
}

.thinking-content-enter-active {
  animation: thinking-in 0.2s ease-out;
}

.thinking-content-leave-active {
  animation: thinking-out 0.2s ease-in;
}

@keyframes thinking-in {
  from {
    opacity: 0;
    transform: translateY(-5px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes thinking-out {
  from {
    opacity: 1;
    transform: translateY(0);
  }
  to {
    opacity: 0;
    transform: translateY(-5px);
  }
}
</style>
