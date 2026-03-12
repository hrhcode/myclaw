<script setup lang="ts">
/**
 * ShimmerButton 闪光按钮组件
 * 带有动态闪光效果的按钮，适合主要操作按钮
 */
import { cn } from '@/lib/utils'

interface Props {
  class?: string
  shimmerColor?: string
  shimmerSize?: string
  background?: string
  borderRadius?: string
}

const props = withDefaults(defineProps<Props>(), {
  shimmerColor: '#ffffff',
  shimmerSize: '0.1em',
  background: 'linear-gradient(135deg, hsl(var(--primary)) 0%, hsl(var(--primary) / 0.8) 100%)',
  borderRadius: 'var(--radius)',
})

defineEmits<{
  click: [event: MouseEvent]
}>()
</script>

<template>
  <button
    :class="cn('shimmer-btn', props.class)"
    :style="{
      '--shimmer-color': props.shimmerColor,
      '--shimmer-size': props.shimmerSize,
      '--btn-bg': props.background,
      '--btn-radius': props.borderRadius,
    }"
    @click="$emit('click', $event)"
  >
    <span class="shimmer" />
    <span class="btn-content">
      <slot />
    </span>
  </button>
</template>

<style scoped>
.shimmer-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.625rem 1.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: hsl(var(--primary-foreground));
  background: var(--btn-bg);
  border: none;
  border-radius: var(--btn-radius);
  cursor: pointer;
  overflow: hidden;
  isolation: isolate;
  transition: transform 0.2s, box-shadow 0.2s;
}

.shimmer-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 20px hsl(var(--primary) / 0.4);
}

.shimmer-btn:active {
  transform: scale(0.98);
}

.shimmer {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    90deg,
    transparent 0%,
    var(--shimmer-color) 50%,
    transparent 100%
  );
  background-size: 200% 100%;
  animation: shimmer-slide 3s ease-in-out infinite;
  opacity: 0.3;
  mix-blend-mode: overlay;
}

.btn-content {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

@keyframes shimmer-slide {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
</style>
