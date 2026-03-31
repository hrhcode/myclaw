<p align="center">
  <h1 align="center">MyClaw - AI 聊天助手</h1>
  <p align="center">
    简体中文 | <a href="README_EN.md">English</a>
  </p>
</p>

基于 GLM-4 的智能对话 AI 助手，具备语义记忆搜索、长期记忆管理、工具调用和实时日志监控功能。

## ✨ 功能特性

- 🚀 **现代化聊天界面** - 界面简洁响应，支持流式输出和 AI 思考过程展示
- 🧠 **语义记忆搜索** - 基于向量的消息和长期记忆混合搜索，支持 MMR 重排序和时间衰减
- 💾 **长期记忆管理** - 持久化存储和检索重要信息，支持重要性评分
- 🔧 **工具调用系统** - 支持动态注册工具，AI 可调用外部工具执行任务
- 🖥️ **浏览器自动化** - 支持浏览器启动、导航、截图、点击等自动化操作
- 📊 **实时日志监控** - 基于 WebSocket 的实时日志流和历史查看
- 🌙 **深色模式** - 完整的深色主题支持
- 💬 **对话管理** - 创建、切换和删除对话
- 📝 **Markdown 渲染** - 富文本显示和代码高亮
- ⚙️ **前端配置** - 直接在 UI 中配置 API Key 和模型参数

## 🛠 技术栈

| 层级     | 技术栈                                     |
| --------- | ------------------------------------------ |
| 前端      | React 19 + TypeScript + Vite + TailwindCSS |
| 后端      | Python 3.10+ + FastAPI + SQLAlchemy 2.0 (Async) |
| 数据库    | SQLite + sqlite-vec (向量扩展) + FTS5 (全文搜索) |
| AI 模型   | GLM-4-Flash / GLM-4 / GLM-4-Plus (智谱 AI) |
| 向量嵌入  | OpenRouter API (NVIDIA Llama-Nemotron) 或本地 sentence-transformers |

## 📁 项目结构

```
myclaw/
├── frontend/                      # 前端应用 (React + TypeScript)
│   ├── src/
│   │   ├── components/          # React 组件
│   │   │   ├── chat/             # 聊天页面和消息组件
│   │   │   ├── conversations/     # 对话列表页面
│   │   │   ├── memory/           # 记忆搜索和管理组件
│   │   │   ├── settings/         # 设置页面
│   │   │   ├── tools/            # 工具管理页面
│   │   │   └── layout/           # 布局组件
│   │   ├── contexts/             # React 上下文 (AppContext, ThemeContext)
│   │   ├── hooks/                # 自定义 Hooks
│   │   ├── services/             # API 服务层
│   │   └── types/                # TypeScript 类型定义
│   └── package.json
│
├── backend/                      # 后端应用 (Python + FastAPI)
│   ├── app/
│   │   ├── api/                  # API 路由层 (Web层)
│   │   │   ├── chat.py           # 聊天接口 (流式响应)
│   │   │   ├── history.py        # 对话历史 CRUD
│   │   │   ├── memory.py         # 记忆搜索和长期记忆管理
│   │   │   ├── config.py         # 配置管理
│   │   │   ├── logs.py           # 日志流和历史查询
│   │   │   └── tools.py          # 工具管理
│   │   │
│   │   ├── services/             # 业务逻辑层 (Service层)
│   │   │   ├── llm_service.py           # LLM 调用封装
│   │   │   ├── conversation_service.py   # 会话业务逻辑
│   │   │   ├── message_service.py       # 消息业务逻辑
│   │   │   ├── vector_search_service.py # 向量搜索编排 (混合搜索)
│   │   │   ├── embedding_service.py     # 向量嵌入生成
│   │   │   ├── memory_flush_service.py  # 记忆刷新服务
│   │   │   ├── memory_summarizer.py     # 记忆摘要生成
│   │   │   ├── sqlite_vec_service.py    # sqlite-vec 封装
│   │   │   └── log_service.py           # 日志服务
│   │   │
│   │   ├── dao/                  # 数据访问层 (DAO层)
│   │   │   ├── conversation_dao.py  # 会话数据访问
│   │   │   ├── message_dao.py       # 消息数据访问
│   │   │   ├── memory_dao.py        # 长期记忆数据访问
│   │   │   ├── config_dao.py        # 配置数据访问
│   │   │   └── tool_call_dao.py     # 工具调用记录访问
│   │   │
│   │   ├── models/               # ORM 实体层 (Domain层)
│   │   │   └── models.py          # SQLAlchemy 模型定义
│   │   │
│   │   ├── schemas/              # DTO 层 (Domain层)
│   │   │   └── schemas.py         # Pydantic Schema 定义
│   │   │
│   │   ├── tools/                # 工具系统
│   │   │   ├── registry.py        # 工具注册表
│   │   │   ├── executor.py        # 工具执行器
│   │   │   ├── base.py            # 工具基类定义
│   │   │   ├── schemas.py        # 工具 Schema 定义
│   │   │   └── builtin/           # 内置工具实现
│   │   │       └── time_tool.py   # 获取当前时间工具
│   │   │
│   │   ├── common/               # 公共组件 (Common层)
│   │   │   ├── config.py          # 配置读写工具
│   │   │   ├── constants.py       # 常量定义
│   │   │   ├── exceptions.py      # 全局异常定义
│   │   │   ├── response.py       # 统一响应模型
│   │   │   ├── logging_config.py  # 日志配置
│   │   └── utils/                # 工具函数
│   │   │       ├── embedding.py   # 嵌入向量工具
│   │   │       ├── search.py      # 搜索算法工具
│   │   │       ├── text.py        # 文本处理工具
│   │   │       └── logging.py     # 日志工具
│   │   │
│   │   ├── core/                 # 核心配置
│   │   │   └── database.py       # 数据库配置和会话管理
│   │   │
│   │   └── main.py               # 应用入口
│   │
│   ├── migrations/               # 数据库迁移脚本
│   │   └── run_migration.py
│   │
│   └── requirements.txt
│
├── start_all.ps1                  # 一键启动脚本 (Windows)
├── README.md
└── README_EN.md
```

