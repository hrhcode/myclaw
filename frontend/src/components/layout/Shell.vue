<script setup lang="ts">
/**
 * Shell 布局组件
 * 整体应用布局框架，包含 Topbar、Sidebar 和内容区域
 * 添加科技感背景效果
 */
import { ref, computed, provide } from 'vue'
import { useRoute } from 'vue-router'
import Topbar from './Topbar.vue'
import Sidebar from './Sidebar.vue'
import { useGateway } from '@/composables/useGateway'

const route = useRoute()
const sidebarCollapsed = ref(false)

const { status: gatewayStatus, loading: gatewayLoading } = useGateway()
provide('gatewayStatus', gatewayStatus)
provide('gatewayLoading', gatewayLoading)

const currentRoute = computed(() => route.name as string)

const isChatPage = computed(() => route.name === 'chat')

function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
}
</script>

<template>
  <div class="shell" :class="{ 'shell--collapsed': sidebarCollapsed }">
    <div class="shell-bg">
      <div class="bg-gradient" />
      <div class="bg-grid" />
      <div class="bg-glow bg-glow-1" />
      <div class="bg-glow bg-glow-2" />
    </div>
    
    <Topbar
      :gateway-status="gatewayStatus"
      :gateway-loading="gatewayLoading"
      @toggle-sidebar="toggleSidebar"
    />
    <Sidebar
      :collapsed="sidebarCollapsed"
      :active-tab="currentRoute"
    />
    <main class="content" :class="{ 'content--chat': isChatPage }">
      <slot />
    </main>
  </div>
</template>

<style scoped>
.shell {
  display: grid;
  grid-template-columns: 220px 1fr;
  grid-template-rows: 56px 1fr;
  grid-template-areas:
    "topbar topbar"
    "sidebar content";
  height: 100vh;
  background: hsl(var(--background));
  position: relative;
  overflow: hidden;
}

.shell--collapsed {
  grid-template-columns: 0 1fr;
}

.shell-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
  z-index: 0;
}

.bg-gradient {
  position: absolute;
  inset: 0;
  background: radial-gradient(
    ellipse 80% 50% at 50% -20%,
    hsl(var(--primary) / 0.08) 0%,
    transparent 50%
  );
}

.dark .bg-gradient {
  background: radial-gradient(
    ellipse 80% 50% at 50% -20%,
    hsl(var(--primary) / 0.15) 0%,
    transparent 50%
  );
}

.bg-grid {
  position: absolute;
  inset: 0;
  background-image: 
    linear-gradient(hsl(var(--border) / 0.3) 1px, transparent 1px),
    linear-gradient(90deg, hsl(var(--border) / 0.3) 1px, transparent 1px);
  background-size: 60px 60px;
  mask-image: radial-gradient(ellipse 60% 60% at 50% 0%, black 0%, transparent 70%);
  -webkit-mask-image: radial-gradient(ellipse 60% 60% at 50% 0%, black 0%, transparent 70%);
}

.bg-glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.4;
  animation: float-glow 20s ease-in-out infinite;
}

.bg-glow-1 {
  width: 400px;
  height: 400px;
  background: hsl(var(--primary) / 0.15);
  top: -100px;
  right: 10%;
  animation-delay: 0s;
}

.bg-glow-2 {
  width: 300px;
  height: 300px;
  background: hsl(var(--chart-3) / 0.1);
  bottom: 10%;
  left: 5%;
  animation-delay: -10s;
}

@keyframes float-glow {
  0%, 100% {
    transform: translate(0, 0) scale(1);
  }
  25% {
    transform: translate(30px, -20px) scale(1.05);
  }
  50% {
    transform: translate(-20px, 30px) scale(0.95);
  }
  75% {
    transform: translate(-30px, -10px) scale(1.02);
  }
}

.content {
  grid-area: content;
  overflow-y: auto;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
  padding: 1.5rem 2rem;
  position: relative;
  z-index: 1;
}

.content--chat {
  padding: 0;
  overflow: hidden;
}

@media (max-width: 768px) {
  .shell {
    grid-template-columns: 1fr;
    grid-template-rows: 56px 1fr;
    grid-template-areas:
      "topbar"
      "content";
  }

  .shell--collapsed {
    grid-template-columns: 1fr;
  }

  .content {
    padding: 1rem;
  }
  
  .bg-glow {
    display: none;
  }
}
</style>
