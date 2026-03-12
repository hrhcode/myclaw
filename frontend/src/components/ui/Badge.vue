<script setup lang="ts">
/**
 * Badge 标签组件
 * 提供统一的标签样式
 */
defineProps<{
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'danger'
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
  padding: 0.125rem 0.5rem;
  border-radius: var(--radius-full);
  font-size: 0.75rem;
  font-weight: 500;
  white-space: nowrap;
}

.md {
  padding: 0.25rem 0.75rem;
  font-size: 0.8125rem;
}

.default {
  background: hsl(var(--muted));
  color: hsl(var(--muted-foreground));
}

.primary {
  background: hsl(var(--primary) / 0.1);
  color: hsl(var(--primary));
}

.success {
  background: hsl(var(--chart-2) / 0.1);
  color: hsl(var(--chart-2));
}

.warning {
  background: hsl(45 93% 47% / 0.1);
  color: hsl(45 93% 47%);
}

.danger {
  background: hsl(var(--destructive) / 0.1);
  color: hsl(var(--destructive));
}
</style>
