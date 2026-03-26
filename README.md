# AI对话助手

基于GLM-4.7-Flash模型的智能对话应用，支持流式输出和会话管理。

## 技术栈

- **前端**: React + TypeScript + Vite + TailwindCSS
- **后端**: Python + FastAPI
- **数据库**: SQLite
- **大模型**: GLM-4.7-Flash (智谱AI)

## 功能特性

- ✅ 现代化聊天UI界面
- ✅ 支持流式输出显示
- ✅ 前端配置API Key
- ✅ 会话管理（创建、切换、删除）
- ✅ 历史对话记录持久化
- ✅ Markdown消息渲染
- ✅ 深色模式支持

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
│   │   ├── services/            # API服务
│   │   ├── types/               # TypeScript类型定义
│   │   └── App.tsx              # 主应用组件
│   └── package.json
│
├── backend/                     # 后端项目
│   ├── app/
│   │   ├── api/                 # API路由
│   │   │   ├── chat.py          # 聊天接口
│   │   │   └── history.py       # 历史记录接口
│   │   ├── models/              # 数据模型
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── database.py          # 数据库配置
│   │   └── main.py             # 应用入口
│   └── requirements.txt
│
├── start_backend.bat            # 启动后端脚本
└── start_frontend.bat           # 启动前端脚本
```

## 快速开始

### 1. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 启动后端服务

```bash
# Windows
start_backend.bat

# 或手动启动
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端服务将在 http://localhost:8000 启动

### 3. 安装前端依赖

```bash
cd frontend
npm install
```

### 4. 启动前端服务

```bash
# Windows
start_frontend.bat

# 或手动启动
cd frontend
npm run dev
```

前端服务将在 http://localhost:5173 启动

### 5. 配置API Key

1. 打开前端应用
2. 点击右上角"设置"按钮
3. 输入您的智谱AI API Key
4. 保存配置

## API文档

启动后端服务后，访问以下地址查看API文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API接口

### 聊天接口

- `POST /api/chat` - 发送消息（非流式）
- `POST /api/chat/stream` - 发送消息（流式）

### 历史记录接口

- `GET /api/conversations` - 获取会话列表
- `POST /api/conversations` - 创建新会话
- `DELETE /api/conversations/{id}` - 删除会话
- `GET /api/conversations/{id}/messages` - 获取会话消息

## 数据库

项目使用SQLite数据库，数据库文件位于 `backend/chat.db`

### 数据表

#### conversations（会话表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| title | TEXT | 会话标题 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

#### messages（消息表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| conversation_id | INTEGER | 关联会话ID |
| role | TEXT | 角色(user/assistant) |
| content | TEXT | 消息内容 |
| created_at | DATETIME | 创建时间 |

## GLM-4.7-Flash API

本项目使用智谱AI的GLM-4.7-Flash模型，详情请参考：

[GLM-4.7-Flash 文档](https://docs.bigmodel.cn/cn/guide/models/free/glm-4.7-flash)

## 开发说明

### 前端开发

```bash
cd frontend
npm run dev      # 开发服务器
npm run build    # 构建生产版本
npm run preview  # 预览生产构建
```

### 后端开发

```bash
cd backend
python -m uvicorn app.main:app --reload
```

## 注意事项

1. 请妥善保管您的API Key，不要泄露
2. API Key存储在浏览器的localStorage中
3. 每次对话都会调用智谱AI API，请注意使用量
4. 数据库文件会在首次运行后端时自动创建

## 许可证

MIT License
