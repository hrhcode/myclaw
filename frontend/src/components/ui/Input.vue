<script setup lang="ts">
/**
 * Input 输入框组件
 * 提供统一的输入框样式
 */
defineProps<{
  modelValue?: string | number
  type?: string
  placeholder?: string
  disabled?: boolean
  error?: string
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
    <div class="input-container" :class="{ disabled, error: !!error }">
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
  gap: 0.25rem;
}

.input-container {
  display: flex;
  align-items: center;
  background: hsl(var(--background));
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius);
  transition: border-color 0.2s, box-shadow 0.2s;
}

.input-container:focus-within {
  border-color: hsl(var(--primary));
  box-shadow: 0 0 0 2px hsl(var(--primary) / 0.2);
}

.input-container.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.input-container.error {
  border-color: hsl(var(--destructive));
}

.input-container.error:focus-within {
  box-shadow: 0 0 0 2px hsl(var(--destructive) / 0.2);
}

.input {
  flex: 1;
  padding: 0.5rem 0.75rem;
  background: transparent;
  border: none;
  font-size: 0.875rem;
  color: hsl(var(--foreground));
  width: 100%;
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
  padding: 0 0.5rem;
  color: hsl(var(--muted-foreground));
}

.input-prefix {
  padding-left: 0.75rem;
}

.input-suffix {
  padding-right: 0.75rem;
}

.input-error {
  font-size: 0.75rem;
  color: hsl(var(--destructive));
  margin: 0;
}
</style>
