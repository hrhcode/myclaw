# MyClaw 前后端闭环清单

本文档用于说明当前前端页面分别承载什么功能、对应哪些后端接口，以及是否已经形成闭环。

## 当前产品模型

- 用户显性感知的隔离单位只有“会话”。
- 模型、技能、工作目录、记忆提炼、自动化基础归属等配置统一归入“全局配置”。
- 后端内部仍保留 `session_id` 作为底层承载容器，但不再作为前端一级产品概念暴露。

## 页面闭环

### 1. 对话页 `/chat`

- 前端功能：
  - 发送消息
  - 流式接收智能体回复
  - 展示推理、工具调用、工具结果、循环提醒
  - 新建会话
  - 刷新会话列表
- 主要前端文件：
  - `frontend/src/components/chat/ChatPage.tsx`
  - `frontend/src/components/chat/MessageList.tsx`
  - `frontend/src/components/chat/MessageInput.tsx`
- 对应后端接口：
  - `POST /api/chat/stream`
  - `GET /api/conversations`
  - `POST /api/conversations`
  - `GET /api/conversations/{id}/messages`
- 闭环状态：
  - 已闭环
- 备注：
  - 当前仍通过后端内部默认 session 承载运行上下文，但前端不再暴露工作会话概念。

### 2. 会话页 `/conversations`

- 前端功能：
  - 查看全部会话
  - 搜索会话
  - 查看消息数量和最后更新时间
  - 重命名会话
  - 删除会话
  - 跳转回对话页继续
- 主要前端文件：
  - `frontend/src/components/conversations/ConversationsPage.tsx`
- 对应后端接口：
  - `GET /api/conversations`
  - `GET /api/conversations/stats`
  - `PUT /api/conversations/{id}`
  - `DELETE /api/conversations/{id}`
- 闭环状态：
  - 已闭环

### 3. 记忆页 `/memory`

- 前端功能：
  - 调整记忆检索参数
  - 查看长期记忆
  - 新增、编辑、删除长期记忆
  - 查看记忆重要度、来源、归属范围
- 主要前端文件：
  - `frontend/src/components/memory/index.tsx`
  - `frontend/src/components/memory/ConfigTab.tsx`
  - `frontend/src/components/memory/LongTermMemoryTab.tsx`
- 对应后端接口：
  - `GET /api/config/{key}`
  - `PUT /api/config/{key}`
  - `GET /api/memory/long-term`
  - `POST /api/memory/long-term`
  - `PUT /api/memory/long-term/{id}`
  - `DELETE /api/memory/long-term/{id}`
- 闭环状态：
  - 已闭环
- 备注：
  - 长期记忆底层仍可能带 `session_id`，目前前端仅把它显示为“全局 / 隔离会话 N”，不再提供工作会话管理。

### 4. 自动化页 `/automations`

- 前端功能：
  - 创建自动化任务
  - 编辑调度方式、调度参数、提示词
  - 启用 / 停用自动化
  - 删除自动化
  - 查看最近执行记录
- 主要前端文件：
  - `frontend/src/components/automations/AutomationsPage.tsx`
- 对应后端接口：
  - `GET /api/automations`
  - `POST /api/automations`
  - `PUT /api/automations/{id}`
  - `DELETE /api/automations/{id}`
  - `GET /api/automations/{id}/runs`
- 闭环状态：
  - 已闭环
- 备注：
  - 自动化创建时前端不再要求选择工作会话，后端会自动落到默认全局 session。

### 5. 工具页 `/tools`

- 前端功能：
  - 查看可用工具列表
  - 查看工具描述和参数
  - 启用 / 禁用工具
- 主要前端文件：
  - `frontend/src/components/tools/ToolsPage.tsx`
- 对应后端接口：
  - `GET /api/tools`
  - `PUT /api/tools/{tool_name}/toggle`
- 闭环状态：
  - 已闭环
- 备注：
  - 当前工具页尚未接入 `GET /api/tools/config` 和 `PUT /api/tools/config`，因此“工具策略”仍主要在后端配置层，前端只支持单工具开关。

### 6. 设置页 `/settings`

- 前端功能：
  - 对话模型配置
  - 向量模型配置
  - 联网搜索配置
  - 浏览器自动化配置
  - 全局运行配置
  - 全局技能开关
- 主要前端文件：
  - `frontend/src/components/settings/SettingsPage.tsx`
  - `frontend/src/components/settings/WebSearchConfigPanel.tsx`
  - `frontend/src/components/settings/BrowserConfigPanel.tsx`
- 对应后端接口：
  - `GET /api/config/providers`
  - `GET /api/config/providers/{provider}/models`
  - `GET /api/config/embedding-providers`
  - `GET /api/config/embedding-providers/{provider}/models`
  - `GET /api/config/{key}`
  - `PUT /api/config/{key}`
  - `GET /api/config/web-search`
  - `PUT /api/config/web-search`
  - `GET /api/config/browser`
  - `PUT /api/config/browser`
  - `GET /api/config/runtime`
  - `PUT /api/config/runtime`
  - `GET /api/skills`
  - `GET /api/config/skills`
  - `PUT /api/config/skills`
- 闭环状态：
  - 已闭环
- 备注：
  - 这是当前“全局配置”的核心承载页，已经替代旧的工作会话配置页。

### 7. 日志页 `/logs/realtime` 与 `/logs/history`

- 前端功能：
  - 实时查看日志流
  - 过滤日志等级
  - 搜索日志内容
  - 查看历史日志
- 主要前端文件：
  - `frontend/src/components/logs/LogsPage.tsx`
  - `frontend/src/components/logs/HistoryLogsPage.tsx`
- 对应后端接口：
  - `WS /api/logs/stream`
  - `GET /api/logs/history`
  - 以及若干状态/统计/清理接口
- 闭环状态：
  - 基本闭环
- 备注：
  - 实时日志已闭环，历史日志功能依赖历史页实现细节，后续建议再做一次中文化和信息层级统一检查。

## 已完成的结构收口

- 已移除前端“工作会话”一级导航和页面。
- 已移除聊天页中的工作会话选择。
- 已将会话列表改为全局加载，不再按前端 session 过滤。
- 已将设置页迁移到全局配置接口。
- 已删除前端中已不再使用的工作会话组件与大部分 session API 封装。

## 仍建议继续优化的点

### 1. 日志相关页面继续统一风格

- 当前实时日志页已经收口，但历史日志页和部分日志子组件建议继续检查中文文案和视觉密度。

### 2. 工具页补齐“工具策略”配置

- 后端已有工具策略接口，但前端当前只支持工具开关。
- 建议后续把 `profile / allow / deny / max_iterations / timeout_seconds` 纳入工具页，而不是散落在后端配置。

### 3. 底层 session 继续内收

- 当前后端内部仍大量依赖 `session_id`。
- 这在现阶段是合理的技术折中，但要避免再次泄漏到前端产品模型。
