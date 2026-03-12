<script setup lang="ts">
/**
 * 工具管理页面
 * 提供工具列表查看和启用/禁用功能
 */
import { ref, onMounted, computed } from 'vue'
import { toolsApi, type Tool } from '@/api/settings'
import { Card, Button, Badge, Toggle, Empty, Skeleton } from '@/components/ui'
import { useToast } from '@/composables/useToast'

const toast = useToast()

const tools = ref<Tool[]>([])
const loading = ref(false)
const searchQuery = ref('')

const filteredTools = computed(() => {
  if (!searchQuery.value) return tools.value
  const query = searchQuery.value.toLowerCase()
  return tools.value.filter(tool => 
    tool.name.toLowerCase().includes(query) ||
    tool.description.toLowerCase().includes(query)
  )
})

const enabledCount = computed(() => tools.value.filter(t => t.enabled).length)

onMounted(async () => {
  await loadTools()
})

async function loadTools() {
  loading.value = true
  try {
    const result = await toolsApi.list()
    tools.value = result.tools
  } catch (error) {
    toast.error('加载工具列表失败')
  } finally {
    loading.value = false
  }
}

async function toggleTool(tool: Tool) {
  try {
    await toolsApi.setEnabled(tool.name, !tool.enabled)
    tool.enabled = !tool.enabled
    toast.success(`工具 ${tool.name} 已${tool.enabled ? '启用' : '禁用'}`)
  } catch (error) {
    toast.error('操作失败')
  }
}

function getToolIcon(name: string): string {
  const icons: Record<string, string> = {
    web_search: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z',
    web_fetch: 'M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4',
    current_time: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z',
  }
  return icons[name] || 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z'
}

function getToolCategory(name: string): string {
  const categories: Record<string, string> = {
    web_search: '搜索',
    web_fetch: '网络',
    current_time: '工具',
  }
  return categories[name] || '其他'
}

function getParamTypeColor(type: string): string {
  const colors: Record<string, string> = {
    string: 'hsl(var(--primary))',
    number: 'hsl(var(--chart-2))',
    integer: 'hsl(var(--chart-2))',
    boolean: 'hsl(var(--chart-1))',
    array: 'hsl(var(--chart-3))',
    object: 'hsl(var(--chart-4))',
  }
  return colors[type] || 'hsl(var(--muted-foreground))'
}
</script>

<template>
  <div class="tools-page">
    <div class="page-header">
      <div class="header-content">
        <h1>工具管理</h1>
        <p class="header-subtitle">配置 AI 可用的工具</p>
      </div>
      <Button variant="secondary" :loading="loading" @click="loadTools">
        <svg class="icon" :class="{ spinning: loading }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        刷新
      </Button>
    </div>

    <div class="stats-bar">
      <div class="stat-item">
        <span class="stat-value">{{ tools.length }}</span>
        <span class="stat-label">个工具</span>
      </div>
      <div class="stat-item">
        <span class="stat-value">{{ enabledCount }}</span>
        <span class="stat-label">已启用</span>
      </div>
      <div class="stat-item">
        <span class="stat-value">{{ tools.length - enabledCount }}</span>
        <span class="stat-label">已禁用</span>
      </div>
      <div class="search-box">
        <svg class="search-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          v-model="searchQuery"
          type="text"
          class="search-input"
          placeholder="搜索工具..."
        />
      </div>
    </div>

    <div v-if="loading && tools.length === 0" class="loading-skeleton">
      <div v-for="i in 3" :key="i" class="skeleton-card">
        <div class="skeleton-header">
          <Skeleton width="48px" height="48px" />
          <div class="skeleton-info">
            <Skeleton width="120px" height="1.25rem" />
            <Skeleton width="200px" height="0.875rem" />
          </div>
        </div>
        <div class="skeleton-params">
          <Skeleton :rows="2" />
        </div>
      </div>
    </div>

    <Empty
      v-else-if="filteredTools.length === 0"
      icon="search"
      title="未找到工具"
      :description="searchQuery ? '没有匹配的工具' : '暂无可用工具'"
    />

    <div v-else class="tools-list">
      <Card
        v-for="tool in filteredTools"
        :key="tool.name"
        class="tool-card"
        :class="{ disabled: !tool.enabled }"
      >
        <div class="tool-header">
          <div class="tool-icon">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="getToolIcon(tool.name)" />
            </svg>
          </div>
          <div class="tool-info">
            <div class="tool-title-row">
              <h3 class="tool-name">{{ tool.name }}</h3>
              <Badge variant="default" size="sm">{{ getToolCategory(tool.name) }}</Badge>
            </div>
            <p class="tool-description">{{ tool.description }}</p>
          </div>
          <Toggle v-model="tool.enabled" @update:model-value="toggleTool(tool)" />
        </div>
        
        <div class="tool-parameters">
          <h4>参数定义</h4>
          <div v-if="Object.keys(tool.parameters.properties || {}).length > 0" class="params-table">
            <div class="params-header">
              <span class="param-col param-name">参数名</span>
              <span class="param-col param-type">类型</span>
              <span class="param-col param-desc">说明</span>
              <span class="param-col param-req">必填</span>
            </div>
            <div
              v-for="(param, key) in tool.parameters.properties"
              :key="key"
              class="params-row"
            >
              <span class="param-col param-name">
                <code>{{ key }}</code>
              </span>
              <span class="param-col param-type">
                <Badge
                  size="sm"
                  :style="{ background: getParamTypeColor(param.type) + '20', color: getParamTypeColor(param.type) }"
                >
                  {{ param.type }}
                </Badge>
              </span>
              <span class="param-col param-desc">{{ param.description || '-' }}</span>
              <span class="param-col param-req">
                <Badge v-if="tool.parameters.required?.includes(key)" variant="danger" size="sm">
                  必填
                </Badge>
                <span v-else class="muted">可选</span>
              </span>
            </div>
          </div>
          <div v-else class="no-params">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
            </svg>
            <span>无参数</span>
          </div>
        </div>
      </Card>
    </div>
  </div>
