<script setup lang="ts">
/**
 * Badge 标签组件
 * 提供统一的标签样式，支持多种变体
 */
defineProps<{
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'danger' | 'outline'
  size?: 'sm' | 'md'
}>()
</script>

<template>
  <span class="badge" :class="[variant, size]">
    <slot />
  </span>
</template>

<style scoped>
.badge {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.625rem;
  border-radius: var(--radius-full);
  font-size: 0.75rem;
  font-weight: 500;
  white-space: nowrap;
  letter-spacing: 0.01em;
  transition: all 0.2s;
}

.sm {
  padding: 0.125rem 0.5rem;
  font-size: 0.6875rem;
}

.md {
  padding: 0.375rem 0.75rem;
  font-size: 0.8125rem;
}

.default {
  background: hsl(var(--muted));
  color: hsl(var(--muted-foreground));
}

.primary {
  background: linear-gradient(135deg, hsl(var(--primary) / 0.15) 0%, hsl(var(--primary) / 0.1) 100%);
  color: hsl(var(--primary));
  border: 1px solid hsl(var(--primary) / 0.2);
}

.success {
  background: linear-gradient(135deg, hsl(var(--chart-2) / 0.15) 0%, hsl(var(--chart-2) / 0.1) 100%);
  color: hsl(var(--chart-2));
  border: 1px solid hsl(var(--chart-2) / 0.2);
}

.warning {
  background: linear-gradient(135deg, hsl(var(--chart-4) / 0.15) 0%, hsl(var(--chart-4) / 0.1) 100%);
  color: hsl(var(--chart-4));
  border: 1px solid hsl(var(--chart-4) / 0.2);
}

.danger {
  background: linear-gradient(135deg, hsl(var(--destructive) / 0.15) 0%, hsl(var(--destructive) / 0.1) 100%);
  color: hsl(var(--destructive));
  border: 1px solid hsl(var(--destructive) / 0.2);
}

.outline {
  background: transparent;
  color: hsl(var(--foreground));
  border: 1px solid hsl(var(--border));
}
</style>
