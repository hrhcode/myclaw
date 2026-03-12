<script setup lang="ts">
import { cn } from "@/lib/utils";

interface Props {
  class?: string;
  size?: number;
  gridColor?: string;
}

const props = withDefaults(defineProps<Props>(), {
  size: 40,
  gridColor: "hsl(var(--border))",
});
</script>

<template>
  <div :class="cn('absolute inset-0 overflow-hidden pointer-events-none', props.class)">
    <div
      class="absolute inset-0"
      :style="{
        backgroundImage: `linear-gradient(${gridColor} 1px, transparent 1px), linear-gradient(to right, ${gridColor} 1px, transparent 1px)`,
        backgroundSize: `${props.size}px ${props.size}px`,
      }"
    />
  </div>
</template>
