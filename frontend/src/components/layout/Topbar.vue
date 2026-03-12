<script setup lang="ts">
/**
 * Topbar 组件
 * 顶部栏，包含健康状况指示器和主题切换
 */
import ThemeToggle from '@/components/common/ThemeToggle.vue'
import type { GatewayStatus } from '@/api/gateway'

const props = defineProps<{
  gatewayStatus: GatewayStatus | null
  gatewayLoading: boolean
}>()

const emit = defineEmits<{
  'toggle-sidebar': []
}>()
</script>

<template>
  <header class="topbar">
    <div class="topbar-left">
      <button @click="emit('toggle-sidebar')" class="menu-btn">
        <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>
      <span class="logo gradient-text">MyClaw</span>
    </div>

    <div class="topbar-right">
      <div class="gateway-status" :class="{ loading: gatewayLoading }">
        <span class="status-dot" :class="{ ok: gatewayStatus?.running }"></span>
        <span class="status-label">健康状况</span>
        <span class="status-value">
          {{ gatewayStatus?.running ? '正常' : '离线' }}
        </span>
      </div>
      <ThemeToggle />
    </div>
  </header>
</template>

<style scoped>
.topbar {
  grid-area: topbar;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1.5rem;
  background: hsl(var(--card) / 0.8);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid hsl(var(--border));
  z-index: 100;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.menu-btn {
  padding: 0.5rem;
  background: transparent;
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
  color: hsl(var(--muted-foreground));
  transition: all 0.2s;
}

.menu-btn:hover {
  background: hsl(var(--accent));
  color: hsl(var(--accent-foreground));
}

.icon {
  width: 1.25rem;
  height: 1.25rem;
}

.logo {
  font-size: 1.25rem;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.gateway-status {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.25rem 0.5rem;
  background: hsl(var(--muted) / 0.5);
  border-radius: var(--radius-full);
  font-size: 0.75rem;
}

.gateway-status.loading {
  opacity: 0.6;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: hsl(var(--destructive));
  box-shadow: 0 0 8px hsl(var(--destructive) / 0.5);
  animation: pulse-subtle 2s ease-in-out infinite;
}

.status-dot.ok {
  background: hsl(var(--chart-2));
  box-shadow: 0 0 8px hsl(var(--chart-2) / 0.5);
  animation: none;
}

.status-label {
  color: hsl(var(--muted-foreground));
  font-weight: 600;
}

.status-value {
  font-weight: 500;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

@keyframes pulse-subtle {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@media (max-width: 768px) {
  .topbar {
    padding: 0 1rem;
  }

  .gateway-status {
    display: none;
  }
}
</style>
