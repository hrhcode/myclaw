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
      <div class="icon-container">
        <Transition name="icon-switch">
          <svg 
            :key="theme"
            class="icon" 
            :class="theme"
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path v-if="theme === 'light'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
            <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
        </Transition>
      </div>
      <div class="btn-glow" />
    </button>
  </div>
</template>

<style scoped>
.theme-toggle {
  display: flex;
  align-items: center;
}

.theme-btn {
  position: relative;
  padding: 0.625rem;
  border-radius: var(--radius);
  background: hsl(var(--card));
  border: 1px solid hsl(var(--border));
  cursor: pointer;
  color: hsl(var(--muted-foreground));
  transition: all 0.2s ease;
  overflow: hidden;
}

.theme-btn:hover {
  background: hsl(var(--accent));
  color: hsl(var(--accent-foreground));
  border-color: hsl(var(--primary) / 0.3);
  transform: translateY(-2px);
  box-shadow: 0 4px 20px -5px hsl(var(--primary) / 0.3);
}

.btn-glow {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
  transform: translateX(-100%);
  transition: transform 0.4s ease;
}

.theme-btn:hover .btn-glow {
  transform: translateX(100%);
}

.icon-container {
  position: relative;
  width: 1.25rem;
  height: 1.25rem;
}

.icon {
  position: absolute;
  top: 0;
  left: 0;
  width: 1.25rem;
  height: 1.25rem;
  display: block;
}

.icon.light {
  color: hsl(var(--muted-foreground));
}

.icon.dark {
  color: hsl(var(--primary));
}

.icon-switch-enter-active {
  animation: icon-in 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.icon-switch-leave-active {
  animation: icon-out 0.15s ease-in;
  position: absolute;
}

@keyframes icon-in {
  0% {
    opacity: 0;
    transform: rotate(-90deg) scale(0.3);
  }
  100% {
    opacity: 1;
    transform: rotate(0deg) scale(1);
  }
}

@keyframes icon-out {
  0% {
    opacity: 1;
    transform: rotate(0deg) scale(1);
  }
  100% {
    opacity: 0;
    transform: rotate(90deg) scale(0.3);
  }
}
</style>
