<script setup lang="ts">
import { cn } from "@/lib/utils";

interface Props {
  class?: string;
  duration?: number;
  borderWidth?: number;
  color1?: string;
  color2?: string;
  color3?: string;
}

const props = withDefaults(defineProps<Props>(), {
  duration: 4,
  borderWidth: 2,
  color1: "#3b82f6",
  color2: "#8b5cf6",
  color3: "#06b6d4",
});
</script>

<template>
  <div
    :class="cn('relative p-[1px] overflow-hidden rounded-lg', props.class)"
    :style="{
      background: `linear-gradient(var(--radius), var(--radius), transparent)`,
    }"
  >
    <div
      class="absolute inset-0"
      :style="{
        background: `conic-gradient(from 0deg at 50% 50%, ${props.color1} 0deg, ${props.color2} 120deg, ${props.color3} 240deg, ${props.color1} 360deg)`,
        animation: `spin ${props.duration}s linear infinite`,
      }"
    />
    <div
      class="relative bg-background rounded-lg"
      :style="{
        padding: `${props.borderWidth}px`,
      }"
    >
      <slot />
    </div>
  </div>
</template>

<style scoped>
@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
