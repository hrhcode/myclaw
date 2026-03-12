<script setup lang="ts">
/**
 * Button 按钮组件
 * 提供统一的按钮样式，支持多种变体和尺寸
 */
defineProps<{
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost' | 'outline'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  disabled?: boolean
  icon?: boolean
  block?: boolean
}>()

defineEmits<{
  click: [event: MouseEvent]
}>()
</script>

<template>
  <button
    class="btn"
    :class="[variant, size, { 'btn-icon': icon, loading, 'btn-block': block }]"
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
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid transparent;
  white-space: nowrap;
  position: relative;
  overflow: hidden;
}

.btn::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 100%);
  opacity: 0;
  transition: opacity 0.2s;
}

.btn:hover::before {
  opacity: 1;
}

.btn:active {
  transform: scale(0.98);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn:disabled:hover {
  transform: none;
}

.btn:disabled::before {
  opacity: 0;
}

.btn-icon {
  padding: 0.5rem;
  border-radius: var(--radius);
}

.btn-icon.sm {
  padding: 0.5rem;
  width: 32px;
  height: 32px;
}

.btn-icon .icon {
  width: 1rem;
  height: 1rem;
}

.btn-icon.sm .icon {
  width: 1rem;
  height: 1rem;
}

.btn-block {
  width: 100%;
}

.md {
  padding: 0.625rem 1.25rem;
  font-size: 0.875rem;
  height: 40px;
}

.sm {
  padding: 0.5rem 1rem;
  font-size: 0.8125rem;
  height: 32px;
}

.lg {
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  height: 48px;
}

.primary {
  background: linear-gradient(135deg, hsl(var(--primary)) 0%, hsl(var(--primary) / 0.9) 100%);
  color: hsl(var(--primary-foreground));
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05), 0 0 0 1px hsl(var(--primary) / 0.1);
}

.primary:hover:not(:disabled) {
  box-shadow: 0 4px 12px hsl(var(--primary) / 0.3), 0 0 0 1px hsl(var(--primary) / 0.2);
}

.secondary {
  background: hsl(var(--secondary));
  color: hsl(var(--secondary-foreground));
  border-color: hsl(var(--border));
  box-shadow: var(--shadow-sm);
}

.secondary.btn-icon {
  background: hsl(var(--secondary));
  border-color: hsl(var(--border));
}

.secondary.btn-icon:hover:not(:disabled) {
  background: hsl(var(--accent));
  border-color: hsl(var(--border));
}

.secondary:hover:not(:disabled) {
  background: hsl(var(--accent));
  border-color: hsl(var(--border));
  box-shadow: var(--shadow);
}

.outline {
  background: transparent;
  color: hsl(var(--primary));
  border-color: hsl(var(--primary) / 0.5);
}

.outline:hover:not(:disabled) {
  background: hsl(var(--primary) / 0.1);
  border-color: hsl(var(--primary));
}

.danger {
  background: linear-gradient(135deg, hsl(var(--destructive)) 0%, hsl(var(--destructive) / 0.9) 100%);
  color: white;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.danger:hover:not(:disabled) {
  box-shadow: 0 4px 12px hsl(var(--destructive) / 0.3);
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

.loading .spinner {
  margin-right: 0.25rem;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
