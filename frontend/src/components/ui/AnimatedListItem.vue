<script setup lang="ts">
/**
 * AnimatedListItem 动画列表项组件
 * 配合 AnimatedList 使用，提供单个列表项的动画
 */
import { cn } from '@/lib/utils'

interface Props {
  class?: string
  visible?: boolean
  index?: number
  stagger?: number
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  index: 0,
  stagger: 100,
})
</script>

<template>
  <div
    :class="cn('animated-list-item', props.class, { visible: props.visible })"
    :style="{
      '--delay': `${props.index * props.stagger}ms`,
    }"
  >
    <slot />
  </div>
</template>

<style scoped>
.animated-list-item {
  opacity: 0;
  transform: translateY(20px);
  transition: opacity 0.4s ease, transform 0.4s ease;
  transition-delay: var(--delay);
}

.animated-list-item.visible {
  opacity: 1;
  transform: translateY(0);
}
</style>