## 🏗 后端架构

后端采用经典的分层架构设计：

```
┌─────────────────────────────────────────────────────────────┐
│                      API Layer (api/)                        │
│         负责处理 HTTP 请求/响应，参数校验，路由分发              │
│    chat.py | history.py | config.py | memory.py | logs.py  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer (services/)                  │
│              封装业务逻辑，处理业务规则和流程                   │
│  llm_service | vector_search_service | embedding_service    │
│  conversation_service | message_service | log_service       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      DAO Layer (dao/)                        │
│            封装数据库操作，提供统一的数据访问接口               │
│  conversation_dao | message_dao | memory_dao | config_dao   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Models & Schemas Layer                     │
│        Models: SQLAlchemy ORM 实体定义                        │
│        Schemas: Pydantic DTO 定义                             │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 前置要求

- Python 3.10+
- Node.js 18+
- 智谱 AI API Key (用于 LLM 对话)
- OpenRouter API Key (用于向量嵌入，可选)

### 1. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 安装前端依赖

```bash
cd frontend
npm install
```

### 3. 启动服务

**方式 A: 一键启动 (Windows)**

```powershell
.\start_all.ps1
```

**方式 B: 手动启动**

```bash
# 终端 1 - 后端
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 终端 2 - 前端
cd frontend
npm run dev
```

### 4. 配置 API Key

1. 打开 <http://localhost:5173>
2. 进入设置页面
3. 输入您的智谱 AI API Key
4. 保存配置

## 📚 API 文档

启动后端后，访问 API 文档：

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>

### 主要接口

| 接口                               | 方法          | 描述                     |
| ---------------------------------- | ------------- | ------------------------ |
| `/api/chat/stream`                 | POST          | 与 AI 进行流式对话       |
| `/api/conversations`               | GET/POST/DELETE/PUT | 会话管理           |
| `/api/conversations/{id}/messages` | GET           | 获取对话消息             |
| `/api/memory/search`               | POST          | 语义记忆搜索             |
| `/api/memory/long-term`            | GET/POST/PUT/DELETE | 长期记忆 CRUD    |
| `/api/memory/index/{id}`           | POST          | 为会话消息生成向量索引   |
| `/api/logs/stream`                 | WebSocket     | 实时日志流               |
| `/api/logs/history`                | GET           | 历史日志查询             |
| `/api/logs/stats`                  | GET           | 日志统计信息             |
| `/api/logs/cleanup`                | POST          | 日志清理                 |
| `/api/config`                      | GET/POST/PUT/DELETE | 配置管理          |
| `/api/config/providers`             | GET           | 获取 LLM 提供商列表      |
| `/api/tools`                       | GET           | 获取工具列表             |
| `/api/tools/{name}/toggle`         | PUT           | 启用/禁用工具            |

## 🗄 数据库结构

### conversations（对话表）

| 字段       | 类型      | 描述                 |
| ---------- | --------- | -------------------- |
| id         | INTEGER   | 主键，自增           |
| title      | TEXT      | 对话标题             |
| created_at | DATETIME  | 创建时间             |
| updated_at | DATETIME  | 更新时间             |

### messages（消息表）

| 字段             | 类型      | 描述                 |
| ---------------- | --------- | -------------------- |
| id               | INTEGER   | 主键                 |
| conversation_id  | INTEGER   | 对话外键             |
| role             | TEXT      | 角色 (user/assistant)|
| content          | TEXT      | 消息内容             |
| embedding        | BLOB      | 向量嵌入             |
| embedding_model  | TEXT      | 嵌入模型名称         |
| created_at       | DATETIME  | 创建时间             |

### long_term_memory（长期记忆表）

| 字段       | 类型      | 描述                   |
| ---------- | --------- | ---------------------- |
| id         | INTEGER   | 主键                   |
| key        | TEXT      | 记忆键（可选）         |
| content    | TEXT      | 记忆内容               |
| embedding  | BLOB      | 向量嵌入               |
| importance | FLOAT     | 重要性分数 (0-1)       |
| source     | TEXT      | 记忆来源               |
| created_at | DATETIME  | 创建时间               |
| updated_at | DATETIME  | 更新时间               |

### tool_calls（工具调用记录表）

| 字段              | 类型      | 描述                   |
| ----------------- | --------- | ---------------------- |
| id                | INTEGER   | 主键                   |
| message_id        | INTEGER   | 关联消息外键           |
| conversation_id   | INTEGER   | 对话外键               |
| tool_name         | TEXT      | 工具名称               |
| tool_call_id      | TEXT      | 工具调用 ID            |
| arguments         | TEXT      | 调用参数 (JSON)        |
| result            | TEXT      | 调用结果 (JSON)        |
| status            | TEXT      | 状态 (pending/success/failed) |
| error             | TEXT      | 错误信息               |
| created_at        | DATETIME  | 创建时间               |

### embedding_cache（嵌入缓存表）

| 字段              | 类型      | 描述                   |
| ----------------- | --------- | ---------------------- |
| id                | INTEGER   | 主键                   |
| content_hash      | TEXT      | 内容哈希 (唯一索引)    |
| embedding         | BLOB      | 向量嵌入               |
| model             | TEXT      | 嵌入模型名称           |
| created_at        | DATETIME  | 创建时间               |
| last_accessed_at  | DATETIME  | 最后访问时间           |
| access_count      | INTEGER   | 访问次数               |

### logs（日志表）

| 字段       | 类型      | 描述                   |
| ---------- | --------- | ---------------------- |
| id         | INTEGER   | 主键                   |
| timestamp  | TEXT      | 日志时间戳             |
| level      | TEXT      | 日志级别               |
| logger     | TEXT      | 日志记录器名称         |
| message    | TEXT      | 日志消息               |
| extra      | TEXT      | 额外信息 (JSON)        |
| created_at | DATETIME  | 创建时间               |

## 🔧 记忆搜索功能

应用支持高级记忆搜索功能：

- **混合搜索**: 结合向量相似度 (sqlite-vec) 和 BM25 全文搜索
- **MMR 重排序**: 最大边际相关性 (Maximal Marginal Relevance) 实现多样化结果
- **时间衰减**: 基于时间的重要性评分衰减
- **可配置参数**:
  - `top_k`: 返回结果数量
  - `min_score`: 最小相似度阈值
  - `vector_weight` / `text_weight`: 混合搜索权重
  - `mmr_lambda`: MMR 平衡参数
  - `enable_temporal_decay`: 是否启用时间衰减
  - `half_life_days`: 时间衰减半衰期

## 🔧 工具调用系统

工具调用系统采用注册表模式，支持动态注册和管理工具：

- **注册工具**: 通过 `ToolRegistry` 注册新工具
- **执行工具**: 通过 `ToolExecutor` 执行工具调用
- **内置工具**: `get_current_time` - 获取当前时间
- **工具过滤**: 支持 allow/deny 列表控制可用工具

## 📝 开发

### 前端

```bash
cd frontend
npm run dev      # 开发服务器
npm run build    # 生产构建
npm run preview  # 预览生产构建
npm run lint     # 运行 ESLint
```

### 后端

```bash
cd backend
python -m uvicorn app.main:app --reload  # 开发模式（热重载）
```

## ⚠️ 注意事项

1. 请妥善保管您的 API Key，切勿分享给他人
2. API Key 存储在浏览器的 localStorage 中
3. 每次对话都会调用智谱 AI API，请注意使用量
4. 数据库文件会在首次运行时自动创建
5. 向量嵌入会在消息保存后异步生成
6. 首次搜索前需确保消息已生成向量嵌入

## 📄 许可证

MIT License
