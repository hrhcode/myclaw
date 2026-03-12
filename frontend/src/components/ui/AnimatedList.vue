<script setup lang="ts">
/**
 * AnimatedList 动画列表组件
 * 列表项依次进入的动画效果
 */
import { ref, onMounted } from 'vue'
import { cn } from '@/lib/utils'

interface Props {
  class?: string
  delay?: number
  stagger?: number
}

const props = withDefaults(defineProps<Props>(), {
  delay: 0,
  stagger: 100,
})

const isVisible = ref(false)

onMounted(() => {
  setTimeout(() => {
    isVisible.value = true
  }, props.delay)
})
</script>

<template>
  <div :class="cn('animated-list', props.class)">
    <slot :visible="isVisible" :stagger="props.stagger" />
  </div>
</template>

<style scoped>
.animated-list {
  display: contents;
}
</style>
