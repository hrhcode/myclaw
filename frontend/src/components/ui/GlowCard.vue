<script setup lang="ts">
/**
 * GlowCard 发光卡片组件
 * 带有动态发光边框效果的卡片，支持鼠标跟随光效
 */
import { ref, onMounted, onUnmounted } from 'vue'
import { cn } from '@/lib/utils'

interface Props {
  class?: string
  glowColor?: string
  hoverGlow?: boolean
  borderWidth?: number
}

const props = withDefaults(defineProps<Props>(), {
  glowColor: 'rgba(59, 130, 246, 0.5)',
  hoverGlow: true,
  borderWidth: 1,
})

const cardRef = ref<HTMLDivElement | null>(null)
const mousePosition = ref({ x: 0, y: 0 })
const isHovering = ref(false)

function handleMouseMove(e: MouseEvent) {
  if (cardRef.value && props.hoverGlow) {
    const rect = cardRef.value.getBoundingClientRect()
    mousePosition.value = {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    }
  }
}

function handleMouseEnter() {
  isHovering.value = true
}

function handleMouseLeave() {
  isHovering.value = false
}

onMounted(() => {
  if (cardRef.value) {
    cardRef.value.addEventListener('mousemove', handleMouseMove)
    cardRef.value.addEventListener('mouseenter', handleMouseEnter)
    cardRef.value.addEventListener('mouseleave', handleMouseLeave)
  }
})

onUnmounted(() => {
  if (cardRef.value) {
    cardRef.value.removeEventListener('mousemove', handleMouseMove)
    cardRef.value.removeEventListener('mouseenter', handleMouseEnter)
    cardRef.value.removeEventListener('mouseleave', handleMouseLeave)
  }
})
</script>

<template>
  <div
    ref="cardRef"
    :class="cn('glow-card', props.class)"
    :style="{
      '--glow-color': props.glowColor,
      '--border-width': `${props.borderWidth}px`,
    }"
  >
    <div
      v-if="hoverGlow"
      class="glow-effect"
      :style="{
        opacity: isHovering ? 1 : 0,
        background: `radial-gradient(600px circle at ${mousePosition.x}px ${mousePosition.y}px, ${props.glowColor}, transparent 40%)`,
      }"
    />
    <div class="card-border" />
    <div class="card-content">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.glow-card {
  position: relative;
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: hsl(var(--card));
}

.glow-effect {
  position: absolute;
  inset: 0;
  pointer-events: none;
  transition: opacity 0.3s ease;
  z-index: 1;
}

.card-border {
  position: absolute;
  inset: 0;
  border-radius: inherit;
  padding: var(--border-width);
  background: linear-gradient(
    135deg,
    hsl(var(--border)) 0%,
    hsl(var(--border)) 50%,
    hsl(var(--primary) / 0.3) 100%
  );
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
  z-index: 2;
}

.glow-card:hover .card-border {
  background: linear-gradient(
    135deg,
    var(--glow-color) 0%,
    hsl(var(--border)) 50%,
    var(--glow-color) 100%
  );
}

.card-content {
  position: relative;
  z-index: 3;
  height: 100%;
}
</style>
