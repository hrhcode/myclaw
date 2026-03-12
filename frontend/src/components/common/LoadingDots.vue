<script setup lang="ts">
defineProps<{
  size?: 'sm' | 'md' | 'lg'
}>()
</script>

<template>
  <div class="loading-dots" :class="size || 'md'">
    <span class="dot" style="animation-delay: 0s"></span>
    <span class="dot" style="animation-delay: 0.15s"></span>
    <span class="dot" style="animation-delay: 0.3s"></span>
  </div>
</template>

<style scoped>
.loading-dots {
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.dot {
  width: 0.5rem;
  height: 0.5rem;
  background: hsl(var(--primary));
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
  box-shadow: 0 0 10px hsl(var(--primary) / 0.5);
}

.loading-dots.sm .dot {
  width: 0.375rem;
  height: 0.375rem;
}

.loading-dots.lg .dot {
  width: 0.75rem;
  height: 0.75rem;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}
</style>