</template>

<style scoped>
.tools-page {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
}

.header-content h1 {
  font-size: 1.75rem;
  font-weight: 800;
  margin: 0;
}

.header-subtitle {
  font-size: 0.875rem;
  color: hsl(var(--muted-foreground));
  margin: 0.25rem 0 0 0;
}

.stats-bar {
  display: flex;
  align-items: center;
  gap: 2rem;
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: hsl(var(--card));
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius-lg);
}

.stat-item {
  display: flex;
  align-items: baseline;
  gap: 0.25rem;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: hsl(var(--primary));
}

.stat-label {
  font-size: 0.875rem;
  color: hsl(var(--muted-foreground));
}

.search-box {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-left: auto;
  max-width: 400px;
}

.search-icon {
  width: 1.25rem;
  height: 1.25rem;
  color: hsl(var(--muted-foreground));
}

.search-input {
  flex: 1;
  padding: 0.5rem;
  background: hsl(var(--background));
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius);
  font-size: 0.875rem;
  color: hsl(var(--foreground));
}

.search-input:focus {
  outline: none;
  border-color: hsl(var(--primary));
}

.loading-skeleton {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.skeleton-card {
  background: hsl(var(--card));
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius-lg);
  padding: 1.25rem;
}

.skeleton-header {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.skeleton-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.skeleton-params {
  padding-top: 1rem;
  border-top: 1px solid hsl(var(--border));
}

.tools-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.tool-card {
  padding: 0;
  transition: opacity 0.2s;
}

.tool-card.disabled {
  opacity: 0.6;
}

.tool-header {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1.25rem;
}

.tool-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: hsl(var(--primary) / 0.1);
  border-radius: var(--radius);
  flex-shrink: 0;
}

.tool-icon svg {
  width: 24px;
  height: 24px;
  color: hsl(var(--primary));
}

.tool-info {
  flex: 1;
  min-width: 0;
}

.tool-title-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
}

.tool-name {
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

.tool-description {
  font-size: 0.875rem;
  color: hsl(var(--muted-foreground));
  margin: 0;
}

.tool-parameters {
  padding: 1rem 1.25rem;
  border-top: 1px solid hsl(var(--border));
  background: hsl(var(--muted) / 0.2);
}

.tool-parameters h4 {
  font-size: 0.75rem;
  font-weight: 600;
  color: hsl(var(--muted-foreground));
  margin: 0 0 0.75rem 0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.params-table {
  display: flex;
  flex-direction: column;
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius);
  overflow: hidden;
}

.params-header {
  display: grid;
  grid-template-columns: 1fr 80px 2fr 60px;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: hsl(var(--muted) / 0.5);
  font-size: 0.6875rem;
  font-weight: 600;
  color: hsl(var(--muted-foreground));
  text-transform: uppercase;
}

.params-row {
  display: grid;
  grid-template-columns: 1fr 80px 2fr 60px;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border-top: 1px solid hsl(var(--border));
  font-size: 0.8125rem;
}

.param-col {
  display: flex;
  align-items: center;
}

.param-name code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.8125rem;
  background: hsl(var(--muted) / 0.5);
  padding: 0.125rem 0.375rem;
  border-radius: var(--radius);
}

.param-desc {
  color: hsl(var(--muted-foreground));
}

.muted {
  font-size: 0.75rem;
  color: hsl(var(--muted-foreground));
}

.no-params {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 1rem;
  color: hsl(var(--muted-foreground));
  font-size: 0.875rem;
}

.no-params svg {
  width: 1.25rem;
  height: 1.25rem;
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

@media (max-width: 768px) {
  .stats-bar {
    flex-wrap: wrap;
    gap: 1rem;
  }
  
  .search-box {
    width: 100%;
    max-width: none;
    margin-left: 0;
    margin-top: 0.5rem;
  }
  
  .params-header,
  .params-row {
    grid-template-columns: 1fr 60px 1fr;
  }
  
  .param-req {
    display: none;
  }
}
</style>
