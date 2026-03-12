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
  <div class="select-wrapper" :class="{ disabled }">
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

.select-wrapper.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.select {
  appearance: none;
  padding: 0.5rem 2.5rem 0.5rem 0.75rem;
  background: hsl(var(--background));
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius);
  font-size: 0.875rem;
  color: hsl(var(--foreground));
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s;
  min-width: 120px;
}

.select:focus {
  outline: none;
  border-color: hsl(var(--primary));
  box-shadow: 0 0 0 2px hsl(var(--primary) / 0.2);
}

.select:disabled {
  cursor: not-allowed;
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
}
</style>
