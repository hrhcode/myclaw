<p align="center">
  <img src="frontend/public/myclaw.svg" alt="MyClaw Logo" width="160">
</p>

<h1 align="center">MyClaw</h1>

<p align="center">
  <strong>个人 Agent 平台 — 基于 React + FastAPI + SQLite 构建</strong>
</p>

<p align="center">
  <a href="README.md">中文</a> | <a href="README_EN.md">English</a>
</p>

---

MyClaw 是一个面向个人使用的精简 Agent 平台，主入口是 React + FastAPI 的 Web 应用。当前版本已经从「单机会话聊天应用」升级为「带工作会话、自动化、记忆和会话协作能力的个人 Agent 控制台」。

## 当前状态

- 后端已补齐核心个人版能力
- 后端 API 已完成本地回归联调
- 后端测试已补齐 `session / automation / memory / tool executor` 相关覆盖
- 前端已打通会话、自动化、记忆的闭环页面
- 前端核心导航和主页面文案已统一为中文

## 核心能力

### 1. 聊天与 Agent 运行

- 流式聊天响应（SSE）
- 每条回复保留运行轨迹和工具调用事件
- 支持聊天命令：`/new` `/reset` `/compact` `/status`

### 2. 工作会话

- 创建、切换、重命名、删除工作会话
- 设置默认工作会话
- 每个工作会话独立维护：
  - `workspace_path` — 本地工作目录
  - `model / provider` — 模型配置
  - `tool_profile` / `tool_allow` / `tool_deny` — 工具过滤
  - `max_iterations` — Agent 循环上限
  - `context_summary` — 上下文摘要
  - `memory_auto_extract` / `memory_threshold` — 记忆策略

### 3. Skills 与提示注入

- 自动发现本地 skills
- 为不同工作会话独立启停 skills
- 支持项目级提示文件：`AGENTS.md`、`TOOLS.md`

### 4. 跨会话协作

- `sessions_list` — 查看所有工作会话
- `sessions_history` — 查询其他会话历史
- `sessions_send` — 向其他会话派发任务
- `session_status` — 获取会话状态

### 5. 自动化

- 创建、编辑、启停、删除自动化任务
- 支持调度类型：固定间隔 / 每日 / 每周
- 自动化结果写入对应工作会话历史和运行记录

### 6. 长期记忆

- 长期记忆列表、搜索、筛选、排序
- 支持来源区分：手动创建 / 会话摘要 / 自动提炼
- 支持记忆检索参数配置：top-k、最低相关度、混合检索权重、MMR 重排、时间衰减

## 技术栈

