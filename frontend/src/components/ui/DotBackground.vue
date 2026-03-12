<script setup lang="ts">
import { cn } from "@/lib/utils";

interface Props {
  class?: string;
  squareSize?: number;
  dotSize?: number;
  dotColor?: string;
}

const props = withDefaults(defineProps<Props>(), {
  squareSize: 40,
  dotSize: 1,
  dotColor: "hsl(var(--muted-foreground))",
});
</script>

<template>
  <div :class="cn('absolute inset-0 overflow-hidden pointer-events-none', props.class)">
    <div
      class="absolute inset-0"
      :style="{
        backgroundImage: `radial-gradient(${props.dotColor} ${props.dotSize}px, transparent ${props.dotSize}px)`,
        backgroundSize: `${props.squareSize}px ${props.squareSize}px`,
      }"
    />
  </div>
</template>
