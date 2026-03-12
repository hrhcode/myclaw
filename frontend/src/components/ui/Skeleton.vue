<script setup lang="ts">
/**
 * Skeleton 骨架屏组件
 * 提供加载占位效果
 */
defineProps<{
  width?: string
  height?: string
  rows?: number
  circle?: boolean
}>()
</script>

<template>
  <div class="skeleton-wrapper">
    <div
      v-if="!rows"
      class="skeleton"
      :class="{ circle }"
      :style="{ width, height }"
    />
    <div v-else class="skeleton-rows">
      <div
        v-for="i in rows"
        :key="i"
        class="skeleton"
        :style="{ width: i === rows ? '70%' : undefined }"
      />
    </div>
  </div>
</template>

<style scoped>
.skeleton-wrapper {
  display: inline-flex;
}

.skeleton {
  background: linear-gradient(
    90deg,
    hsl(var(--muted)) 25%,
    hsl(var(--muted) / 0.5) 50%,
    hsl(var(--muted)) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: var(--radius);
  width: 100%;
  height: 1rem;
}

.circle {
  border-radius: 50%;
}

.skeleton-rows {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  width: 100%;
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
</style>
