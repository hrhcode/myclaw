<script setup lang="ts">
/**
 * Toggle 开关组件
 * 提供统一的开关样式
 */
defineProps<{
  modelValue: boolean
  disabled?: boolean
  label?: string
  size?: 'sm' | 'md' | 'lg'
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
      :class="[size, { active: modelValue }]"
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
  gap: 0.625rem;
}

.toggle-wrapper.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.toggle {
  position: relative;
  padding: 0;
  background: hsl(var(--muted));
  border: 2px solid transparent;
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.1);
}

.toggle:focus {
  outline: none;
  box-shadow: 0 0 0 3px hsl(var(--primary) / 0.2), inset 0 1px 3px rgba(0, 0, 0, 0.1);
}

.toggle.active {
  background: linear-gradient(135deg, hsl(var(--primary)) 0%, hsl(var(--primary) / 0.9) 100%);
  box-shadow: 0 2px 8px hsl(var(--primary) / 0.3);
}

.md {
  width: 44px;
  height: 24px;
}

.sm {
  width: 36px;
  height: 20px;
}

.lg {
  width: 52px;
  height: 28px;
}

.toggle-thumb {
  position: absolute;
  top: 50%;
  left: 2px;
  transform: translateY(-50%);
  background: white;
  border-radius: 50%;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15), 0 1px 2px rgba(0, 0, 0, 0.1);
}

.md .toggle-thumb {
  width: 18px;
  height: 18px;
}

.sm .toggle-thumb {
  width: 14px;
  height: 14px;
}

.lg .toggle-thumb {
  width: 22px;
  height: 22px;
}

.toggle.active .toggle-thumb {
  transform: translateY(-50%) translateX(20px);
}

.sm.active .toggle-thumb {
  transform: translateY(-50%) translateX(16px);
}

.lg.active .toggle-thumb {
  transform: translateY(-50%) translateX(24px);
}

.toggle-label {
  font-size: 0.875rem;
  color: hsl(var(--foreground));
  user-select: none;
}
</style>
