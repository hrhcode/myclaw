<script setup lang="ts">
/**
 * Topbar 组件
 * 顶部栏，包含 Gateway 状态指示器和主题切换
 * 添加科技感效果
 */
import { computed } from 'vue'
import ThemeToggle from '@/components/common/ThemeToggle.vue'
import type { GatewayStatus } from '@/api/gateway'

const props = defineProps<{
  gatewayStatus: GatewayStatus | null
  gatewayLoading: boolean
}>()

const emit = defineEmits<{
  'toggle-sidebar': []
}>()

const uptimeFormatted = computed(() => {
  const seconds = props.gatewayStatus?.uptime_seconds || 0
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  if (hours > 0) {
    return `${hours}h ${minutes}m`
  }
  return `${minutes}m`
})
</script>

<template>
  <header class="topbar">
    <div class="topbar-border" />
    <div class="topbar-left">
      <button @click="emit('toggle-sidebar')" class="menu-btn">
        <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>
      <div class="logo-wrapper">
        <span class="logo">
          <span class="logo-text">My</span>
          <span class="logo-highlight">Claw</span>
        </span>
        <div class="logo-glow" />
      </div>
    </div>

    <div class="topbar-center">
      <div class="gateway-status" :class="{ loading: gatewayLoading, running: gatewayStatus?.running }">
        <div class="status-pulse" />
        <span class="status-dot" :class="{ ok: gatewayStatus?.running }"></span>
        <span class="status-label">Gateway</span>
        <span class="status-value mono">
          {{ gatewayStatus?.running ? '运行中' : '已停止' }}
        </span>
        <span v-if="gatewayStatus?.running" class="uptime mono">
          {{ uptimeFormatted }}
        </span>
      </div>
    </div>

    <div class="topbar-right">
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
  background: hsl(var(--card) / 0.7);
  backdrop-filter: blur(16px);
  border-bottom: 1px solid hsl(var(--border));
  z-index: 100;
  position: relative;
}

.topbar-border {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent 0%,
    hsl(var(--primary) / 0.5) 20%,
    hsl(var(--primary) / 0.3) 50%,
    hsl(var(--primary) / 0.5) 80%,
    transparent 100%
  );
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.topbar-center {
  display: flex;
  align-items: center;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.menu-btn {
  padding: 0.5rem;
  background: transparent;
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
  color: hsl(var(--muted-foreground));
  transition: all 0.2s ease;
}

.menu-btn:hover {
  background: hsl(var(--accent));
  color: hsl(var(--accent-foreground));
}

.icon {
  width: 1.25rem;
  height: 1.25rem;
}

.logo-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.logo {
  font-size: 1.25rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  display: flex;
  align-items: center;
}

.logo-text {
  color: hsl(var(--foreground));
}

.logo-highlight {
  background: linear-gradient(135deg, hsl(var(--primary)) 0%, hsl(var(--chart-3)) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.logo-glow {
  position: absolute;
  inset: -4px -8px;
  background: radial-gradient(ellipse at center, hsl(var(--primary) / 0.15) 0%, transparent 70%);
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.logo-wrapper:hover .logo-glow {
  opacity: 1;
}

.gateway-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.375rem 0.875rem;
  background: hsl(var(--muted) / 0.5);
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius-full);
  font-size: 0.875rem;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
}

.gateway-status.running {
  border-color: hsl(var(--chart-2) / 0.3);
  background: linear-gradient(135deg, hsl(var(--chart-2) / 0.08) 0%, hsl(var(--muted) / 0.3) 100%);
}

.gateway-status.loading {
  opacity: 0.6;
}

.status-pulse {
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 20% 50%, hsl(var(--chart-2) / 0.1) 0%, transparent 50%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.gateway-status.running .status-pulse {
  animation: status-pulse 2s ease-in-out infinite;
}

@keyframes status-pulse {
  0%, 100% { opacity: 0; }
  50% { opacity: 1; }
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: hsl(var(--destructive));
  box-shadow: 0 0 8px hsl(var(--destructive) / 0.5);
  position: relative;
  z-index: 1;
}

.status-dot.ok {
  background: hsl(var(--chart-2));
  box-shadow: 0 0 8px hsl(var(--chart-2) / 0.5);
  animation: dot-pulse 2s ease-in-out infinite;
}

@keyframes dot-pulse {
  0%, 100% { 
    box-shadow: 0 0 8px hsl(var(--chart-2) / 0.5);
    transform: scale(1);
  }
  50% { 
    box-shadow: 0 0 12px hsl(var(--chart-2) / 0.8);
    transform: scale(1.1);
  }
}

.status-label {
  color: hsl(var(--muted-foreground));
  position: relative;
  z-index: 1;
}

.status-value {
  font-weight: 500;
  position: relative;
  z-index: 1;
}

.uptime {
  color: hsl(var(--muted-foreground));
  font-size: 0.75rem;
  position: relative;
  z-index: 1;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

@media (max-width: 768px) {
  .topbar {
    padding: 0 1rem;
  }

  .topbar-center {
    display: none;
  }
}
</style>
