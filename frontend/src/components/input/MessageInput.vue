<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  disabled?: boolean
  placeholder?: string
}>()

const emit = defineEmits<{
  (e: 'submit', value: string): void
}>()

const input = ref('')
const textareaRef = ref<HTMLTextAreaElement | null>(null)

function handleSubmit() {
  const value = input.value.trim()
  if (!value || props.disabled) return
  
  emit('submit', value)
  input.value = ''
}

function adjustHeight() {
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
    textareaRef.value.style.height = Math.min(textareaRef.value.scrollHeight, 200) + 'px'
  }
}

function focus() {
  textareaRef.value?.focus()
}

defineExpose({ focus })
</script>

<template>
  <form @submit.prevent="handleSubmit" class="message-input">
    <div class="input-wrapper">
      <textarea
        ref="textareaRef"
        v-model="input"
        :placeholder="placeholder || '输入消息...'"
        :disabled="disabled"
        @input="adjustHeight"
        @keydown.enter.exact.prevent="handleSubmit"
        @keydown.enter.shift.exact="() => {}"
        rows="1"
        class="input-field"
      />
      <button
        type="submit"
        :disabled="disabled || !input.trim()"
        class="submit-btn"
      >
        <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
        </svg>
      </button>
    </div>
    <div class="input-hint">
      <span>Enter 发送 · Shift+Enter 换行</span>
    </div>
  </form>
</template>

<style scoped>
.message-input {
  width: 100%;
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 0.5rem;
  padding: 0.75rem;
  background: var(--color-input-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  transition: border-color 0.2s;
}

.input-wrapper:focus-within {
  border-color: var(--color-accent);
}

.input-field {
  flex: 1;
  padding: 0.5rem;
  background: transparent;
  border: none;
  outline: none;
  resize: none;
  font-size: 0.875rem;
  line-height: 1.5;
  color: var(--color-text-primary);
  max-height: 12.5rem;
}

.input-field::placeholder {
  color: var(--color-text-tertiary);
}

.input-field:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.submit-btn {
  padding: 0.5rem;
  background: var(--color-accent);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  color: white;
  transition: all 0.2s;
}

.submit-btn:hover:not(:disabled) {
  background: var(--color-accent-hover);
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.icon {
  width: 1.25rem;
  height: 1.25rem;
}

.input-hint {
  margin-top: 0.5rem;
  text-align: right;
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}
</style>
