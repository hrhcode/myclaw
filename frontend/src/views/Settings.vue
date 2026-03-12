<script setup lang="ts">
/**
 * 设置页面
 * 提供系统配置管理功能
 */
import { ref, onMounted, computed } from 'vue'
import { configApi, type AppConfig } from '@/api/settings'

const config = ref<AppConfig | null>(null)
const loading = ref(false)
const saving = ref(false)
const message = ref<{ type: 'success' | 'error'; text: string } | null>(null)

const llmProvider = ref('')
const llmModel = ref('')
const llmApiKey = ref('')
const showApiKey = ref(false)

const memoryEnabled = ref(true)
const embeddingProvider = ref('none')
const embeddingApiKey = ref('')
const embeddingBaseUrl = ref('')
const vectorWeight = ref(0.7)
const ftsWeight = ref(0.3)
const minScore = ref(0.3)

const systemPrompt = ref('')

const isFormChanged = computed(() => {
  if (!config.value) return false
  return (
    llmProvider.value !== config.value.llm.provider ||
    llmModel.value !== config.value.llm.model ||
    llmApiKey.value !== config.value.llm.api_key ||
    memoryEnabled.value !== config.value.memory.enabled ||
    embeddingProvider.value !== config.value.memory.embedding.provider ||
    embeddingApiKey.value !== config.value.memory.embedding.api_key ||
    embeddingBaseUrl.value !== config.value.memory.embedding.base_url ||
    vectorWeight.value !== config.value.memory.hybrid_search.vector_weight ||
    ftsWeight.value !== config.value.memory.hybrid_search.fts_weight ||
    minScore.value !== config.value.memory.hybrid_search.min_score ||
    systemPrompt.value !== config.value.agent.system_prompt
  )
})

onMounted(async () => {
  await loadConfig()
})

async function loadConfig() {
  loading.value = true
  try {
    config.value = await configApi.get()
    
    llmProvider.value = config.value.llm.provider
    llmModel.value = config.value.llm.model
    llmApiKey.value = config.value.llm.api_key
    
    memoryEnabled.value = config.value.memory.enabled
    embeddingProvider.value = config.value.memory.embedding.provider
    embeddingApiKey.value = config.value.memory.embedding.api_key
    embeddingBaseUrl.value = config.value.memory.embedding.base_url
    vectorWeight.value = config.value.memory.hybrid_search.vector_weight
    ftsWeight.value = config.value.memory.hybrid_search.fts_weight
    minScore.value = config.value.memory.hybrid_search.min_score
    
    systemPrompt.value = config.value.agent.system_prompt
  } catch (error) {
    showMessage('error', '加载配置失败')
  } finally {
    loading.value = false
  }
}

async function saveConfig() {
  saving.value = true
  try {
    await configApi.update({
      llm_provider: llmProvider.value,
      llm_model: llmModel.value,
      llm_api_key: llmApiKey.value,
      memory_enabled: memoryEnabled.value,
      embedding_provider: embeddingProvider.value,
      embedding_api_key: embeddingApiKey.value,
      embedding_base_url: embeddingBaseUrl.value,
      vector_weight: vectorWeight.value,
      fts_weight: ftsWeight.value,
      min_score: minScore.value,
      system_prompt: systemPrompt.value,
    })
    showMessage('success', '配置已保存')
    await loadConfig()
  } catch (error) {
    showMessage('error', '保存配置失败')
  } finally {
    saving.value = false
  }
}

async function reloadConfig() {
  try {
    await configApi.reload()
    showMessage('success', '配置已重新加载')
    await loadConfig()
  } catch (error) {
    showMessage('error', '重新加载配置失败')
  }
}

function resetToDefault() {
  systemPrompt.value = '你是一个有用的 AI 助手。你可以使用各种工具来帮助用户解决问题。'
}

function showMessage(type: 'success' | 'error', text: string) {
  message.value = { type, text }
  setTimeout(() => {
    message.value = null
  }, 3000)
}
</script>

