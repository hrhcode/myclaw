<script setup lang="ts">
/**
 * Toggle 开关组件
 * 提供统一的开关样式
 */
defineProps<{
  modelValue: boolean
  disabled?: boolean
  label?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

function toggle() {
  if (!disabled) {
    emit('update:modelValue', !modelValue)
  }
}
</script>

<template>
  <div class="toggle-wrapper" :class="{ disabled }">
    <button
      type="button"
      role="switch"
      :aria-checked="modelValue"
      :disabled="disabled"
      class="toggle"
      :class="{ active: modelValue }"
      @click="toggle"
    >
      <span class="toggle-thumb" />
    </button>
    <span v-if="label" class="toggle-label">{{ label }}</span>
  </div>
</template>

<style scoped>
.toggle-wrapper {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.toggle-wrapper.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.toggle {
  position: relative;
  width: 44px;
  height: 24px;
  padding: 0;
  background: hsl(var(--muted));
  border: none;
  border-radius: 24px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.toggle:focus {
  outline: none;
  box-shadow: 0 0 0 2px hsl(var(--primary) / 0.3);
}

.toggle.active {
  background: hsl(var(--primary));
}

.toggle-thumb {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 18px;
  height: 18px;
  background: white;
  border-radius: 50%;
  transition: transform 0.3s;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.toggle.active .toggle-thumb {
  transform: translateX(20px);
}

.toggle-label {
  font-size: 0.875rem;
  color: hsl(var(--foreground));
}
</style>
