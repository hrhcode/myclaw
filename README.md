# MyClaw

<p align="center">
  <strong>极简 AI 助手 - 面向个人用户的微信 AI 机器人</strong>
</p>

<p align="center">
  <a href="#特性">特性</a> •
  <a href="#快速开始">快速开始</a> •
  <a href="#配置">配置</a> •
  <a href="#技术栈">技术栈</a>
</p>

---

## 特性

- 🤖 **AI 对话** - 基于智谱 AI 免费大模型
- 💬 **微信集成** - 企业微信机器人通道
- 🔧 **工具调用** - 网络搜索、网页抓取等
- 🧠 **记忆系统** - 对话记忆和语义搜索
- 🌐 **Web 界面** - 可选的 Web 聊天界面
- 📦 **极简部署** - 单进程、单配置文件

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+ (可选，用于前端)

### 安装

```bash
# 克隆项目
git clone https://github.com/hrhcode/myclaw.git
cd myclaw

# 安装后端依赖
cd backend
pip install -e .

# 安装前端依赖（可选）
cd ../frontend
npm install
```

### 配置

```bash
# 复制配置文件
cp config.example.yaml config.yaml

# 编辑配置
vim config.yaml

# 设置环境变量
export ZHIPU_API_KEY=your_api_key
```

### 启动

```bash
# 启动后端
cd backend
python -m app.main

# 启动前端（可选）
cd frontend
npm run dev
```

## 配置

```yaml
server:
  port: 18789
  host: "127.0.0.1"

llm:
  provider: zhipu
  model: glm-4-flash
  api_key: "${ZHIPU_API_KEY}"

wechat:
  enabled: true
  corp_id: "${WECHAT_CORP_ID}"
  agent_id: "${WECHAT_AGENT_ID}"
  secret: "${WECHAT_SECRET}"

memory:
  enabled: true
  embedding_model: embedding-3
```

## 技术栈

| 层级 | 技术 |
|------|------|
| LLM | 智谱 AI (glm-4-flash) |
| 后端 | Python + FastAPI + SQLite |
| 前端 | Vue 3 + Vite + TailwindCSS |
| 通道 | 企业微信机器人 |

## 许可证

MIT License
