<script setup lang="ts">
/**
 * 系统设置页面
 * 提供配置管理功能
 */
import { ref, reactive, onMounted, computed } from 'vue'
import { configApi, type AppConfig } from '@/api/settings'
import { Card, Button, Input, Toggle, Textarea, Badge, Modal, Skeleton } from '@/components/ui'
import { useToast } from '@/composables/useToast'

const toast = useToast()

const loading = ref(false)
const saving = ref(false)
const config = ref<AppConfig | null>(null)
const activeTab = ref<'llm' | 'memory' | 'agent' | 'gateway' | 'server'>('llm')
const showExportModal = ref(false)
const showImportModal = ref(false)
const importJson = ref('')

const formData = reactive({
  llm: {
    provider: '',
    model: '',
    api_key: '',
  },
  memory: {
    enabled: false,
    max_memories: 1000,
    embedding: {
      provider: '',
      model: '',
      api_key: '',
      base_url: '',
    },
    hybrid_search: {
      enabled: true,
      vector_weight: 0.7,
      fts_weight: 0.3,
      min_score: 0.5,
    },
  },
  agent: {
    system_prompt: '',
  },
  gateway: {
    enabled: true,
  },
  server: {
    port: 18790,
    host: '0.0.0.0',
  },
})

const errors = reactive<Record<string, string>>({})

