<script setup lang="ts">
/**
 * App 根组件
 * 使用 Shell 布局和路由
 */
import Shell from '@/components/layout/Shell.vue'
</script>

<template>
  <Shell>
    <router-view />
  </Shell>
</template>

<style>
/* 全局样式已在 style.css 中定义 */
</style>
