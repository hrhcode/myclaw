<script setup lang="ts">
/**
 * Channels 通道管理页面
 * 显示和管理所有通道，支持配置功能
 */
import { ref, onMounted, onUnmounted } from 'vue'
import { channelApi, type ChannelStatus } from '@/api/gateway'
import { channelConfigApi } from '@/api/settings'
import { get } from '@/utils/request'
import { Card, Button, Badge, Modal, Input, Toggle, Skeleton } from '@/components/ui'
import { useToast } from '@/composables/useToast'
import type { AppConfig } from '@/api/settings'

const toast = useToast()

const channels = ref<Record<string, ChannelStatus>>({})
const config = ref<AppConfig | null>(null)
const loading = ref(false)
const configLoading = ref(false)
const error = ref<string | null>(null)
const showQQModal = ref(false)
const showWechatModal = ref(false)
const saving = ref(false)

const qqConfig = ref({
  enabled: false,
  api_url: 'http://localhost:6099',
  access_token: '',
})

const wechatConfig = ref({
  enabled: false,
  corp_id: '',
  agent_id: '',
  secret: '',
  token: '',
  encoding_aes_key: '',
})

let refreshInterval: number | null = null

onMounted(async () => {
  await Promise.all([loadChannels(), loadConfig()])
  refreshInterval = window.setInterval(loadChannels, 10000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})

async function loadChannels() {
  loading.value = true
  try {
    const result = await channelApi.list()
    channels.value = Object.fromEntries(
      result.channels.map((ch) => [ch.name, ch.status])
    )
    error.value = null
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

async function loadConfig() {
  configLoading.value = true
  try {
    config.value = await get('/api/config')
    
    qqConfig.value = {
      enabled: config.value.channels.qq.enabled,
      api_url: config.value.channels.qq.api_url,
      access_token: config.value.channels.qq.access_token,
    }
    
    wechatConfig.value = {
      enabled: config.value.channels.wechat.enabled,
      corp_id: config.value.channels.wechat.corp_id,
      agent_id: config.value.channels.wechat.agent_id,
      secret: config.value.channels.wechat.secret,
      token: config.value.channels.wechat.token,
      encoding_aes_key: config.value.channels.wechat.encoding_aes_key,
    }
  } catch (e) {
    console.error('加载配置失败:', e)
  } finally {
    configLoading.value = false
  }
}

async function startChannel(name: string) {
  try {
    await channelApi.start(name)
    toast.success(`通道 ${name} 已启动`)
    await loadChannels()
  } catch (e) {
    toast.error('启动失败')
  }
}

async function stopChannel(name: string) {
  try {
    await channelApi.stop(name)
    toast.success(`通道 ${name} 已停止`)
    await loadChannels()
  } catch (e) {
    toast.error('停止失败')
  }
}

async function saveQQConfig() {
  saving.value = true
  try {
    await channelConfigApi.update('qq', qqConfig.value)
    toast.success('QQ 通道配置已保存')
    showQQModal.value = false
    await loadConfig()
  } catch (e) {
    toast.error('保存配置失败')
  } finally {
    saving.value = false
  }
}

async function saveWechatConfig() {
  saving.value = true
  try {
    await channelConfigApi.update('wechat', wechatConfig.value)
    toast.success('微信通道配置已保存')
    showWechatModal.value = false
    await loadConfig()
  } catch (e) {
    toast.error('保存配置失败')
  } finally {
    saving.value = false
  }
}

function getChannelIcon(name: string): string {
  const icons: Record<string, string> = {
    web: 'M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9',
    qq: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z',
    wechat: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z',
  }
  return icons[name] || icons.web
}

function getChannelTitle(name: string): string {
  const titles: Record<string, string> = {
    web: 'Web',
    qq: 'QQ',
    wechat: '企业微信',
  }
  return titles[name] || name
}

function getChannelDescription(name: string): string {
  const descriptions: Record<string, string> = {
    web: 'Web 端聊天接口，支持 REST API 和 SSE 流式输出',
    qq: 'QQ 机器人通道，基于 NapCat 实现',
    wechat: '企业微信机器人通道',
  }
  return descriptions[name] || '消息通道'
}
</script>

<template>
  <div class="channels-page page-container">
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">通道管理</h1>
        <p class="page-subtitle">管理和配置消息通道</p>
      </div>
      <Button variant="secondary" size="sm" icon :loading="loading" @click="loadChannels" title="刷新">
        <svg class="icon" :class="{ spinning: loading }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      </Button>
    </div>

    <div v-if="error" class="error-alert">
      <div class="error-icon">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>
      <div class="error-content">
        <h4>加载失败</h4>
        <p>{{ error }}</p>
      </div>
    </div>

    <div v-if="loading && Object.keys(channels).length === 0" class="loading-skeleton">
      <div v-for="i in 3" :key="i" class="skeleton-card">
        <div class="skeleton-header">
          <Skeleton width="48px" height="48px" radius="var(--radius)" />
          <div class="skeleton-info">
            <Skeleton width="80px" height="1.25rem" />
            <Skeleton width="200px" height="0.875rem" />
          </div>
        </div>
        <div class="skeleton-stats">
          <Skeleton width="100%" height="2rem" />
        </div>
        <div class="skeleton-actions">
          <Skeleton width="60px" height="2rem" />
          <Skeleton width="60px" height="2rem" />
        </div>
      </div>
    </div>

    <div v-else class="channels-grid">
      <Card class="channel-card">
        <div class="channel-header">
          <div class="channel-icon icon-box icon-box-primary">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="getChannelIcon('web')" />
            </svg>
          </div>
          <div class="channel-info">
            <h3 class="channel-title">{{ getChannelTitle('web') }}</h3>
            <p class="channel-desc">{{ getChannelDescription('web') }}</p>
          </div>
          <Badge :variant="channels.web?.running ? 'success' : 'default'" size="md">
            {{ channels.web?.running ? '运行中' : '已停止' }}
          </Badge>
        </div>
        
        <div class="channel-stats">
          <div class="stat-item">
            <span class="stat-label">连接状态</span>
            <Badge :variant="channels.web?.connected ? 'success' : 'default'" size="sm">
              {{ channels.web?.connected ? '已连接' : '未连接' }}
            </Badge>
          </div>
          <div class="stat-item">
            <span class="stat-label">API 端点</span>
            <code class="stat-value">/v1/chat/completions</code>
          </div>
        </div>
        
        <div class="channel-actions">
          <Button 
            v-if="channels.web?.running"
            variant="danger"
            size="sm"
            @click="stopChannel('web')"
          >
            停止
          </Button>
          <Button 
            v-else
            variant="primary"
            size="sm"
            @click="startChannel('web')"
          >
            启动
          </Button>
        </div>
      </Card>

      <Card class="channel-card">
        <div class="channel-header">
          <div class="channel-icon icon-box" style="background: hsl(200 100% 47% / 0.1); color: hsl(200 100% 47%);">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="getChannelIcon('qq')" />
            </svg>
          </div>
          <div class="channel-info">
            <h3 class="channel-title">{{ getChannelTitle('qq') }}</h3>
            <p class="channel-desc">{{ getChannelDescription('qq') }}</p>
          </div>
          <Badge :variant="channels.qq?.running ? 'success' : 'default'" size="md">
            {{ channels.qq?.running ? '运行中' : '已停止' }}
          </Badge>
        </div>
        
        <div class="channel-stats">
          <div class="stat-item">
            <span class="stat-label">启用状态</span>
            <Badge :variant="qqConfig.enabled ? 'success' : 'default'" size="sm">
              {{ qqConfig.enabled ? '已启用' : '未启用' }}
            </Badge>
          </div>
          <div class="stat-item">
            <span class="stat-label">API 地址</span>
            <code class="stat-value">{{ qqConfig.api_url || '-' }}</code>
          </div>
        </div>
        
        <div class="channel-actions">
          <Button variant="secondary" size="sm" @click="showQQModal = true">
            配置
          </Button>
          <Button 
            v-if="channels.qq?.running"
            variant="danger"
            size="sm"
            @click="stopChannel('qq')"
          >
            停止
          </Button>
          <Button 
            v-else-if="qqConfig.enabled"
            variant="primary"
            size="sm"
            @click="startChannel('qq')"
          >
            启动
          </Button>
        </div>
      </Card>

      <Card class="channel-card">
        <div class="channel-header">
          <div class="channel-icon icon-box icon-box-success">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="getChannelIcon('wechat')" />
            </svg>
          </div>
          <div class="channel-info">
            <h3 class="channel-title">{{ getChannelTitle('wechat') }}</h3>
            <p class="channel-desc">{{ getChannelDescription('wechat') }}</p>
          </div>
          <Badge :variant="channels.wechat?.running ? 'success' : 'default'" size="md">
            {{ channels.wechat?.running ? '运行中' : '已停止' }}
          </Badge>
        </div>
        
        <div class="channel-stats">
          <div class="stat-item">
            <span class="stat-label">启用状态</span>
            <Badge :variant="wechatConfig.enabled ? 'success' : 'default'" size="sm">
              {{ wechatConfig.enabled ? '已启用' : '未启用' }}
            </Badge>
          </div>
          <div class="stat-item">
            <span class="stat-label">企业ID</span>
            <code class="stat-value">{{ wechatConfig.corp_id || '-' }}</code>
          </div>
        </div>
        
        <div class="channel-actions">
          <Button variant="secondary" size="sm" @click="showWechatModal = true">
            配置
          </Button>
          <Button 
            v-if="channels.wechat?.running"
            variant="danger"
            size="sm"
            @click="stopChannel('wechat')"
          >
            停止
          </Button>
          <Button 
            v-else-if="wechatConfig.enabled"
            variant="primary"
            size="sm"
            @click="startChannel('wechat')"
          >
            启动
          </Button>
        </div>
      </Card>
    </div>

    <Modal v-model="showQQModal" title="QQ 通道配置" size="md">
      <div class="config-form">
        <div class="form-group">
          <label class="form-label">启用通道</label>
          <Toggle v-model="qqConfig.enabled" />
        </div>
        
        <div class="form-group">
          <label class="form-label">NapCat API 地址</label>
          <Input v-model="qqConfig.api_url" placeholder="http://localhost:6099" />
          <p class="form-hint">NapCat 或 go-cqhttp 的 HTTP API 地址</p>
        </div>
        
        <div class="form-group">
          <label class="form-label">Access Token</label>
          <Input v-model="qqConfig.access_token" type="password" placeholder="访问令牌" />
          <p class="form-hint">API 访问令牌（可选）</p>
        </div>
      </div>
      
      <template #footer>
        <Button variant="secondary" @click="showQQModal = false">取消</Button>
        <Button variant="primary" :loading="saving" @click="saveQQConfig">保存</Button>
      </template>
    </Modal>

    <Modal v-model="showWechatModal" title="企业微信通道配置" size="md">
      <div class="config-form">
        <div class="form-group">
          <label class="form-label">启用通道</label>
          <Toggle v-model="wechatConfig.enabled" />
        </div>
        
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">企业ID</label>
            <Input v-model="wechatConfig.corp_id" placeholder="CorpID" />
          </div>
          <div class="form-group">
            <label class="form-label">AgentId</label>
            <Input v-model="wechatConfig.agent_id" placeholder="应用ID" />
          </div>
        </div>
        
        <div class="form-group">
          <label class="form-label">应用 Secret</label>
          <Input v-model="wechatConfig.secret" type="password" placeholder="应用密钥" />
        </div>
        
        <div class="form-group">
          <label class="form-label">Token</label>
          <Input v-model="wechatConfig.token" placeholder="回调 Token" />
          <p class="form-hint">企业微信回调配置中的 Token</p>
        </div>
        
        <div class="form-group">
          <label class="form-label">EncodingAESKey</label>
          <Input v-model="wechatConfig.encoding_aes_key" placeholder="消息加密密钥" />
          <p class="form-hint">企业微信回调配置中的 EncodingAESKey</p>
        </div>
      </div>
      
      <template #footer>
        <Button variant="secondary" @click="showWechatModal = false">取消</Button>
        <Button variant="primary" :loading="saving" @click="saveWechatConfig">保存</Button>
      </template>
    </Modal>
  </div>
</template>

<style scoped>
.channels-page {
  width: 100%;
}

.error-alert {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1rem 1.25rem;
  background: linear-gradient(135deg, hsl(var(--destructive) / 0.1) 0%, hsl(var(--destructive) / 0.05) 100%);
  border: 1px solid hsl(var(--destructive) / 0.3);
  border-radius: var(--radius-lg);
  margin-bottom: 1rem;
}

.error-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: hsl(var(--destructive) / 0.1);
  border-radius: var(--radius);
  flex-shrink: 0;
}

.error-icon svg {
  width: 20px;
  height: 20px;
  color: hsl(var(--destructive));
}

.error-content h4 {
  font-size: 0.875rem;
  font-weight: 600;
  margin: 0 0 0.25rem 0;
  color: hsl(var(--destructive));
}

.error-content p {
  font-size: 0.8125rem;
  margin: 0;
  color: hsl(var(--muted-foreground));
}

.loading-skeleton {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 1.5rem;
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

.skeleton-stats {
  margin-bottom: 1rem;
}

.skeleton-actions {
  display: flex;
  gap: 0.5rem;
}

.channels-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: 1.5rem;
}

.channel-card {
  display: flex;
  flex-direction: column;
  padding: 0;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.channel-card:hover {
  transform: translateY(-2px);
  border-color: hsl(var(--primary) / 0.2);
}

.channel-header {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1.5rem;
}

.channel-icon {
  width: 48px;
  height: 48px;
  flex-shrink: 0;
}

.channel-icon svg {
  width: 24px;
  height: 24px;
}

.channel-info {
  flex: 1;
  min-width: 0;
}

.channel-title {
  font-size: 1.0625rem;
  font-weight: 600;
  margin: 0 0 0.375rem 0;
}

.channel-desc {
  font-size: 0.8125rem;
  color: hsl(var(--muted-foreground));
  margin: 0;
  line-height: 1.4;
}

.channel-stats {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  background: hsl(var(--muted) / 0.3);
  border-top: 1px solid hsl(var(--border));
  border-bottom: 1px solid hsl(var(--border));
}

.stat-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.stat-label {
  font-size: 0.8125rem;
  color: hsl(var(--muted-foreground));
  font-weight: 500;
}

.stat-value {
  font-size: 0.75rem;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  background: hsl(var(--muted));
  padding: 0.25rem 0.625rem;
  border-radius: var(--radius);
}

.channel-actions {
  display: flex;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
}

.config-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
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

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
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
  .channels-grid {
    grid-template-columns: 1fr;
  }
  
  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>