const tabs = [
  { id: 'llm', label: 'LLM 配置', icon: 'M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z' },
  { id: 'memory', label: '记忆系统', icon: 'M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4' },
  { id: 'agent', label: 'Agent 配置', icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z' },
  { id: 'gateway', label: 'Gateway', icon: 'M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01' },
  { id: 'server', label: '服务器', icon: 'M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2' },
]

onMounted(async () => {
  await loadConfig()
})

async function loadConfig() {
  loading.value = true
  try {
    config.value = await configApi.get()
    
    formData.llm = {
      provider: config.value.llm?.provider || '',
      model: config.value.llm?.model || '',
      api_key: config.value.llm?.api_key || '',
    }
    
    formData.memory = {
      enabled: config.value.memory?.enabled || false,
      max_memories: config.value.memory?.max_memories || 1000,
      embedding: {
        provider: config.value.memory?.embedding?.provider || '',
        model: config.value.memory?.embedding?.model || '',
        api_key: config.value.memory?.embedding?.api_key || '',
        base_url: config.value.memory?.embedding?.base_url || '',
      },
      hybrid_search: {
        enabled: config.value.memory?.hybrid_search?.enabled ?? true,
        vector_weight: config.value.memory?.hybrid_search?.vector_weight || 0.7,
        fts_weight: config.value.memory?.hybrid_search?.fts_weight || 0.3,
        min_score: config.value.memory?.hybrid_search?.min_score || 0.5,
      },
    }
    
    formData.agent = {
      system_prompt: config.value.agent?.system_prompt || '',
    }
    
    formData.gateway = {
      enabled: config.value.gateway?.enabled ?? true,
    }
    
    formData.server = {
      port: config.value.server?.port || 18790,
      host: config.value.server?.host || '0.0.0.0',
    }
  } catch (error) {
    toast.error('加载配置失败')
  } finally {
    loading.value = false
  }
}

function validate(): boolean {
  Object.keys(errors).forEach(key => delete errors[key])
  
  if (activeTab.value === 'llm') {
    if (!formData.llm.provider) {
      errors['llm.provider'] = '请输入提供商'
    }
    if (!formData.llm.model) {
      errors['llm.model'] = '请输入模型名称'
    }
    if (!formData.llm.api_key) {
      errors['llm.api_key'] = '请输入 API Key'
    }
  }
  
  if (activeTab.value === 'memory' && formData.memory.enabled) {
    if (!formData.memory.embedding.provider) {
      errors['memory.embedding.provider'] = '请输入 Embedding 提供商'
    }
    if (!formData.memory.embedding.model) {
      errors['memory.embedding.model'] = '请输入 Embedding 模型'
    }
  }
  
  if (activeTab.value === 'server') {
    if (formData.server.port < 1 || formData.server.port > 65535) {
      errors['server.port'] = '端口号必须在 1-65535 之间'
    }
    if (!formData.server.host) {
      errors['server.host'] = '请输入监听地址'
    }
  }
  
  return Object.keys(errors).length === 0
}

async function saveConfig() {
  if (!validate()) {
    toast.error('请检查表单错误')
    return
  }
  
  saving.value = true
  try {
    await configApi.update({
      llm_provider: formData.llm.provider,
      llm_model: formData.llm.model,
      llm_api_key: formData.llm.api_key,
      memory_enabled: formData.memory.enabled,
      embedding_provider: formData.memory.embedding.provider,
      embedding_model: formData.memory.embedding.model,
      embedding_api_key: formData.memory.embedding.api_key,
      embedding_base_url: formData.memory.embedding.base_url,
      vector_weight: formData.memory.hybrid_search.vector_weight,
      fts_weight: formData.memory.hybrid_search.fts_weight,
      min_score: formData.memory.hybrid_search.min_score,
      system_prompt: formData.agent.system_prompt,
    })
    toast.success('配置已保存')
    await loadConfig()
  } catch (error) {
    toast.error('保存配置失败')
  } finally {
    saving.value = false
  }
}

async function reloadConfig() {
  try {
    await configApi.reload()
    toast.success('配置已重新加载')
    await loadConfig()
  } catch (error) {
    toast.error('重新加载失败')
  }
}

function exportConfig() {
  const configJson = JSON.stringify(config.value, null, 2)
  const blob = new Blob([configJson], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `myclaw-config-${new Date().toISOString().slice(0, 10)}.json`
  a.click()
  URL.revokeObjectURL(url)
  toast.success('配置已导出')
}

function importConfig() {
  try {
    const imported = JSON.parse(importJson.value)
    config.value = imported
    loadConfig()
    showImportModal.value = false
    importJson.value = ''
    toast.success('配置已导入')
  } catch (error) {
    toast.error('配置格式错误')
  }
}
</script>

<template>
  <div class="settings-page">
    <div class="page-header">
      <div class="header-content">
        <h1>系统设置</h1>
        <p class="header-subtitle">配置 LLM、记忆系统和 Agent 参数</p>
      </div>
      <div class="header-actions">
        <Button variant="secondary" size="sm" @click="showImportModal = true">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
          </svg>
          导入
        </Button>
        <Button variant="secondary" size="sm" @click="exportConfig">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          导出
        </Button>
        <Button variant="secondary" size="sm" @click="reloadConfig">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          重载
        </Button>
      </div>
    </div>

    <div class="settings-layout">
      <div class="settings-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          class="tab-button"
          :class="{ active: activeTab === tab.id }"
          @click="activeTab = tab.id as any"
        >
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="tab.icon" />
          </svg>
          <span>{{ tab.label }}</span>
        </button>
      </div>

      <Card class="settings-content">
        <div v-if="loading" class="loading-skeleton">
          <Skeleton :rows="5" />
        </div>

        <template v-else>
          <div v-show="activeTab === 'llm'" class="form-section">
            <h3 class="section-title">LLM 配置</h3>
            <p class="section-desc">配置大语言模型的提供商和参数</p>
            
            <div class="form-group">
              <label class="form-label">提供商</label>
              <Input v-model="formData.llm.provider" placeholder="openai / anthropic / deepseek" />
              <p v-if="errors['llm.provider']" class="form-error">{{ errors['llm.provider'] }}</p>
            </div>
            
            <div class="form-group">
              <label class="form-label">模型</label>
              <Input v-model="formData.llm.model" placeholder="gpt-4o / claude-3-sonnet" />
              <p v-if="errors['llm.model']" class="form-error">{{ errors['llm.model'] }}</p>
            </div>
            
            <div class="form-group">
              <label class="form-label">API Key</label>
              <Input v-model="formData.llm.api_key" type="password" placeholder="sk-..." />
              <p v-if="errors['llm.api_key']" class="form-error">{{ errors['llm.api_key'] }}</p>
              <p class="form-hint">API Key 将被安全存储，不会在前端明文显示</p>
            </div>
          </div>

          <div v-show="activeTab === 'memory'" class="form-section">
            <h3 class="section-title">记忆系统配置</h3>
            <p class="section-desc">配置对话记忆和向量检索功能</p>
            
            <div class="form-group">
              <label class="form-label">启用记忆系统</label>
              <Toggle v-model="formData.memory.enabled" />
            </div>
            
            <template v-if="formData.memory.enabled">
              <div class="form-group">
                <label class="form-label">最大记忆条数</label>
                <Input v-model="formData.memory.max_memories" type="number" placeholder="1000" />
              </div>
              
              <h4 class="subsection-title">Embedding 配置</h4>
              
              <div class="form-row">
                <div class="form-group">
                  <label class="form-label">提供商</label>
                  <Input v-model="formData.memory.embedding.provider" placeholder="openai" />
                </div>
                <div class="form-group">
                  <label class="form-label">模型</label>
                  <Input v-model="formData.memory.embedding.model" placeholder="text-embedding-3-small" />
                </div>
              </div>
              
              <div class="form-row">
                <div class="form-group">
                  <label class="form-label">API Key</label>
                  <Input v-model="formData.memory.embedding.api_key" type="password" placeholder="sk-..." />
                </div>
                <div class="form-group">
                  <label class="form-label">Base URL</label>
                  <Input v-model="formData.memory.embedding.base_url" placeholder="https://api.openai.com/v1" />
                </div>
              </div>
              
              <h4 class="subsection-title">混合搜索配置</h4>
              
              <div class="form-group">
                <label class="form-label">启用混合搜索</label>
                <Toggle v-model="formData.memory.hybrid_search.enabled" />
              </div>
              
              <template v-if="formData.memory.hybrid_search.enabled">
                <div class="form-row">
                  <div class="form-group">
                    <label class="form-label">向量权重</label>
                    <Input v-model="formData.memory.hybrid_search.vector_weight" type="number" placeholder="0.7" />
                    <p class="form-hint">取值范围 0-1</p>
                  </div>
                  <div class="form-group">
                    <label class="form-label">全文权重</label>
                    <Input v-model="formData.memory.hybrid_search.fts_weight" type="number" placeholder="0.3" />
                    <p class="form-hint">取值范围 0-1</p>
                  </div>
                </div>
                
                <div class="form-group">
                  <label class="form-label">最低分数阈值</label>
                  <Input v-model="formData.memory.hybrid_search.min_score" type="number" placeholder="0.5" />
                  <p class="form-hint">低于此分数的结果将被过滤</p>
                </div>
              </template>
            </template>
          </div>

          <div v-show="activeTab === 'agent'" class="form-section">
            <h3 class="section-title">Agent 配置</h3>
            <p class="section-desc">配置 AI Agent 的行为参数</p>
            
            <div class="form-group">
              <label class="form-label">系统提示词</label>
              <Textarea v-model="formData.agent.system_prompt" :rows="8" placeholder="你是一个有帮助的 AI 助手..." />
              <p class="form-hint">定义 Agent 的角色和行为准则</p>
            </div>
          </div>

          <div v-show="activeTab === 'gateway'" class="form-section">
            <h3 class="section-title">Gateway 配置</h3>
            <p class="section-desc">配置消息网关的启动选项</p>
            
            <div class="form-group">
              <label class="form-label">启用 Gateway</label>
              <Toggle v-model="formData.gateway.enabled" />
              <p class="form-hint">启用后系统启动时会自动启动消息网关</p>
            </div>
            
            <div class="gateway-info">
              <div class="info-item">
                <span class="info-label">当前状态</span>
                <Badge :variant="config?.gateway?.enabled ? 'success' : 'default'">
                  {{ config?.gateway?.enabled ? '已启用' : '已禁用' }}
                </Badge>
              </div>
            </div>
          </div>

          <div v-show="activeTab === 'server'" class="form-section">
            <h3 class="section-title">服务器配置</h3>
            <p class="section-desc">配置 HTTP 服务器参数（需要重启生效）</p>
            
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">监听端口</label>
                <Input v-model="formData.server.port" type="number" placeholder="18790" />
                <p v-if="errors['server.port']" class="form-error">{{ errors['server.port'] }}</p>
              </div>
              <div class="form-group">
                <label class="form-label">监听地址</label>
                <Input v-model="formData.server.host" placeholder="0.0.0.0" />
                <p v-if="errors['server.host']" class="form-error">{{ errors['server.host'] }}</p>
              </div>
            </div>
            
            <div class="server-warning">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <span>修改服务器配置后需要重启后端服务才能生效</span>
            </div>
          </div>

          <div class="form-actions">
            <Button variant="secondary" @click="loadConfig">重置</Button>
            <Button variant="primary" :loading="saving" @click="saveConfig">保存配置</Button>
          </div>
        </template>
      </Card>
    </div>

    <Modal v-model="showImportModal" title="导入配置" size="md">
      <div class="import-form">
        <p class="import-hint">请粘贴导出的配置 JSON：</p>
        <Textarea v-model="importJson" :rows="10" placeholder='{"llm": {...}, ...}' />
      </div>
      <template #footer>
        <Button variant="secondary" @click="showImportModal = false">取消</Button>
        <Button variant="primary" @click="importConfig">导入</Button>
      </template>
    </Modal>
  </div>
</template>

<style scoped>
.settings-page {
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

.header-actions {
  display: flex;
  gap: 0.5rem;
}

.settings-layout {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.settings-tabs {
  display: flex;
  gap: 0.25rem;
  padding: 0.25rem;
  background: hsl(var(--muted) / 0.3);
  border-radius: var(--radius);
  flex-wrap: wrap;
}

.tab-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1rem;
  background: transparent;
  border: none;
  border-radius: var(--radius);
  font-size: 0.875rem;
  color: hsl(var(--muted-foreground));
  cursor: pointer;
  transition: all 0.2s;
}

.tab-button:hover {
  background: hsl(var(--muted) / 0.5);
  color: hsl(var(--foreground));
}

.tab-button.active {
  background: hsl(var(--background));
  color: hsl(var(--foreground));
  font-weight: 500;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.tab-button svg {
  width: 1rem;
  height: 1rem;
  flex-shrink: 0;
}

.settings-content {
  min-height: 400px;
}

.loading-skeleton {
  padding: 1rem;
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.section-title {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0 0 0.25rem 0;
}

.section-desc {
  font-size: 0.875rem;
  color: hsl(var(--muted-foreground));
  margin: 0 0 0.5rem 0;
}

.subsection-title {
  font-size: 0.875rem;
  font-weight: 600;
  margin: 0.5rem 0 0.75rem 0;
  color: hsl(var(--muted-foreground));
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: hsl(var(--foreground));
}

.form-hint {
  font-size: 0.75rem;
  color: hsl(var(--muted-foreground));
  margin: 0;
}

.form-error {
  font-size: 0.75rem;
  color: hsl(var(--destructive));
  margin: 0;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid hsl(var(--border));
}

.gateway-info,
.server-warning {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  background: hsl(var(--muted) / 0.3);
  border-radius: var(--radius);
}

.info-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.info-label {
  font-size: 0.875rem;
  color: hsl(var(--muted-foreground));
}

.server-warning {
  color: hsl(var(--chart-1));
}

.server-warning svg {
  width: 1.25rem;
  height: 1.25rem;
  flex-shrink: 0;
}

.import-form {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.import-hint {
  font-size: 0.875rem;
  color: hsl(var(--muted-foreground));
  margin: 0;
}

@media (max-width: 768px) {
  .settings-tabs {
    flex-wrap: wrap;
  }
  
  .tab-button {
    white-space: nowrap;
  }
  
  .form-row {
    grid-template-columns: 1fr;
  }
  
  .page-header {
    flex-direction: column;
    gap: 1rem;
  }
  
  .header-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
