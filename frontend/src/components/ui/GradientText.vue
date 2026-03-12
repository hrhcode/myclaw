<script setup lang="ts">
import { ref, onMounted } from "vue";
import { cn } from "@/lib/utils";

interface Props {
  class?: string;
  text: string;
  gradient?: string;
}

const props = withDefaults(defineProps<Props>(), {
  gradient: "from-blue-500 via-purple-500 to-cyan-500",
});

const isVisible = ref(false);

onMounted(() => {
  setTimeout(() => {
    isVisible.value = true;
  }, 100);
});
</script>

<template>
  <h1
    :class="cn(
      'text-4xl font-bold tracking-tight transition-all duration-700',
      isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4',
      props.class
    )"
  >
    <span
      :class="cn('bg-clip-text text-transparent bg-gradient-to-r bg-gradient-to-r', props.gradient)"
    >
      {{ props.text }}
    </span>
  </h1>
</template>