<template>
  <div class="settings-page">
    <div class="page-header">
      <h1>设置</h1>
      <div class="header-actions">
        <button @click="reloadConfig" class="btn btn-secondary" :disabled="loading">
          重新加载
        </button>
        <button 
          @click="saveConfig" 
          class="btn btn-primary" 
          :disabled="saving || !isFormChanged"
        >
          {{ saving ? '保存中...' : '保存配置' }}
        </button>
      </div>
    </div>

    <div v-if="message" class="message" :class="message.type">
      {{ message.text }}
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else class="settings-content">
      <section class="settings-section">
        <h2>LLM 配置</h2>
        <div class="form-group">
          <label>提供商</label>
          <select v-model="llmProvider" class="form-control">
            <option value="zhipu">智谱 AI</option>
            <option value="openai">OpenAI</option>
            <option value="openrouter">OpenRouter</option>
          </select>
        </div>
        <div class="form-group">
          <label>模型</label>
          <input 
            v-model="llmModel" 
            type="text" 
            class="form-control" 
            placeholder="模型名称"
          />
        </div>
        <div class="form-group">
          <label>API Key</label>
          <div class="input-group">
            <input 
              v-model="llmApiKey" 
              :type="showApiKey ? 'text' : 'password'" 
              class="form-control" 
              placeholder="API Key"
            />
            <button 
              @click="showApiKey = !showApiKey" 
              class="btn btn-icon"
              type="button"
            >
              {{ showApiKey ? '隐藏' : '显示' }}
            </button>
          </div>
        </div>
      </section>

      <section class="settings-section">
        <h2>记忆系统</h2>
        <div class="form-group">
          <label class="checkbox-label">
            <input v-model="memoryEnabled" type="checkbox" />
            启用记忆系统
          </label>
        </div>
        
        <template v-if="memoryEnabled">
          <div class="form-group">
            <label>Embedding 提供商</label>
            <select v-model="embeddingProvider" class="form-control">
              <option value="none">禁用（仅 FTS）</option>
              <option value="zhipu">智谱 AI</option>
              <option value="openrouter">OpenRouter</option>
            </select>
          </div>
          
          <template v-if="embeddingProvider !== 'none'">
            <div class="form-group">
              <label>Embedding API Key</label>
              <input 
                v-model="embeddingApiKey" 
                type="password" 
                class="form-control" 
                placeholder="可选，默认使用 LLM API Key"
              />
            </div>
            <div class="form-group">
              <label>API Base URL</label>
              <input 
                v-model="embeddingBaseUrl" 
                type="text" 
                class="form-control" 
                placeholder="API 基础 URL"
              />
            </div>
          </template>

          <div class="form-row">
            <div class="form-group">
              <label>向量检索权重: {{ vectorWeight }}</label>
              <input 
                v-model.number="vectorWeight" 
                type="range" 
                min="0" 
                max="1" 
                step="0.1" 
                class="form-range"
              />
            </div>
            <div class="form-group">
              <label>FTS 权重: {{ ftsWeight }}</label>
              <input 
                v-model.number="ftsWeight" 
                type="range" 
                min="0" 
                max="1" 
                step="0.1" 
                class="form-range"
              />
            </div>
          </div>
          
          <div class="form-group">
            <label>最低相似度阈值: {{ minScore }}</label>
            <input 
              v-model.number="minScore" 
              type="range" 
              min="0" 
              max="1" 
              step="0.05" 
              class="form-range"
            />
          </div>
        </template>
      </section>

      <section class="settings-section">
        <h2>Agent 配置</h2>
        <div class="form-group">
          <label>
            系统提示词
            <button @click="resetToDefault" class="btn btn-link">重置默认</button>
          </label>
          <textarea 
            v-model="systemPrompt" 
            class="form-control form-textarea" 
            rows="4"
            placeholder="系统提示词"
          />
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.settings-page {
  max-width: 800px;
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

.header-actions {
  display: flex;
  gap: 0.5rem;
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

.settings-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.settings-section {
  background: hsl(var(--card));
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius-lg);
  padding: 1.5rem;
}

.settings-section h2 {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 1rem 0;
  color: hsl(var(--muted-foreground));
}

.form-group {
  margin-bottom: 1rem;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.875rem;
  font-weight: 500;
  margin-bottom: 0.5rem;
  color: hsl(var(--foreground));
}

.form-control {
  width: 100%;
  padding: 0.5rem 0.75rem;
  background: hsl(var(--background));
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius);
  font-size: 0.875rem;
  color: hsl(var(--foreground));
  transition: border-color 0.2s;
}

.form-control:focus {
  outline: none;
  border-color: hsl(var(--primary));
  box-shadow: 0 0 0 2px hsl(var(--primary) / 0.2);
}

.form-textarea {
  resize: vertical;
  min-height: 100px;
}

.form-range {
  width: 100%;
  height: 6px;
  background: hsl(var(--muted));
  border-radius: 3px;
  appearance: none;
  cursor: pointer;
}

.form-range::-webkit-slider-thumb {
  appearance: none;
  width: 16px;
  height: 16px;
  background: hsl(var(--primary));
  border-radius: 50%;
  cursor: pointer;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.input-group {
  display: flex;
  gap: 0.5rem;
}

.input-group .form-control {
  flex: 1;
}

.checkbox-label {
  display: flex !important;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.checkbox-label input {
  width: 16px;
  height: 16px;
  cursor: pointer;
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

.btn-primary {
  background: hsl(var(--primary));
  color: hsl(var(--primary-foreground));
}

.btn-primary:hover:not(:disabled) {
  background: hsl(var(--primary) / 0.9);
}

.btn-secondary {
  background: hsl(var(--secondary));
  color: hsl(var(--secondary-foreground));
  border-color: hsl(var(--border));
}

.btn-secondary:hover:not(:disabled) {
  background: hsl(var(--accent));
}

.btn-icon {
  padding: 0.5rem;
  background: hsl(var(--muted));
  border: 1px solid hsl(var(--border));
  font-size: 0.75rem;
  white-space: nowrap;
}

.btn-link {
  background: none;
  border: none;
  color: hsl(var(--primary));
  padding: 0;
  font-size: 0.75rem;
  cursor: pointer;
}

.btn-link:hover {
  text-decoration: underline;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>
