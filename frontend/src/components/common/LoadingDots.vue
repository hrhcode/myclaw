<script setup lang="ts">
defineProps<{
  size?: 'sm' | 'md' | 'lg'
}>()
</script>

<template>
  <div class="loading-dots" :class="size || 'md'">
    <span class="dot" style="animation-delay: 0s"></span>
    <span class="dot" style="animation-delay: 0.1s"></span>
    <span class="dot" style="animation-delay: 0.2s"></span>
  </div>
</template>

<style scoped>
.loading-dots {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.dot {
  width: 0.5rem;
  height: 0.5rem;
  background: var(--color-text-tertiary);
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.loading-dots.sm .dot {
  width: 0.375rem;
  height: 0.375rem;
}

.loading-dots.lg .dot {
  width: 0.625rem;
  height: 0.625rem;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}
</style>