| 层级 | 技术 |
| --- | --- |
| 前端 | React 19、TypeScript、Vite 8.0.1、TailwindCSS 3.4、Framer Motion、lucide-react |
| 后端 | FastAPI 0.115.0、SQLAlchemy 2.0.35、Pydantic 2.9.2、aiosqlite |
| 数据库 | SQLite + sqlite-vec 向量扩展（WAL 模式） |
| 模型接入 | zai-sdk 0.2.2（智谱 AI） |
| 向量嵌入 | sentence-transformers 2.2.0 |
| 浏览器自动化 | Playwright |
| 任务调度 | croniter |

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
│  │  ├─ contexts/            # React Context (AppContext, ThemeContext)
│  │  ├─ services/            # API 层 (axios + fetch SSE)
│  │  └─ types/               # TypeScript 类型定义
│  └─ package.json
├─ backend/
│  ├─ app/
│  │  ├─ agent_loop/          # Agent 执行引擎 (controller.py + prompting.py)
│  │  ├─ api/                 # API 路由 (挂载在 /api 下)
│  │  ├─ core/                # 核心配置
│  │  ├─ dao/                 # 数据访问层
│  │  ├─ models/              # ORM 模型
│  │  ├─ schemas/             # Pydantic Schema
│  │  ├─ services/            # 业务逻辑层
│  │  ├─ tools/               # 工具系统 (registry → executor → profiles)
│  │  └─ main.py              # 应用入口
│  ├─ tests/                  # 单元测试
│  └─ requirements.txt
├─ docs/                      # 项目文档
├─ start_all.ps1              # Windows 一键启动脚本
└─ README.md
```

## 数据库 Schema

### conversations

| 字段 | 类型 | 描述 |
| --- | --- | --- |
| id | INTEGER | 主键，自增 |
| title | TEXT | 会话标题 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### messages

| 字段 | 类型 | 描述 |
| --- | --- | --- |
| id | INTEGER | 主键 |
| conversation_id | INTEGER | 外键，关联 conversation |
| role | TEXT | 角色 (user / assistant) |
| content | TEXT | 消息内容 |
| embedding | BLOB | 向量嵌入 |
| created_at | DATETIME | 创建时间 |

### long_term_memory

| 字段 | 类型 | 描述 |
| --- | --- | --- |
| id | INTEGER | 主键 |
| key | TEXT | 记忆键（可选） |
| content | TEXT | 记忆内容 |
| embedding | BLOB | 向量嵌入 |
| importance | FLOAT | 重要性评分 (0-1) |
| source | TEXT | 记忆来源 |
| created_at | DATETIME | 创建时间 |

## 工具系统

工具系统使用注册表模式进行动态工具注册和管理：

- **注册工具**：通过 `ToolRegistry` 注册新工具
- **执行工具**：通过 `ToolExecutor` 执行工具调用
- **工具过滤**：支持 allow / deny 列表控制可用工具

### 内置工具

| 工具名 | 描述 |
| --- | --- |
| `get_current_time` | 获取当前时间 |
| `browser_start` | 启动浏览器 |
| `browser_navigate` | 导航到 URL |
| `browser_snapshot` | 获取页面快照 |
| `browser_screenshot` | 截取页面或元素截图 |
| `browser_click` | 点击页面元素 |
| `browser_type` | 在元素中输入文本 |
| `browser_hover` | 悬停在页面元素上 |
| `browser_wait` | 等待条件 |
| `browser_scroll` | 滚动页面 |
| `browser_press` | 模拟键盘按键 |
| `browser_select` | 在下拉菜单中选择选项 |
| `browser_history` | 导航浏览器历史（前进 / 后退） |
| `browser_stop` | 停止浏览器 |
| `web_search` | 网络搜索 |

## 记忆搜索特性

- **混合搜索**：结合向量相似度和文本匹配
- **MMR 重排**：最大边际相关性，获得多样化结果
- **时间衰减**：基于时间的相关性评分
- **可配置参数**：`top_k`、`min_score`、`vector_weight` / `text_weight`、`mmr_lambda`、`half_life_days`

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- 一个可用的模型 API Key

### 1. 安装依赖

```powershell
# 后端
cd backend
pip install -r requirements.txt

# 前端
cd frontend
npm install
```

### 2. 启动服务

**方式 A：一键启动（Windows）**

```powershell
.\start_all.ps1
```

**方式 B：分别启动**

```powershell
# 终端 1 — 后端
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 终端 2 — 前端
cd frontend
npm run dev
```

### 3. 配置 API Key

1. 打开 [http://localhost:5173](http://localhost:5173)
2. 进入设置页面
3. 填入模型 API Key
4. 保存配置

## 主要 API

### 聊天

| 端点 | 方法 | 描述 |
| --- | --- | --- |
| `/api/chat/stream` | POST | 流式聊天（SSE） |

### 工作会话

| 端点 | 方法 | 描述 |
| --- | --- | --- |
| `/api/sessions` | GET / POST | 列表 / 创建工作会话 |
| `/api/sessions/{id}` | PUT / DELETE | 更新 / 删除工作会话 |
| `/api/sessions/{id}/status` | GET | 获取会话状态 |
| `/api/sessions/{id}/dispatch` | POST | 向会话派发任务 |
| `/api/sessions/{id}/history-summary` | GET | 获取会话历史摘要 |

### Skills

| 端点 | 方法 | 描述 |
| --- | --- | --- |
| `/api/skills` | GET | 获取可用 skills |
| `/api/sessions/{id}/skills` | GET / PUT | 获取 / 更新会话 skills |

### 自动化

| 端点 | 方法 | 描述 |
| --- | --- | --- |
| `/api/automations` | GET / POST | 列表 / 创建自动化任务 |
| `/api/automations/{id}` | PUT / DELETE | 更新 / 删除自动化任务 |
| `/api/automations/{id}/runs` | GET | 获取运行记录 |

### 记忆

| 端点 | 方法 | 描述 |
| --- | --- | --- |
| `/api/memory/long-term` | GET / POST | 长期记忆列表 / 创建 |
| `/api/memory/long-term/{id}` | PUT / DELETE | 更新 / 删除长期记忆 |
| `/api/memory/search` | POST | 语义记忆搜索 |

启动后访问 [http://localhost:8000/docs](http://localhost:8000/docs) 查看完整 API 文档（Swagger UI）。

## 测试

后端测试可在 `backend` 目录运行：

```powershell
$env:PYTHONPATH='D:\Project\Me\myclaw-new\myclaw\backend'
python -m unittest discover -s tests -p "test_*.py"
```

当前已通过的测试：

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
