<script setup lang="ts">
/**
 * TextReveal 文字揭示动画组件
 * 文字逐字显示的动画效果
 */
import { ref, onMounted } from 'vue'
import { cn } from '@/lib/utils'

interface Props {
  class?: string
  text: string
  delay?: number
  duration?: number
  gradient?: string
}

const props = withDefaults(defineProps<Props>(), {
  delay: 0,
  duration: 0.05,
  gradient: 'from-foreground via-primary to-foreground',
})

const isVisible = ref(false)

onMounted(() => {
  setTimeout(() => {
    isVisible.value = true
  }, props.delay)
})

const words = props.text.split(' ')
</script>

<template>
  <span :class="cn('text-reveal', props.class)">
    <span
      v-for="(word, wordIndex) in words"
      :key="wordIndex"
      class="word"
    >
      <span
        v-for="(char, charIndex) in word"
        :key="charIndex"
        class="char"
        :class="{ visible: isVisible }"
        :style="{
          '--delay': `${wordIndex * 0.1 + charIndex * props.duration}s`,
        }"
      >
        {{ char }}
      </span>
      <span v-if="wordIndex < words.length - 1">&nbsp;</span>
    </span>
  </span>
</template>

<style scoped>
.text-reveal {
  display: inline;
}

.word {
  display: inline-block;
  white-space: nowrap;
}

.char {
  display: inline-block;
  opacity: 0;
  transform: translateY(20px) rotateX(-90deg);
  transition: opacity 0.4s ease, transform 0.4s ease;
  transition-delay: var(--delay);
}

.char.visible {
  opacity: 1;
  transform: translateY(0) rotateX(0);
}
</style>
