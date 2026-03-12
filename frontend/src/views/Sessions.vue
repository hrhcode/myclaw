<script setup lang="ts">
/**
 * Sessions 会话管理页面
 * 显示和管理所有会话
 */
import { useSessions } from '@/composables/useSessions'
import SessionTable from '@/components/session/SessionTable.vue'

const { sessions, loading, error, filters, deleteSession, refresh } = useSessions()
</script>

<template>
  <div class="sessions-page">
    <div class="page-header">
      <h1>会话管理</h1>
      <button @click="refresh" class="btn btn-secondary" :disabled="loading">
        <svg class="icon" :class="{ spinning: loading }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        刷新
      </button>
    </div>

    <div class="filters">
      <div class="filter-item">
        <label>通道</label>
        <select v-model="filters.channel">
          <option value="">全部</option>
          <option value="web">Web</option>
          <option value="qq">QQ</option>
          <option value="wechat">微信</option>
        </select>
      </div>
      <div class="filter-item">
        <label>数量限制</label>
        <input v-model.number="filters.limit" type="number" min="1" max="100" />
      </div>
    </div>

    <div v-if="error" class="error-message">
      {{ error }}
    </div>

    <SessionTable
      :sessions="sessions"
      :loading="loading"
      @delete="deleteSession"
    />
  </div>
</template>

<style scoped>
.sessions-page {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.page-header h1 {
  font-size: 1.75rem;
  font-weight: 800;
  margin: 0;
}

.filters {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.filter-item label {
  font-size: 0.75rem;
  color: hsl(var(--muted-foreground));
}

.filter-item select,
.filter-item input {
  padding: 0.5rem 0.75rem;
  background: hsl(var(--input));
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius);
  font-size: 0.875rem;
  min-width: 120px;
}

.error-message {
  padding: 1rem;
  background: hsl(var(--destructive) / 0.1);
  border: 1px solid hsl(var(--destructive));
  border-radius: var(--radius);
  color: hsl(var(--destructive));
  margin-bottom: 1rem;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: var(--radius);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary {
  background: hsl(var(--secondary));
  color: hsl(var(--secondary-foreground));
  border: 1px solid hsl(var(--border));
}

.btn-secondary:hover:not(:disabled) {
  background: hsl(var(--accent));
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.icon {
  width: 1rem;
  height: 1rem;
}

.icon.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
