<script setup lang="ts">
/**
 * StatsCard 统计卡片组件
 * 带有动画数字和发光效果的统计展示卡片
 */
import { ref, onMounted, watch, computed } from 'vue'
import { cn } from '@/lib/utils'

interface Props {
  class?: string
  title: string
  value: number | string
  suffix?: string
  prefix?: string
  icon?: string
  trend?: 'up' | 'down' | 'neutral'
  trendValue?: string
  glowColor?: string
  animate?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  glowColor: 'hsl(var(--primary))',
  animate: true,
})

const displayValue = ref(0)
const isAnimating = ref(false)
const cardRef = ref<HTMLDivElement | null>(null)

const numericValue = computed(() => {
  if (typeof props.value === 'number') return props.value
  const parsed = parseFloat(props.value)
  return isNaN(parsed) ? 0 : parsed
})

const formattedValue = computed(() => {
  if (typeof props.value === 'string') return props.value
  return displayValue.value.toLocaleString()
})

function animateValue(start: number, end: number, duration: number) {
  if (!props.animate) {
    displayValue.value = end
    return
  }
  
  const startTime = performance.now()
  
  function update(currentTime: number) {
    const elapsed = currentTime - startTime
    const progress = Math.min(elapsed / duration, 1)
    const easeProgress = 1 - Math.pow(1 - progress, 3)
    displayValue.value = Math.floor(start + (end - start) * easeProgress)
    
    if (progress < 1) {
      requestAnimationFrame(update)
    }
  }
  
  requestAnimationFrame(update)
}

onMounted(() => {
  if (props.animate && cardRef.value) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !isAnimating.value) {
            isAnimating.value = true
            animateValue(0, numericValue.value, 1000)
          }
        })
      },
      { threshold: 0.1 }
    )
    observer.observe(cardRef.value)
  } else {
    displayValue.value = numericValue.value
  }
})

watch(() => props.value, (newVal) => {
  if (typeof newVal === 'number') {
    animateValue(displayValue.value, newVal, 500)
  }
})
</script>

<template>
  <div
    ref="cardRef"
    :class="cn('stats-card', props.class)"
    :style="{ '--glow-color': props.glowColor }"
  >
    <div class="stats-glow" />
    <div class="stats-content">
      <div class="stats-header">
        <span class="stats-title">{{ title }}</span>
        <div v-if="icon" class="stats-icon">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="icon" />
          </svg>
        </div>
      </div>
      <div class="stats-value-wrapper">
        <span v-if="prefix" class="stats-prefix">{{ prefix }}</span>
        <span class="stats-value">{{ formattedValue }}</span>
        <span v-if="suffix" class="stats-suffix">{{ suffix }}</span>
      </div>
      <div v-if="trend" class="stats-trend" :class="trend">
        <svg v-if="trend === 'up'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" />
        </svg>
        <svg v-else-if="trend === 'down'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
        </svg>
        <span>{{ trendValue }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stats-card {
  position: relative;
  padding: 1.5rem;
  background: hsl(var(--card));
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: all 0.3s ease;
}

.stats-card:hover {
  border-color: hsl(var(--primary) / 0.3);
  transform: translateY(-2px);
}

.stats-card:hover .stats-glow {
  opacity: 1;
}

.stats-glow {
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle at center, var(--glow-color) 0%, transparent 70%);
  opacity: 0;
  transition: opacity 0.5s ease;
  pointer-events: none;
}

.stats-content {
  position: relative;
  z-index: 1;
}

.stats-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.stats-title {
  font-size: 0.875rem;
  font-weight: 500;
  color: hsl(var(--muted-foreground));
}

.stats-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: hsl(var(--primary) / 0.1);
  border-radius: var(--radius);
  color: hsl(var(--primary));
}

.stats-icon svg {
  width: 18px;
  height: 18px;
}

.stats-value-wrapper {
  display: flex;
  align-items: baseline;
  gap: 0.25rem;
}

.stats-value {
  font-size: 2rem;
  font-weight: 700;
  color: hsl(var(--foreground));
  letter-spacing: -0.02em;
  font-variant-numeric: tabular-nums;
}

.stats-prefix,
.stats-suffix {
  font-size: 1rem;
  font-weight: 500;
  color: hsl(var(--muted-foreground));
}

.stats-trend {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  margin-top: 0.5rem;
  font-size: 0.75rem;
  font-weight: 500;
}

.stats-trend svg {
  width: 14px;
  height: 14px;
}

.stats-trend.up {
  color: hsl(var(--chart-2));
}

.stats-trend.down {
  color: hsl(var(--destructive));
}

.stats-trend.neutral {
  color: hsl(var(--muted-foreground));
}
</style>
