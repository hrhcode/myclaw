# MyClaw

MyClaw 是一个面向个人使用的精简 Agent 平台，主入口是 React + FastAPI 的 Web 应用。当前版本已经从“单机会话聊天应用”升级为“带工作会话、自动化、记忆和会话协作能力的个人 Agent 控制台”。

## 当前状态

- 后端已补齐核心个人版能力：
  - `Session Runtime`：按工作会话隔离模型、工作区、工具配置和上下文摘要
  - `Workspace + Skills`：支持本地工作区、技能发现、启停和提示注入
  - `Session Tools`：支持跨会话查询历史、状态和任务派发
  - `Automation`：支持固定间隔、每日、每周调度的个人自动化任务
  - `Memory`：支持长期记忆、会话级记忆策略和自动提炼
- 后端 API 已完成本地回归联调。
- 后端测试已补齐 `session / automation / memory / tool executor` 相关覆盖。
- 前端已打通会话、自动化、记忆的闭环页面。
- 前端核心导航和主页面文案已统一为中文。

## 核心能力

### 1. 聊天与 Agent 运行

- 流式聊天响应
- 每条回复保留运行轨迹和工具调用事件
- 支持聊天命令：
  - `/new`
  - `/reset`
  - `/compact`
  - `/status`

### 2. 工作会话

- 创建、切换、重命名、删除工作会话
- 设置默认工作会话
- 每个工作会话独立维护：
  - `workspace_path`
  - `model / provider`
  - `tool_profile`
  - `tool_allow / tool_deny`
  - `max_iterations`
  - `context_summary`
  - `memory_auto_extract / memory_threshold`

### 3. Skills 与提示注入

- 自动发现本地 skills
- 为不同工作会话独立启停 skills
- 注入工作区提示和会话摘要
- 支持项目级提示文件：
  - `AGENTS.md`
  - `TOOLS.md`

### 4. 跨会话协作

- `sessions_list`
- `sessions_history`
- `sessions_send`
- `session_status`

支持从一个工作会话向另一个工作会话派发任务，并触发一次新的 Agent 运行。

### 5. 自动化

- 创建、编辑、启停、删除自动化任务
- 支持两类调度：
  - 固定间隔
  - 每日 / 每周固定时间
- 自动化结果会写入：
  - 对应工作会话历史
  - automation run 记录

### 6. 长期记忆

- 长期记忆列表、搜索、筛选、排序
- 支持区分来源：
  - 手动创建
  - 会话摘要
  - 自动提炼
- 支持记忆检索参数配置：
  - top-k
  - 最低相关度
  - 混合检索权重
  - MMR 重排
  - 时间衰减

## 技术栈

- 前端：React 19、TypeScript、Vite、Tailwind CSS、Framer Motion
- 后端：FastAPI、SQLAlchemy、Pydantic
- 数据库：SQLite
- 模型接入：当前以现有 LLM 配置体系为主

## 项目结构

```text
myclaw/
├─ frontend/
│  ├─ src/
│  │  ├─ components/
│  │  │  ├─ chat/             # 聊天页
│  │  │  ├─ conversations/    # 聊天记录页
│  │  │  ├─ sessions/         # 工作会话页
│  │  │  ├─ automations/      # 自动化页
│  │  │  ├─ memory/           # 记忆页
│  │  │  ├─ settings/         # 设置页
│  │  │  ├─ tools/            # 工具页
│  │  │  └─ layout/           # 布局组件
│  │  ├─ contexts/
│  │  ├─ services/
│  │  └─ types/
│  └─ package.json
├─ backend/
│  ├─ app/
│  │  ├─ agent_loop/
│  │  ├─ api/
│  │  ├─ core/
│  │  ├─ dao/
│  │  ├─ models/
│  │  ├─ schemas/
│  │  ├─ services/
│  │  └─ tools/
│  ├─ tests/
│  └─ requirements.txt
├─ start_all.ps1
└─ README.md
```

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- 一个可用的模型 API Key

### 1. 安装后端依赖

```powershell
cd backend
pip install -r requirements.txt
```

### 2. 安装前端依赖

```powershell
cd frontend
npm install
```

### 3. 启动服务

方式 A：一键启动

```powershell
.\start_all.ps1
```

方式 B：分别启动

```powershell
# 终端 1
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

```powershell
# 终端 2
cd frontend
npm run dev
```

启动后访问：

- 前端：[http://localhost:5173](http://localhost:5173)
- 后端 OpenAPI：[http://localhost:8000/docs](http://localhost:8000/docs)

## 主要 API

### 聊天

- `POST /api/chat/stream`

### 工作会话

- `GET /api/sessions`
- `POST /api/sessions`
- `PUT /api/sessions/{id}`
- `DELETE /api/sessions/{id}`
- `GET /api/sessions/{id}/status`
- `POST /api/sessions/{id}/dispatch`
- `GET /api/sessions/{id}/history-summary`

### Skills

- `GET /api/skills`
- `GET /api/sessions/{id}/skills`
- `PUT /api/sessions/{id}/skills`

### 自动化

- `GET /api/automations`
- `POST /api/automations`
- `PUT /api/automations/{id}`
- `DELETE /api/automations/{id}`
- `GET /api/automations/{id}/runs`

### 记忆

- `GET /api/memory/long-term`
- `POST /api/memory/long-term`
- `PUT /api/memory/long-term/{id}`
- `DELETE /api/memory/long-term/{id}`
- `POST /api/memory/search`

## 测试

后端测试可在 `backend` 目录运行：

```powershell
$env:PYTHONPATH='D:\Project\Me\myclaw-new\myclaw\backend'
python -m unittest discover -s tests -p "test_*.py"
```

当前已补充并通过的重点测试包括：

- `test_session_service.py`
- `test_automation_service.py`
- `test_memory_api.py`
- `test_tool_executor.py`
- `test_agent_loop_prompting.py`
- `test_time_tool.py`

前端构建验证：

```powershell
cd frontend
npm run build
```

## 当前已知边界

- 当前定位为个人单用户版本，不包含团队、多租户、多渠道接入
- 安全审批、沙箱隔离、提权控制暂未作为本阶段重点
- Canvas、语音、移动端节点、插件市场暂未纳入
- 历史聊天内容如果本身是英文，会按原始消息内容展示，不会被 UI 翻译

## 开发建议

- 优先通过工作会话隔离不同项目
- 对长期任务优先使用自动化而不是手动重复触发
- 对固定项目目录建议配置 `workspace_path` 和本地 skills

## License

MIT
