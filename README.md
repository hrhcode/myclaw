<p align="center">
  <h1 align="center">MyClaw - AI 聊天助手</h1>
  <p align="center">
    简体中文 | <a href="README_EN.md">English</a>
  </p>
</p>

基于 GLM-4.7-Flash 的智能对话 AI 助手，具备语义记忆搜索、长期记忆管理和实时日志监控功能。

## ✨ 功能特性

- 🚀 **现代化聊天界面** - 界面简洁响应，支持流式输出
- 🧠 **语义记忆搜索** - 基于向量的消息和长期记忆混合搜索
- 💾 **长期记忆管理** - 持久化存储和检索重要信息
- 📊 **实时日志监控** - 基于 WebSocket 的实时日志流和历史查看
- 🌙 **深色模式** - 完整的深色主题支持
- 💬 **对话管理** - 创建、切换和删除对话
- 📝 **Markdown 渲染** - 富文本显示和代码高亮
- ⚙️ **前端配置** - 直接在 UI 中配置 API Key

## 🛠 技术栈

| 层级     | 技术栈                                     |
| --------- | ------------------------------------------ |
| 前端      | React 19 + TypeScript + Vite + TailwindCSS |
| 后端      | Python + FastAPI + SQLAlchemy (Async)      |
| 数据库    | SQLite with sqlite-vec extension           |
| AI 模型   | GLM-4.7-Flash (智谱 AI)                   |
| 向量嵌入  | sentence-transformers                      |

## 📁 项目结构

```
myclaw/
├── frontend/                      # 前端应用
│   ├── src/
│   │   ├── components/            # React 组件
│   │   │   ├── chat/              # 聊天页面和消息组件
│   │   │   ├── conversations/     # 对话列表页面
│   │   │   ├── memory/            # 记忆搜索和管理
│   │   │   ├── settings/          # 设置页面
│   │   │   └── layout/            # 布局组件
│   │   ├── contexts/              # React 上下文
│   │   ├── hooks/                 # 自定义 Hooks
│   │   ├── services/              # API 服务
│   │   └── types/                 # TypeScript 类型定义
│   └── package.json
│
├── backend/                       # 后端应用
│   ├── app/
│   │   ├── api/                   # API 路由
│   │   │   ├── chat.py            # 聊天接口
│   │   │   ├── history.py         # 对话历史
│   │   │   ├── memory.py          # 记忆搜索和长期记忆
│   │   │   ├── config.py          # 配置管理
│   │   │   └── logs.py            # 日志流
│   │   ├── services/              # 业务逻辑
│   │   ├── models.py              # SQLAlchemy 模型
│   │   ├── schemas.py             # Pydantic 模式
│   │   ├── database.py            # 数据库配置
│   │   ├── llm_service.py         # LLM 集成
│   │   ├── vector_search_service.py # 向量搜索
│   │   └── main.py                # 应用入口
│   └── requirements.txt
│
├── start_all.ps1                  # 一键启动脚本 (Windows)
└── README.md
```

## 🚀 快速开始

### 前置要求

- Python 3.10+
- Node.js 18+
- 智谱 AI API Key

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

| 接口                               | 方法     | 描述                     |
| ---------------------------------- | -------- | ------------------------ |
| `/api/chat/stream`                 | POST     | 与 AI 进行流式对话       |
| `/api/conversations`               | GET/POST | 列表/创建对话            |
| `/api/conversations/{id}`          | DELETE   | 删除对话                 |
| `/api/conversations/{id}/messages` | GET      | 获取对话消息             |
| `/api/memory/search`               | POST     | 语义记忆搜索             |
| `/api/memory/long-term`            | GET/POST | 长期记忆 CRUD 操作       |
| `/api/logs/stream`                 | WebSocket| 实时日志流               |
| `/api/config`                      | GET/PUT  | 配置管理                 |

## 🗄 数据库结构

### conversations（对话表）

| 字段       | 类型     | 描述                 |
| ----------- | -------- | -------------------- |
| id          | INTEGER  | 主键，自增           |
| title       | TEXT     | 对话标题             |
| created_at  | DATETIME | 创建时间             |
| updated_at  | DATETIME | 更新时间             |

### messages（消息表）

| 字段            | 类型     | 描述                 |
| ---------------- | -------- | -------------------- |
| id               | INTEGER  | 主键                 |
| conversation_id  | INTEGER  | 对话外键             |
| role             | TEXT     | 角色 (user/assistant)|
| content          | TEXT     | 消息内容             |
| embedding        | BLOB     | 向量嵌入             |
| created_at       | DATETIME | 创建时间             |

### long_term_memory（长期记忆表）

| 字段       | 类型     | 描述                   |
| ----------- | -------- | ---------------------- |
| id          | INTEGER  | 主键                   |
| key         | TEXT     | 记忆键（可选）         |
| content     | TEXT     | 记忆内容               |
| embedding   | BLOB     | 向量嵌入               |
| importance  | FLOAT    | 重要性分数 (0-1)       |
| source      | TEXT     | 记忆来源               |
| created_at  | DATETIME | 创建时间               |

## 🔧 记忆搜索功能

应用支持高级记忆搜索功能：

- **混合搜索**: 结合向量相似度和文本匹配
- **MMR 重排序**: 最大边际相关性实现多样化结果
- **时间衰减**: 基于时间的相关性评分
- **可配置参数**:
  - `top_k`: 返回结果数量
  - `min_score`: 最小相似度阈值
  - `vector_weight` / `text_weight`: 混合搜索权重
  - `mmr_lambda`: MMR 平衡参数
  - `half_life_days`: 时间衰减半衰期

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

## 📄 许可证

MIT License
