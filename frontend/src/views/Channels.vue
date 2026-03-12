<script setup lang="ts">
/**
 * Channels 通道管理页面
 * 显示和管理所有通道，支持配置功能
 * 使用科技感组件优化视觉效果
 */
import { ref, onMounted, onUnmounted } from 'vue'
import { channelApi, type ChannelStatus } from '@/api/gateway'
import { channelConfigApi } from '@/api/settings'
import { get } from '@/utils/request'
import { Card, Button, Badge, Modal, Input, Toggle, Skeleton, GlowCard, AnimatedList, AnimatedListItem } from '@/components/ui'
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
const listVisible = ref(false)

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
  setTimeout(() => {
    listVisible.value = true
  }, 100)
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

function getChannelGlowColor(name: string): string {
  const colors: Record<string, string> = {
    web: 'rgba(59, 130, 246, 0.4)',
    qq: 'rgba(0, 170, 255, 0.4)',
    wechat: 'rgba(16, 185, 129, 0.4)',
  }
  return colors[name] || 'rgba(59, 130, 246, 0.4)'
}

const channelList = ['web', 'qq', 'wechat']
</script>

<template>
  <div class="channels-page page-container">
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          <span class="title-text">通道管理</span>
          <span class="title-glow" />
        </h1>
        <p class="page-subtitle">管理和配置消息通道</p>
      </div>
      <Button variant="secondary" :loading="loading" @click="loadChannels">
        <svg class="icon" :class="{ spinning: loading }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        刷新
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

    <AnimatedList v-else class="channels-grid" :visible="listVisible" :stagger="100">
      <AnimatedListItem v-for="(name, index) in channelList" :key="name" :index="index" :visible="listVisible">
        <GlowCard class="channel-card" :glow-color="getChannelGlowColor(name)">
          <div class="channel-header">
            <div class="channel-icon" :class="`icon-${name}`">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="getChannelIcon(name)" />
              </svg>
            </div>
            <div class="channel-info">
              <h3 class="channel-title">{{ getChannelTitle(name) }}</h3>
              <p class="channel-desc">{{ getChannelDescription(name) }}</p>
            </div>
            <div class="channel-status-badge">
              <Badge :variant="channels[name]?.running ? 'success' : 'default'" size="md">
                {{ channels[name]?.running ? '运行中' : '已停止' }}
              </Badge>
            </div>
          </div>
          
          <div class="channel-stats">
            <div class="stat-item">
              <span class="stat-label">{{ name === 'web' ? '连接状态' : '启用状态' }}</span>
              <Badge 
                :variant="(name === 'web' ? channels[name]?.connected : (name === 'qq' ? qqConfig.enabled : wechatConfig.enabled)) ? 'success' : 'default'" 
                size="sm"
              >
                {{ (name === 'web' ? channels[name]?.connected : (name === 'qq' ? qqConfig.enabled : wechatConfig.enabled)) ? (name === 'web' ? '已连接' : '已启用') : (name === 'web' ? '未连接' : '未启用') }}
              </Badge>
            </div>
            <div class="stat-item">
              <span class="stat-label">{{ name === 'web' ? 'API 端点' : (name === 'qq' ? 'API 地址' : '企业ID') }}</span>
              <code class="stat-value">{{ name === 'web' ? '/v1/chat/completions' : (name === 'qq' ? (qqConfig.api_url || '-') : (wechatConfig.corp_id || '-')) }}</code>
            </div>
          </div>
          
          <div class="channel-actions">
            <Button 
              v-if="name !== 'web'"
              variant="secondary" 
              size="sm" 
              @click="name === 'qq' ? (showQQModal = true) : (showWechatModal = true)"
            >
              配置
            </Button>
            <Button 
              v-if="channels[name]?.running"
              variant="danger"
              size="sm"
              @click="stopChannel(name)"
            >
              停止
            </Button>
            <Button 
              v-else-if="name === 'web' || (name === 'qq' ? qqConfig.enabled : wechatConfig.enabled)"
              variant="primary"
              size="sm"
              @click="startChannel(name)"
            >
              启动
            </Button>
          </div>
        </GlowCard>
      </AnimatedListItem>
    </AnimatedList>

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

.page-title {
  position: relative;
  display: inline-block;
}

.title-text {
  background: linear-gradient(135deg, hsl(var(--foreground)) 0%, hsl(var(--foreground) / 0.7) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.title-glow {
  position: absolute;
  inset: -10px -20px;
  background: radial-gradient(ellipse at center, hsl(var(--primary) / 0.1) 0%, transparent 70%);
  pointer-events: none;
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
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius);
  flex-shrink: 0;
}

.channel-icon svg {
  width: 24px;
  height: 24px;
}

.icon-web {
  background: hsl(var(--primary) / 0.1);
  color: hsl(var(--primary));
}

.icon-qq {
  background: hsl(200 100% 47% / 0.1);
  color: hsl(200 100% 47%);
}

.icon-wechat {
  background: hsl(var(--chart-2) / 0.1);
  color: hsl(var(--chart-2));
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

.channel-status-badge {
  flex-shrink: 0;
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
