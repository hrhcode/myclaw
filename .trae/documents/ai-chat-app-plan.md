# AI对话软件开发计划

## 项目概述
开发一款AI对话软件，支持与智谱AI GLM-4.7-Flash模型进行智能对话。

## 技术栈
- **前端**: React + TypeScript + Vite
- **后端**: Python + FastAPI
- **数据库**: SQLite
- **大模型**: GLM-4.7-Flash (智谱AI)

## 项目结构

```
myclaw/
├── frontend/                    # 前端项目
│   ├── src/
│   │   ├── components/          # 组件目录
│   │   │   ├── ChatWindow/      # 聊天窗口组件
│   │   │   ├── MessageList/     # 消息列表组件
│   │   │   ├── MessageInput/    # 消息输入组件
│   │   │   └── Settings/        # 设置组件(API Key配置)
│   │   ├── hooks/               # 自定义Hooks
│   │   ├── services/            # API服务
│   │   ├── types/               # TypeScript类型定义
│   │   ├── utils/               # 工具函数
│   │   ├── App.tsx              # 主应用组件
│   │   └── main.tsx             # 入口文件
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                     # 后端项目
│   ├── app/
│   │   ├── api/                 # API路由
│   │   │   ├── chat.py          # 聊天接口
│   │   │   └── history.py       # 历史记录接口
│   │   ├── models/              # 数据模型
│   │   ├── services/            # 业务逻辑
│   │   ├── database/            # 数据库配置
│   │   └── main.py              # 应用入口
│   ├── requirements.txt
│   └── .env
│
└── README.md
```

## 功能模块

### 1. 前端功能
- **对话界面**: 现代化聊天UI，支持流式输出
- **消息管理**: 显示用户和AI消息，支持Markdown渲染
- **API Key配置**: 前端设置页面配置智谱AI API Key
- **会话管理**: 创建、切换、删除对话会话
- **历史记录**: 查看历史对话记录

### 2. 后端功能
- **对话API**: 调用GLM-4.7-Flash模型，支持流式响应
- **会话存储**: 保存对话历史到SQLite
- **消息持久化**: 存储用户消息和AI回复
- **CORS配置**: 支持前端跨域请求

## 开发步骤

### 阶段一：项目初始化
1. 创建前端项目 (React + TypeScript + Vite)
2. 创建后端项目 (FastAPI)
3. 初始化SQLite数据库

### 阶段二：后端开发
1. 设计数据库表结构 (会话表、消息表)
2. 实现数据库连接和ORM配置
3. 开发对话API接口 (调用GLM-4.7-Flash)
4. 实现流式响应功能
5. 开发历史记录API

### 阶段三：前端开发
1. 搭建基础UI框架和样式
2. 实现API Key配置组件
3. 开发聊天窗口组件
4. 实现消息列表和消息输入组件
5. 集成流式输出显示
6. 实现会话管理功能

### 阶段四：联调测试
1. 前后端接口联调
2. 流式输出测试
3. 数据持久化测试
4. 用户体验优化

## 数据库设计

### 会话表 (conversations)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| title | TEXT | 会话标题 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 消息表 (messages)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| conversation_id | INTEGER | 关联会话ID |
| role | TEXT | 角色(user/assistant) |
| content | TEXT | 消息内容 |
| created_at | DATETIME | 创建时间 |

## API设计

### 后端API
- `POST /api/chat`: 发送消息并获取AI回复 (支持流式)
- `GET /api/conversations`: 获取会话列表
- `POST /api/conversations`: 创建新会话
- `DELETE /api/conversations/{id}`: 删除会话
- `GET /api/conversations/{id}/messages`: 获取会话消息

### GLM-4.7-Flash API调用
- 端点: `https://open.bigmodel.cn/api/paas/v4/chat/completions`
- 模型: `glm-4.7-flash`
- 支持流式输出和深度思考模式

## 依赖清单

### 前端依赖
- react, react-dom
- typescript
- vite
- axios (HTTP请求)
- react-markdown (Markdown渲染)
- tailwindcss (样式)

### 后端依赖
- fastapi
- uvicorn
- sqlalchemy
- aiosqlite
- httpx (异步HTTP请求)
- python-dotenv
