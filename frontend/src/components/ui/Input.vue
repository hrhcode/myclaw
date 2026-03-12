<script setup lang="ts">
/**
 * Input 输入框组件
 * 提供统一的输入框样式，支持前后缀插槽
 */
defineProps<{
  modelValue?: string | number
  type?: string
  placeholder?: string
  disabled?: boolean
  error?: string
  size?: 'sm' | 'md' | 'lg'
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string | number]
}>()

function onInput(event: Event) {
  const target = event.target as HTMLInputElement
  emit('update:modelValue', target.value)
}
</script>

<template>
  <div class="input-wrapper">
    <div class="input-container" :class="[size, { disabled, error: !!error }]">
      <span v-if="$slots.prefix" class="input-prefix">
        <slot name="prefix" />
      </span>
      <input
        :value="modelValue"
        :type="type || 'text'"
        :placeholder="placeholder"
        :disabled="disabled"
        class="input"
        @input="onInput"
      />
      <span v-if="$slots.suffix" class="input-suffix">
        <slot name="suffix" />
      </span>
    </div>
    <p v-if="error" class="input-error">{{ error }}</p>
  </div>
</template>

<style scoped>
.input-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.input-container {
  display: flex;
  align-items: center;
  background: hsl(var(--background));
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: var(--shadow-sm);
}

.input-container:hover:not(.disabled) {
  border-color: hsl(var(--border) / 0.8);
}

.input-container:focus-within {
  border-color: hsl(var(--primary));
  box-shadow: 0 0 0 3px hsl(var(--primary) / 0.1), var(--shadow-sm);
}

.input-container.disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: hsl(var(--muted) / 0.3);
}

.input-container.error {
  border-color: hsl(var(--destructive));
}

.input-container.error:focus-within {
  box-shadow: 0 0 0 3px hsl(var(--destructive) / 0.1);
}

.input-container:not(.sm):not(.md):not(.lg) .input,
.md .input {
  padding: 0.625rem 0.875rem;
  font-size: 0.875rem;
  height: 40px;
}

.sm .input {
  padding: 0.5rem 0.75rem;
  font-size: 0.8125rem;
  height: 32px;
}

.lg .input {
  padding: 0.75rem 1rem;
  font-size: 1rem;
  height: 48px;
}

.input {
  flex: 1;
  background: transparent;
  border: none;
  color: hsl(var(--foreground));
  width: 100%;
  min-width: 0;
}

.input:focus {
  outline: none;
}

.input::placeholder {
  color: hsl(var(--muted-foreground));
}

.input:disabled {
  cursor: not-allowed;
}

.input-prefix,
.input-suffix {
  display: flex;
  align-items: center;
  color: hsl(var(--muted-foreground));
}

.input-prefix {
  padding-left: 0.875rem;
}

.input-suffix {
  padding-right: 0.875rem;
}

.input-error {
  font-size: 0.75rem;
  color: hsl(var(--destructive));
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}
</style>
