<script setup lang="ts">
/**
 * Sidebar 导航组件
 * 侧边导航栏，支持分组和折叠
 */
import { computed } from 'vue'
import { useRouter } from 'vue-router'

defineProps<{
  collapsed: boolean
  activeTab: string
}>()

const router = useRouter()

const navGroups = [
  {
    label: '',
    items: [
      { id: 'chat', label: '聊天', icon: 'chat' },
    ],
  },
  {
    label: '控制面板',
    items: [
      { id: 'overview', label: '概览', icon: 'dashboard' },
      { id: 'channels', label: '通道', icon: 'channel' },
      { id: 'sessions', label: '会话', icon: 'session' },
    ],
  },
  {
    label: '管理',
    items: [
      { id: 'tools', label: '工具', icon: 'tool' },
      { id: 'memories', label: '记忆', icon: 'memory' },
    ],
  },
  {
    label: '系统',
    items: [
      { id: 'settings', label: '设置', icon: 'settings' },
    ],
  },
]

function navigate(id: string) {
  router.push({ name: id })
}

function getIconClass(icon: string): string {
  const iconMap: Record<string, string> = {
    chat: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z',
    dashboard: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6',
    channel: 'M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01',
    session: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z',
    tool: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z',
    memory: 'M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z',
    settings: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z',
  }
  return iconMap[icon] || ''
}
</script>

<template>
  <nav class="sidebar" :class="{ collapsed }">
    <div v-for="group in navGroups" :key="group.label" class="nav-group">
      <div v-if="group.label && !collapsed" class="nav-group-label">
        {{ group.label }}
      </div>
      <div
        v-for="item in group.items"
        :key="item.id"
        class="nav-item"
        :class="{ active: activeTab === item.id }"
        @click="navigate(item.id)"
      >
        <svg class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="getIconClass(item.icon)" />
        </svg>
        <span v-if="!collapsed" class="nav-label">{{ item.label }}</span>
      </div>
    </div>
  </nav>
</template>

<style scoped>
.sidebar {
  grid-area: sidebar;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1rem;
  background: hsl(var(--card) / 0.5);
  border-right: 1px solid hsl(var(--border));
  overflow-y: auto;
  transition: all 0.3s ease;
}

.sidebar.collapsed {
  width: 0;
  padding: 0;
  overflow: hidden;
  opacity: 0;
}

.nav-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.nav-group-label {
  padding: 0.5rem 0.75rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: hsl(var(--muted-foreground));
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 0.75rem;
  border-radius: var(--radius);
  cursor: pointer;
  color: hsl(var(--foreground));
  transition: all 0.2s;
}

.nav-item:hover {
  background: hsl(var(--accent));
  color: hsl(var(--accent-foreground));
}

.nav-item.active {
  background: hsl(var(--primary));
  color: hsl(var(--primary-foreground));
}

.nav-icon {
  width: 1.25rem;
  height: 1.25rem;
  flex-shrink: 0;
}

.nav-label {
  font-size: 0.875rem;
  font-weight: 500;
  white-space: nowrap;
}

@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 56px;
    bottom: 0;
    width: 220px;
    z-index: 50;
    transform: translateX(0);
  }

  .sidebar.collapsed {
    transform: translateX(-100%);
  }
}
</style>
