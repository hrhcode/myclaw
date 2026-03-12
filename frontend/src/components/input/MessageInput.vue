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
const isFocused = ref(false)

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
    <div 
      class="input-wrapper"
      :class="{ focused: isFocused }"
    >
      <div class="input-glow" v-if="isFocused" />
      <textarea
        ref="textareaRef"
        v-model="input"
        :placeholder="placeholder || '输入消息...'"
        :disabled="disabled"
        @input="adjustHeight"
        @focus="isFocused = true"
        @blur="isFocused = false"
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
        <div class="btn-glow" />
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
  position: relative;
  display: flex;
  align-items: flex-end;
  gap: 0.5rem;
  padding: 0.75rem;
  background: hsl(var(--card));
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius);
  transition: all 0.3s ease;
  overflow: hidden;
}

.input-wrapper.focused {
  border-color: hsl(var(--primary) / 0.5);
  box-shadow: 0 0 0 3px hsl(var(--primary) / 0.1);
}

.input-glow {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, 
    transparent 0%,
    hsl(var(--primary) / 0.05) 50%,
    transparent 100%
  );
  animation: shimmer 2s linear infinite;
  pointer-events: none;
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
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
  color: hsl(var(--foreground));
  max-height: 12.5rem;
  position: relative;
  z-index: 1;
}

.input-field::placeholder {
  color: hsl(var(--muted-foreground));
}

.input-field:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.submit-btn {
  position: relative;
  padding: 0.625rem;
  background: linear-gradient(135deg, hsl(var(--primary)) 0%, hsl(var(--primary) / 0.8) 100%);
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
  color: hsl(var(--primary-foreground));
  transition: all 0.3s ease;
  overflow: hidden;
}

.btn-glow {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
  transform: translateX(-100%);
  transition: transform 0.5s ease;
}

.submit-btn:hover:not(:disabled) .btn-glow {
  transform: translateX(100%);
}

.submit-btn:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 4px 20px -5px hsl(var(--primary) / 0.5);
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.icon {
  width: 1.25rem;
  height: 1.25rem;
  position: relative;
  z-index: 1;
}

.input-hint {
  margin-top: 0.5rem;
  text-align: right;
  font-size: 0.75rem;
  color: hsl(var(--muted-foreground));
}
</style>
