<script setup lang="ts">
/**
 * Textarea 文本域组件
 * 提供统一的文本域样式
 */
defineProps<{
  modelValue?: string
  placeholder?: string
  disabled?: boolean
  rows?: number
  error?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

function onInput(event: Event) {
  const target = event.target as HTMLTextAreaElement
  emit('update:modelValue', target.value)
}
</script>

<template>
  <div class="textarea-wrapper">
    <textarea
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :rows="rows || 4"
      class="textarea"
      :class="{ error: !!error }"
      @input="onInput"
    />
    <p v-if="error" class="textarea-error">{{ error }}</p>
  </div>
</template>

<style scoped>
.textarea-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.textarea {
  padding: 0.5rem 0.75rem;
  background: hsl(var(--background));
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius);
  font-size: 0.875rem;
  color: hsl(var(--foreground));
  resize: vertical;
  min-height: 80px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.textarea:focus {
  outline: none;
  border-color: hsl(var(--primary));
  box-shadow: 0 0 0 2px hsl(var(--primary) / 0.2);
}

.textarea.error {
  border-color: hsl(var(--destructive));
}

.textarea.error:focus {
  box-shadow: 0 0 0 2px hsl(var(--destructive) / 0.2);
}

.textarea::placeholder {
  color: hsl(var(--muted-foreground));
}

.textarea:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.textarea-error {
  font-size: 0.75rem;
  color: hsl(var(--destructive));
  margin: 0;
}
</style>
