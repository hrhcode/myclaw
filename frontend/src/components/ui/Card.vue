<script setup lang="ts">
/**
 * Card 卡片组件
 * 提供统一的卡片容器样式，支持标题、副标题和操作区
 */
defineProps<{
  title?: string
  subtitle?: string
  noPadding?: boolean
  hoverable?: boolean
}>()
</script>

<template>
  <div class="card" :class="{ hoverable }">
    <div v-if="title || $slots.header" class="card-header">
      <div class="card-header-content">
        <h3 v-if="title" class="card-title">{{ title }}</h3>
        <p v-if="subtitle" class="card-subtitle">{{ subtitle }}</p>
        <slot name="header" />
      </div>
      <div v-if="$slots.actions" class="card-actions">
        <slot name="actions" />
      </div>
    </div>
    <div class="card-body" :class="{ 'no-padding': noPadding }">
      <slot />
    </div>
    <div v-if="$slots.footer" class="card-footer">
      <slot name="footer" />
    </div>
  </div>
</template>

<style scoped>
.card {
  background: hsl(var(--card));
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.card.hoverable {
  cursor: pointer;
}

.card.hoverable:hover {
  transform: translateY(-2px);
  border-color: hsl(var(--primary) / 0.2);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid hsl(var(--border));
  background: linear-gradient(180deg, hsl(var(--muted) / 0.2) 0%, transparent 100%);
}

.card-header-content {
  flex: 1;
}

.card-title {
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
  color: hsl(var(--foreground));
  letter-spacing: -0.01em;
}

.card-subtitle {
  font-size: 0.8125rem;
  color: hsl(var(--muted-foreground));
  margin: 0.25rem 0 0 0;
}

.card-actions {
  display: flex;
  gap: 0.5rem;
  margin-left: 1rem;
}

.card-body {
  padding: 1.5rem;
}

.card-body.no-padding {
  padding: 0;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid hsl(var(--border));
  background: hsl(var(--muted) / 0.2);
}
</style>
