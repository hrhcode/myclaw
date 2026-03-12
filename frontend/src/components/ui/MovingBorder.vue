<script setup lang="ts">
/**
 * MovingBorder 移动边框组件
 * 边框上有移动的光点效果，适合强调重要元素
 */
import { cn } from '@/lib/utils'

interface Props {
  class?: string
  duration?: number
  borderWidth?: number
  color1?: string
  color2?: string
}

const props = withDefaults(defineProps<Props>(), {
  duration: 4,
  borderWidth: 2,
  color1: 'hsl(var(--primary))',
  color2: 'hsl(var(--chart-3))',
})
</script>

<template>
  <div :class="cn('moving-border-wrapper', props.class)">
    <div
      class="moving-border-bg"
      :style="{
        '--duration': `${props.duration}s`,
        '--color1': props.color1,
        '--color2': props.color2,
      }"
    />
    <div
      class="moving-border-content"
      :style="{
        '--border-width': `${props.borderWidth}px`,
      }"
    >
      <slot />
    </div>
  </div>
</template>

<style scoped>
.moving-border-wrapper {
  position: relative;
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.moving-border-bg {
  position: absolute;
  inset: 0;
  padding: 2px;
  border-radius: inherit;
  background: conic-gradient(
    from var(--angle, 0deg),
    var(--color1) 0%,
    transparent 10%,
    transparent 40%,
    var(--color2) 50%,
    transparent 60%,
    transparent 90%,
    var(--color1) 100%
  );
  animation: rotate-border var(--duration) linear infinite;
}

@property --angle {
  syntax: '<angle>';
  initial-value: 0deg;
  inherits: false;
}

@keyframes rotate-border {
  to {
    --angle: 360deg;
  }
}

.moving-border-content {
  position: relative;
  background: hsl(var(--card));
  border-radius: calc(var(--radius-lg) - var(--border-width));
  margin: var(--border-width);
  height: calc(100% - var(--border-width) * 2);
}
</style>
