<script setup lang="ts">
/**
 * Channels 通道管理页面
 * 显示和管理所有通道，支持配置功能
 */
import { ref, onMounted, computed } from 'vue'
import { channelApi, type ChannelStatus } from '@/api/gateway'
import { channelConfigApi } from '@/api/settings'
import type { AppConfig } from '@/api/settings'
import { get } from '@/utils/request'

const channels = ref<Record<string, ChannelStatus>>({})
const config = ref<AppConfig | null>(null)
const loading = ref(false)
const configLoading = ref(false)
const error = ref<string | null>(null)
const message = ref<{ type: 'success' | 'error'; text: string } | null>(null)
const editingChannel = ref<string | null>(null)

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

onMounted(async () => {
  await Promise.all([loadChannels(), loadConfig()])
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
    showMessage('success', `通道 ${name} 已启动`)
    await loadChannels()
  } catch (e) {
    showMessage('error', '启动失败')
  }
}

async function stopChannel(name: string) {
  try {
    await channelApi.stop(name)
    showMessage('success', `通道 ${name} 已停止`)
    await loadChannels()
  } catch (e) {
    showMessage('error', '停止失败')
  }
}

async function saveQQConfig() {
  try {
    await channelConfigApi.update('qq', qqConfig.value)
    showMessage('success', 'QQ 通道配置已保存')
    editingChannel.value = null
    await loadConfig()
  } catch (e) {
    showMessage('error', '保存配置失败')
  }
}

async function saveWechatConfig() {
  try {
    await channelConfigApi.update('wechat', wechatConfig.value)
    showMessage('success', '微信通道配置已保存')
    editingChannel.value = null
    await loadConfig()
  } catch (e) {
    showMessage('error', '保存配置失败')
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

function getChannelDescription(name: string): string {
  const descriptions: Record<string, string> = {
    web: 'Web 端聊天接口，支持 REST API 和 SSE 流式输出',
    qq: 'QQ 机器人通道，基于 NapCat 实现',
    wechat: '企业微信机器人通道',
  }
  return descriptions[name] || '消息通道'
}

function showMessage(type: 'success' | 'error', text: string) {
  message.value = { type, text }
  setTimeout(() => {
    message.value = null
  }, 3000)
}
</script>

<template>
  <div class="channels-page">
    <div class="page-header">
      <h1>通道管理</h1>
      <button @click="loadChannels" class="btn btn-secondary" :disabled="loading">
        <svg class="icon" :class="{ spinning: loading }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        刷新
      </button>
    </div>

    <div v-if="message" class="message" :class="message.type">
      {{ message.text }}
    </div>

    <div v-if="error" class="error-message">
      {{ error }}
    </div>

    <div class="channels-grid">
      <!-- Web 通道 -->
      <div class="channel-card">
        <div class="channel-header">
          <div class="channel-icon">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="getChannelIcon('web')" />
            </svg>
          </div>
          <div class="channel-info">
            <h3>Web</h3>
            <p>{{ getChannelDescription('web') }}</p>
          </div>
          <div class="channel-status" :class="{ running: channels.web?.running }">
            <span class="status-dot"></span>
            <span>{{ channels.web?.running ? '运行中' : '已停止' }}</span>
          </div>
        </div>
        <div class="channel-meta">
          <span :class="{ active: channels.web?.connected }">
            {{ channels.web?.connected ? '已连接' : '未连接' }}
          </span>
        </div>
        <div class="channel-actions">
          <button 
            v-if="channels.web?.running"
            @click="stopChannel('web')"
            class="btn btn-danger"
          >
            停止
          </button>
          <button 
            v-else
            @click="startChannel('web')"
            class="btn btn-primary"
          >
            启动
          </button>
        </div>
      </div>

      <!-- QQ 通道 -->
      <div class="channel-card">
        <div class="channel-header">
          <div class="channel-icon">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="getChannelIcon('qq')" />
            </svg>
          </div>
          <div class="channel-info">
            <h3>QQ</h3>
            <p>{{ getChannelDescription('qq') }}</p>
          </div>
          <div class="channel-status" :class="{ running: channels.qq?.running }">
            <span class="status-dot"></span>
            <span>{{ channels.qq?.running ? '运行中' : '已停止' }}</span>
          </div>
        </div>
        
        <div v-if="editingChannel === 'qq'" class="channel-config">
          <div class="form-group">
            <label>启用</label>
            <label class="toggle">
              <input type="checkbox" v-model="qqConfig.enabled" />
              <span class="toggle-slider"></span>
            </label>
          </div>
          <div class="form-group">
            <label>API 地址</label>
            <input v-model="qqConfig.api_url" type="text" class="form-control" placeholder="http://localhost:6099" />
          </div>
          <div class="form-group">
            <label>Access Token</label>
            <input v-model="qqConfig.access_token" type="password" class="form-control" placeholder="访问令牌" />
          </div>
          <div class="config-actions">
            <button @click="editingChannel = null" class="btn btn-secondary">取消</button>
            <button @click="saveQQConfig" class="btn btn-primary">保存</button>
          </div>
        </div>
        
        <template v-else>
          <div class="channel-meta">
            <span :class="{ active: qqConfig.enabled }">
              {{ qqConfig.enabled ? '已启用' : '未启用' }}
            </span>
            <span v-if="qqConfig.api_url" class="muted">{{ qqConfig.api_url }}</span>
          </div>
          <div class="channel-actions">
            <button @click="editingChannel = 'qq'" class="btn btn-secondary">配置</button>
            <button 
              v-if="channels.qq?.running"
              @click="stopChannel('qq')"
              class="btn btn-danger"
            >
              停止
            </button>
            <button 
              v-else-if="qqConfig.enabled"
              @click="startChannel('qq')"
              class="btn btn-primary"
            >
              启动
            </button>
          </div>
        </template>
      </div>

      <!-- 微信通道 -->
      <div class="channel-card">
        <div class="channel-header">
          <div class="channel-icon">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="getChannelIcon('wechat')" />
            </svg>
          </div>
          <div class="channel-info">
            <h3>企业微信</h3>
            <p>{{ getChannelDescription('wechat') }}</p>
          </div>
          <div class="channel-status" :class="{ running: channels.wechat?.running }">
            <span class="status-dot"></span>
            <span>{{ channels.wechat?.running ? '运行中' : '已停止' }}</span>
          </div>
        </div>
        
        <div v-if="editingChannel === 'wechat'" class="channel-config">
          <div class="form-group">
            <label>启用</label>
            <label class="toggle">
              <input type="checkbox" v-model="wechatConfig.enabled" />
              <span class="toggle-slider"></span>
            </label>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>企业ID</label>
              <input v-model="wechatConfig.corp_id" type="text" class="form-control" />
            </div>
            <div class="form-group">
              <label>AgentId</label>
              <input v-model="wechatConfig.agent_id" type="text" class="form-control" />
            </div>
          </div>
          <div class="form-group">
            <label>Secret</label>
            <input v-model="wechatConfig.secret" type="password" class="form-control" />
          </div>
          <div class="form-group">
            <label>Token</label>
            <input v-model="wechatConfig.token" type="text" class="form-control" />
          </div>
          <div class="form-group">
            <label>EncodingAESKey</label>
            <input v-model="wechatConfig.encoding_aes_key" type="text" class="form-control" />
          </div>
          <div class="config-actions">
            <button @click="editingChannel = null" class="btn btn-secondary">取消</button>
            <button @click="saveWechatConfig" class="btn btn-primary">保存</button>
          </div>
        </div>
        
        <template v-else>
          <div class="channel-meta">
            <span :class="{ active: wechatConfig.enabled }">
              {{ wechatConfig.enabled ? '已启用' : '未启用' }}
            </span>
            <span v-if="wechatConfig.corp_id" class="muted">{{ wechatConfig.corp_id }}</span>
          </div>
          <div class="channel-actions">
            <button @click="editingChannel = 'wechat'" class="btn btn-secondary">配置</button>
            <button 
              v-if="channels.wechat?.running"
              @click="stopChannel('wechat')"
              class="btn btn-danger"
            >
              停止
            </button>
            <button 
              v-else-if="wechatConfig.enabled"
              @click="startChannel('wechat')"
              class="btn btn-primary"
            >
              启动
            </button>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.channels-page {
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

.error-message {
  padding: 1rem;
  background: hsl(var(--destructive) / 0.1);
  border: 1px solid hsl(var(--destructive));
  border-radius: var(--radius);
  color: hsl(var(--destructive));
  margin-bottom: 1rem;
}

.channels-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 1.5rem;
}

.channel-card {
  background: hsl(var(--card));
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius-lg);
  padding: 1.25rem;
}

.channel-header {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1rem;
}

.channel-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: hsl(var(--muted) / 0.5);
  border-radius: var(--radius);
  flex-shrink: 0;
}

