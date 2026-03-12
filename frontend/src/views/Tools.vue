<script setup lang="ts">
/**
 * 工具管理页面
 * 提供工具列表查看和启用/禁用功能
 */
import { ref, onMounted } from 'vue'
import { toolsApi, type Tool } from '@/api/settings'

const tools = ref<Tool[]>([])
const loading = ref(false)
const message = ref<{ type: 'success' | 'error'; text: string } | null>(null)

onMounted(async () => {
  await loadTools()
})

async function loadTools() {
  loading.value = true
  try {
    const result = await toolsApi.list()
    tools.value = result.tools
  } catch (error) {
    showMessage('error', '加载工具列表失败')
  } finally {
    loading.value = false
  }
}

async function toggleTool(tool: Tool) {
  try {
    await toolsApi.setEnabled(tool.name, !tool.enabled)
    tool.enabled = !tool.enabled
    showMessage('success', `工具 ${tool.name} 已${tool.enabled ? '启用' : '禁用'}`)
  } catch (error) {
    showMessage('error', '操作失败')
  }
}

function getToolIcon(name: string): string {
  const icons: Record<string, string> = {
    web_search: '🔍',
    web_fetch: '🌐',
    current_time: '🕐',
  }
  return icons[name] || '🔧'
}

function showMessage(type: 'success' | 'error', text: string) {
  message.value = { type, text }
  setTimeout(() => {
    message.value = null
  }, 3000)
}
</script>

<template>
  <div class="tools-page">
    <div class="page-header">
      <h1>工具管理</h1>
      <button @click="loadTools" class="btn btn-secondary" :disabled="loading">
        刷新
      </button>
    </div>

    <div v-if="message" class="message" :class="message.type">
      {{ message.text }}
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else class="tools-list">
      <div 
        v-for="tool in tools" 
        :key="tool.name" 
        class="tool-card"
        :class="{ disabled: !tool.enabled }"
      >
        <div class="tool-header">
          <div class="tool-icon">{{ getToolIcon(tool.name) }}</div>
          <div class="tool-info">
            <h3 class="tool-name">{{ tool.name }}</h3>
            <p class="tool-description">{{ tool.description }}</p>
          </div>
          <label class="toggle">
            <input 
              type="checkbox" 
              :checked="tool.enabled" 
              @change="toggleTool(tool)"
            />
            <span class="toggle-slider"></span>
          </label>
        </div>
        
        <div class="tool-parameters">
          <h4>参数</h4>
          <div v-if="Object.keys(tool.parameters.properties || {}).length > 0" class="param-list">
            <div 
              v-for="(param, key) in tool.parameters.properties" 
              :key="key" 
              class="param-item"
            >
              <span class="param-name">{{ key }}</span>
              <span class="param-type">{{ param.type }}</span>
              <span class="param-desc">{{ param.description }}</span>
              <span 
                v-if="tool.parameters.required?.includes(key)" 
                class="param-required"
              >
                必填
              </span>
            </div>
          </div>
          <div v-else class="no-params">
            无参数
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.tools-page {
  max-width: 900px;
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

.message {
  padding: 0.75rem 1rem;
  border-radius: var(--radius);
  margin-bottom: 1rem;
}

.message.success {
  background: hsl(var(--chart-2) / 0.1);
  color: hsl(var(--chart-2));
  border: 1px solid hsl(var(--chart-2) / 0.3);
}

.message.error {
  background: hsl(var(--destructive) / 0.1);
  color: hsl(var(--destructive));
  border: 1px solid hsl(var(--destructive) / 0.3);
}

.loading {
  text-align: center;
  padding: 2rem;
  color: hsl(var(--muted-foreground));
}

.tools-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.tool-card {
  background: hsl(var(--card));
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius-lg);
  padding: 1.25rem;
  transition: all 0.2s;
}

.tool-card.disabled {
  opacity: 0.6;
}

.tool-header {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
}

.tool-icon {
  font-size: 1.5rem;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: hsl(var(--muted) / 0.5);
  border-radius: var(--radius);
  flex-shrink: 0;
}

.tool-info {
  flex: 1;
  min-width: 0;
}

.tool-name {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 0.25rem 0;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

.tool-description {
  font-size: 0.875rem;
  color: hsl(var(--muted-foreground));
  margin: 0;
}

.tool-parameters {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid hsl(var(--border));
}

.tool-parameters h4 {
  font-size: 0.75rem;
  font-weight: 600;
  color: hsl(var(--muted-foreground));
  margin: 0 0 0.5rem 0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.param-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.param-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8125rem;
}

.param-name {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-weight: 500;
  color: hsl(var(--primary));
}

.param-type {
  padding: 0.125rem 0.375rem;
  background: hsl(var(--muted));
  border-radius: var(--radius);
  font-size: 0.6875rem;
  color: hsl(var(--muted-foreground));
}

.param-desc {
  color: hsl(var(--muted-foreground));
  flex: 1;
}

.param-required {
  padding: 0.125rem 0.375rem;
  background: hsl(var(--destructive) / 0.1);
  color: hsl(var(--destructive));
  border-radius: var(--radius);
  font-size: 0.6875rem;
  font-weight: 500;
}

.no-params {
  font-size: 0.8125rem;
  color: hsl(var(--muted-foreground));
}

.toggle {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
  flex-shrink: 0;
}

.toggle input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: hsl(var(--muted));
  transition: 0.3s;
  border-radius: 24px;
}

.toggle-slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: 0.3s;
  border-radius: 50%;
}

.toggle input:checked + .toggle-slider {
  background-color: hsl(var(--primary));
}

.toggle input:checked + .toggle-slider:before {
  transform: translateX(20px);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: var(--radius);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.btn-secondary {
  background: hsl(var(--secondary));
  color: hsl(var(--secondary-foreground));
  border-color: hsl(var(--border));
}

.btn-secondary:hover:not(:disabled) {
  background: hsl(var(--accent));
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .tool-header {
    flex-wrap: wrap;
  }
  
  .param-item {
    flex-wrap: wrap;
  }
}
</style>
