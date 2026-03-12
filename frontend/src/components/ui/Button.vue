<script setup lang="ts">
/**
 * Button 按钮组件
 * 提供统一的按钮样式
 */
defineProps<{
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  disabled?: boolean
  icon?: boolean
}>()

defineEmits<{
  click: [event: MouseEvent]
}>()
</script>

<template>
  <button
    class="btn"
    :class="[variant, size, { 'btn-icon': icon, loading }]"
    :disabled="disabled || loading"
    @click="$emit('click', $event)"
  >
    <svg v-if="loading" class="spinner" fill="none" viewBox="0 0 24 24">
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
    </svg>
    <slot />
  </button>
</template>

<style scoped>
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  border-radius: var(--radius);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
  white-space: nowrap;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn:disabled:hover {
  transform: none;
}

.btn-icon {
  padding: 0.5rem;
}

.md {
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
}

.sm {
  padding: 0.375rem 0.75rem;
  font-size: 0.75rem;
}

.lg {
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
}

.primary {
  background: hsl(var(--primary));
  color: hsl(var(--primary-foreground));
}

.primary:hover:not(:disabled) {
  background: hsl(var(--primary) / 0.9);
}

.secondary {
  background: hsl(var(--secondary));
  color: hsl(var(--secondary-foreground));
  border-color: hsl(var(--border));
}

.secondary:hover:not(:disabled) {
  background: hsl(var(--accent));
}

.danger {
  background: hsl(var(--destructive));
  color: white;
}

.danger:hover:not(:disabled) {
  background: hsl(var(--destructive) / 0.9);
}

.ghost {
  background: transparent;
  color: hsl(var(--foreground));
}

.ghost:hover:not(:disabled) {
  background: hsl(var(--muted));
}

.spinner {
  width: 1em;
  height: 1em;
  animation: spin 1s linear infinite;
}

.loading {
  pointer-events: none;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