.channel-icon svg {
  width: 24px;
  height: 24px;
  color: hsl(var(--primary));
}

.channel-info {
  flex: 1;
  min-width: 0;
}

.channel-info h3 {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 0.25rem 0;
}

.channel-info p {
  font-size: 0.75rem;
  color: hsl(var(--muted-foreground));
  margin: 0;
}

.channel-status {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.75rem;
  color: hsl(var(--muted-foreground));
}

.channel-status.running {
  color: hsl(var(--chart-2));
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: hsl(var(--destructive));
}

.channel-status.running .status-dot {
  background: hsl(var(--chart-2));
}

.channel-meta {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1rem;
  font-size: 0.75rem;
  color: hsl(var(--muted-foreground));
}

.channel-meta .active {
  color: hsl(var(--chart-2));
}

.channel-meta .muted {
  opacity: 0.6;
}

.channel-actions {
  display: flex;
  gap: 0.5rem;
}

.channel-config {
  border-top: 1px solid hsl(var(--border));
  padding-top: 1rem;
  margin-top: 0.5rem;
}

.form-group {
  margin-bottom: 0.75rem;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group label {
  display: block;
  font-size: 0.75rem;
  font-weight: 500;
  margin-bottom: 0.25rem;
  color: hsl(var(--muted-foreground));
}

.form-control {
  width: 100%;
  padding: 0.5rem 0.75rem;
  background: hsl(var(--background));
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius);
  font-size: 0.875rem;
  color: hsl(var(--foreground));
}

.form-control:focus {
  outline: none;
  border-color: hsl(var(--primary));
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}

.config-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  margin-top: 1rem;
}

.toggle {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
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

.btn-danger {
  background: hsl(var(--destructive));
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background: hsl(var(--destructive) / 0.9);
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

@media (max-width: 768px) {
  .channels-grid {
    grid-template-columns: 1fr;
  }
  
  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>
