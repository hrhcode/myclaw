<p align="center">
  <img src="frontend/public/myclaw.svg" alt="MyClaw Logo" width="160">
</p>

<h1 align="center">MyClaw</h1>

<p align="center">
  <strong>A lightweight personal edition of OpenClaw — Built with React + FastAPI + SQLite</strong>
</p>

<p align="center">
  <a href="README.md">中文</a> | <a href="README_EN.md">English</a>
</p>

---

MyClaw is a lightweight personal edition of [OpenClaw](https://github.com/openclaw/openclaw). OpenClaw is feature-rich but overly complex for individual users — its 22 messaging channels, native mobile apps, voice wake-up, Docker sandbox, and many other features are unnecessary for most personal use cases. MyClaw keeps only the **core capabilities** of OpenClaw (Agent loop, tool system, memory, channel integration, automation) and reimplements them with a Python + React frontend-backend architecture, allowing full configuration and management through the browser.

<table>
<tr>
<td><img src="docs/assets/电脑渠道展示截图.jpg" alt="MyClaw Desktop UI" width="100%"></td>
<td><img src="docs/assets/qq渠道展示截图.jpg" alt="MyClaw QQ Channel UI" width="100%"></td>
</tr>
</table>

---

## Key Differences from OpenClaw

| Dimension | OpenClaw | **MyClaw** |
| --- | --- | --- |
| **Architecture** | CLI-First, single-process Gateway + WS control plane | **Web-First**, frontend-backend separation (FastAPI + React), all operations via browser |
| **Entry Barrier** | Requires CLI basics, `openclaw wizard` guided setup | **Zero CLI**, open browser and use |
| **Tech Stack** | TypeScript / Node.js | **Python + React**, backend natively suited for AI/data processing |
| **Visual Management** | Control UI as auxiliary entry | **All pages are first-class citizens**, sessions, memory, channels, automation all visualized |
| **Agent Anti-Loop** | Pi Agent RPC mode | **4-layer protection**: iteration cap, progress signature, loop detection, circuit breaker |
| **Memory System** | Single memory plugin slot | **Full pipeline**: Vector + BM25 hybrid search + MMR reranking + temporal decay + Evergreen |
| **Work Sessions** | Channel-based session model | **Independent work sessions**, each with its own model, toolset, working directory, memory strategy |
| **Learning Curve** | Requires understanding Gateway / CLI / node concepts | **Intuitive operation**, similar to using a regular web app |

---

## Core Capabilities

| Module | Capabilities |
| --- | --- |
| **Smart Chat** | SSE streaming responses, full tool call traces, `/new` `/reset` `/compact` `/status` commands, automatic context compression |
| **Work Sessions** | Independent runtime environments with configurable model, toolset, working directory, memory strategy; create / switch / rename / delete / set default |
| **Cross-Session Collaboration** | View all sessions, query other session histories, dispatch tasks to other sessions, get real-time status |
| **Smart Memory** | Dual-layer memory (short-term messages + long-term); hybrid retrieval (Vector + BM25) + MMR reranking + temporal decay + Evergreen |
| **External Channels** | QQ Official Bot integration, supporting channel / DM / group messages / @ trigger; 3-level session mapping; WebSocket real-time message routing |
| **Browser Automation** | Full Playwright-based control: navigate / click / type / scroll / screenshot / dropdown select / keyboard simulate / wait for conditions |
| **Automation Tasks** | Fixed interval / daily / weekly scheduling, results written to work sessions, visual management |
| **Skills** | Auto-discover local skills, enable/disable per work session, supports `AGENTS.md` / `TOOLS.md` project-level prompts |
| **MCP Services** | Built-in MCP service management page, visual configuration and management |
| **Tool System** | 5 preset profiles (MINIMAL / STANDARD / CODING / MESSAGING / FULL), allow/deny whitelists, timeout control, sensitive field auto-hiding |

---

## Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | React 19, TypeScript, Vite 8.0.1, TailwindCSS 3.4, Framer Motion, lucide-react |
| Backend | FastAPI 0.115.0, SQLAlchemy 2.0.35, Pydantic 2.9.2, aiosqlite |
| Database | SQLite + sqlite-vec vector extension (WAL mode) |
| AI Model | zai-sdk 0.2.2 (Zhipu AI) |
| Embeddings | sentence-transformers 2.2.0 |
| Browser Automation | Playwright |
| Task Scheduling | croniter |

---

## Project Structure

```text
myclaw/
├─ frontend/
│  ├─ src/
│  │  ├─ components/
│  │  │  ├─ chat/             # Chat page
│  │  │  ├─ channels/         # Channel management page
│  │  │  ├─ conversations/    # Conversation history page
│  │  │  ├─ sessions/         # Work sessions page
│  │  │  ├─ automations/      # Automation page
│  │  │  ├─ memory/           # Memory page
│  │  │  ├─ settings/         # Settings page
│  │  │  ├─ tools/            # Tools page
│  │  │  └─ layout/           # Layout components
│  │  ├─ contexts/            # React Context (AppContext, ThemeContext)
│  │  ├─ hooks/               # Custom Hooks
│  │  ├─ services/            # API layer (axios + fetch SSE)
│  │  └─ types/               # TypeScript type definitions
│  └─ package.json
├─ backend/
│  ├─ app/
│  │  ├─ agent_loop/          # Agent execution engine (controller.py + prompting.py)
│  │  ├─ api/                 # API routes (mounted under /api)
│  │  ├─ channels/            # Channel system (base, gateway, manager, registry)
│  │  │  └─ qq/               # QQ Official Bot channel implementation
│  │  ├─ core/                # Core configuration
│  │  ├─ dao/                 # Data access layer
│  │  ├─ models/              # ORM models
│  │  ├─ schemas/             # Pydantic schemas
│  │  ├─ services/            # Business logic layer
│  │  ├─ tools/               # Tool system (registry → executor → profiles)
│  │  └─ main.py              # Application entry point
│  ├─ tests/                  # Unit tests
│  └─ requirements.txt
├─ docs/                      # Project documentation + screenshots
├─ start_all.ps1              # One-click startup script (Windows)
└─ README.md
```

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- A valid model API Key

### 1. Install Dependencies

```powershell
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### 2. Start Services

**Option A: One-Click Start (Windows)**

```powershell
.\start_all.ps1
```

**Option B: Manual Start**

```powershell
# Terminal 1 — Backend
cd backend
python start_server.py

# Terminal 2 — Frontend
cd frontend
npm run dev
```

### 3. Configure API Key

1. Open [http://localhost:5173](http://localhost:5173)
2. Navigate to Settings
3. Enter your model API Key
4. Save configuration

---

## License

MIT
