<script setup lang="ts">
/**
 * Shell 布局组件
 * 整体应用布局框架，包含 Topbar、Sidebar 和内容区域
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

function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
}
</script>

<template>
  <div class="shell" :class="{ 'shell--collapsed': sidebarCollapsed }">
    <Topbar
      :gateway-status="gatewayStatus"
      :gateway-loading="gatewayLoading"
      @toggle-sidebar="toggleSidebar"
    />
    <Sidebar
      :collapsed="sidebarCollapsed"
      :active-tab="currentRoute"
    />
    <main class="content">
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
}

.shell--collapsed {
  grid-template-columns: 0 1fr;
}

.content {
  grid-area: content;
  overflow: hidden;
  display: flex;
  flex-direction: column;
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
}
</style>
