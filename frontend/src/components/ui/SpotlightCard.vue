<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";
import { cn } from "@/lib/utils";

interface Props {
  class?: string;
  containerClass?: string;
  color1?: string;
  color2?: string;
  color3?: string;
  size?: number;
}

const props = withDefaults(defineProps<Props>(), {
  color1: "#3b82f6",
  color2: "#8b5cf6",
  color3: "#06b6d4",
  size: 400,
});

const containerRef = ref<HTMLDivElement | null>(null);
const mousePosition = ref({ x: 0, y: 0 });
const isHovering = ref(false);

function handleMouseMove(e: MouseEvent) {
  if (containerRef.value) {
    const rect = containerRef.value.getBoundingClientRect();
    mousePosition.value = {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    };
  }
}

function handleMouseEnter() {
  isHovering.value = true;
}

function handleMouseLeave() {
  isHovering.value = false;
}

onMounted(() => {
  if (containerRef.value) {
    containerRef.value.addEventListener("mousemove", handleMouseMove);
    containerRef.value.addEventListener("mouseenter", handleMouseEnter);
    containerRef.value.addEventListener("mouseleave", handleMouseLeave);
  }
});

onUnmounted(() => {
  if (containerRef.value) {
    containerRef.value.removeEventListener("mousemove", handleMouseMove);
    containerRef.value.removeEventListener("mouseenter", handleMouseEnter);
    containerRef.value.removeEventListener("mouseleave", handleMouseLeave);
  }
});
</script>

<template>
  <div
    ref="containerRef"
    :class="cn('relative', props.containerClass)"
  >
    <div
      :class="cn('pointer-events-none absolute -inset-px opacity-0 transition duration-300', props.class)"
      :style="{
        opacity: isHovering ? 1 : 0,
        background: `radial-gradient(${props.size}px circle at ${mousePosition.x}px ${mousePosition.y}px, ${props.color1}, ${props.color2}, ${props.color3}, transparent)`,
      }"
    />
    <slot />
  </div>
</template>
