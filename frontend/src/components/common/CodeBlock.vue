<script setup lang="ts">
import { ref } from 'vue'
import { useClipboard } from '../../composables/useClipboard'

const props = defineProps<{
  text: string
  language?: string
}>()

const { copy } = useClipboard()
const copied = ref(false)

async function handleCopy() {
  await copy(props.text)
  copied.value = true
  setTimeout(() => {
    copied.value = false
  }, 2000)
}
</script>

<template>
  <div class="code-block">
    <div class="code-header">
      <span class="language" v-if="language">{{ language }}</span>
      <button @click="handleCopy" class="copy-btn" :class="{ copied }">
        <svg v-if="!copied" class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
        <svg v-else class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
        </svg>
        <span>{{ copied ? '已复制' : '复制' }}</span>
      </button>
    </div>
    <pre class="code-content"><code>{{ text }}</code></pre>
  </div>
</template>

<style scoped>
.code-block {
  margin: 0.5rem 0;
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--color-code-bg);
  border: 1px solid var(--color-code-border);
}

.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 1rem;
  background: rgba(255, 255, 255, 0.05);
  border-bottom: 1px solid var(--color-code-border);
}

.language {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  font-weight: 500;
}

.copy-btn {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s;
}

.copy-btn:hover {
  color: var(--color-text-primary);
  border-color: var(--color-text-tertiary);
}

.copy-btn.copied {
  color: var(--color-success);
  border-color: var(--color-success);
}

.icon {
  width: 0.875rem;
  height: 0.875rem;
}

.code-content {
  margin: 0;
  padding: 1rem;
  overflow-x: auto;
  font-size: 0.875rem;
  line-height: 1.5;
  color: var(--color-code-text);
}

.code-content code {
  font-family: 'Fira Code', 'Monaco', 'Consolas', monospace;
}
</style>
