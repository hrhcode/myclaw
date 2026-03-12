<script setup lang="ts">
/**
 * Select 下拉选择组件
 * 提供统一的下拉选择样式
 */
defineProps<{
  modelValue?: string
  options: { value: string; label: string }[]
  placeholder?: string
  disabled?: boolean
  size?: 'sm' | 'md' | 'lg'
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

function onChange(event: Event) {
  const target = event.target as HTMLSelectElement
  emit('update:modelValue', target.value)
}
</script>

<template>
  <div class="select-wrapper" :class="[size, { disabled }]">
    <select
      :value="modelValue"
      :disabled="disabled"
      class="select"
      @change="onChange"
    >
      <option v-if="placeholder" value="" disabled>{{ placeholder }}</option>
      <option
        v-for="option in options"
        :key="option.value"
        :value="option.value"
      >
        {{ option.label }}
      </option>
    </select>
    <svg class="select-arrow" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
    </svg>
  </div>
</template>

<style scoped>
.select-wrapper {
  position: relative;
  display: inline-flex;
}

.select-wrapper:not(.sm):not(.md):not(.lg) .select {
  padding: 0.625rem 2.5rem 0.625rem 0.875rem;
  font-size: 0.875rem;
  height: 40px;
}

.select-wrapper.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.select {
  appearance: none;
  background: hsl(var(--background));
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius);
  color: hsl(var(--foreground));
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: var(--shadow-sm);
  min-width: 120px;
  padding-right: 2.5rem;
}

.md .select {
  padding: 0.625rem 2.5rem 0.625rem 0.875rem;
  font-size: 0.875rem;
  height: 40px;
}

.sm .select {
  padding: 0.5rem 2.25rem 0.5rem 0.75rem;
  font-size: 0.8125rem;
  height: 32px;
}

.lg .select {
  padding: 0.75rem 2.75rem 0.75rem 1rem;
  font-size: 1rem;
  height: 48px;
}

.select:hover:not(:disabled) {
  border-color: hsl(var(--border) / 0.8);
}

.select:focus {
  outline: none;
  border-color: hsl(var(--primary));
  box-shadow: 0 0 0 3px hsl(var(--primary) / 0.1), var(--shadow-sm);
}

.select:disabled {
  cursor: not-allowed;
  background: hsl(var(--muted) / 0.3);
}

.select-arrow {
  position: absolute;
  right: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  width: 1rem;
  height: 1rem;
  color: hsl(var(--muted-foreground));
  pointer-events: none;
  transition: transform 0.2s;
}

.select-wrapper:focus-within .select-arrow {
  color: hsl(var(--primary));
}
</style>
