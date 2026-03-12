<script setup lang="ts">
import { useTheme } from '../../composables/useTheme'

const { theme, toggleTheme } = useTheme()
</script>

<template>
  <div class="theme-toggle">
    <button
      @click="toggleTheme"
      class="theme-btn"
      :title="theme === 'light' ? '切换到深色模式' : '切换到浅色模式'"
    >
      <svg v-if="theme === 'light'" class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
      </svg>
      <svg v-else class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
      </svg>
    </button>
  </div>
</template>

<style scoped>
.theme-toggle {
  display: flex;
  align-items: center;
}

.theme-btn {
  padding: 0.5rem;
  border-radius: var(--radius-md);
  background: transparent;
  border: none;
  cursor: pointer;
  color: var(--color-text-secondary);
  transition: all 0.2s;
}

.theme-btn:hover {
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
}

.icon {
  width: 1.25rem;
  height: 1.25rem;
}
</style>
