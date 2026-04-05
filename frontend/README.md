# MyClaw Frontend

MyClaw 前端应用，基于 React 19 + TypeScript + Vite 构建。

## 技术栈

- **React 19** - UI 框架
- **TypeScript** - 类型安全
- **Vite 8** - 构建工具
- **TailwindCSS 3.4** - CSS 框架
- **Framer Motion** - 动画库
- **lucide-react** - 图标库

## 项目结构

```text
src/
├── components/
│   ├── chat/             # 聊天页
│   ├── channels/         # 通道管理页
│   ├── conversations/    # 聊天记录页
│   ├── sessions/         # 工作会话页
│   ├── automations/      # 自动化页
│   ├── memory/           # 记忆页
│   ├── settings/         # 设置页
│   ├── tools/            # 工具页
│   └── layout/           # 布局组件
├── contexts/             # React Context (AppContext, ThemeContext)
├── hooks/                # 自定义 Hooks
├── services/             # API 层 (axios + fetch SSE)
└── types/                # TypeScript 类型定义
```

## 开发命令

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览生产构建
npm run preview

# 代码检查
npm run lint
```

## 环境要求

- Node.js 18+
- npm 9+

## 相关链接

- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs
- 前端开发服务器: http://localhost:5173
