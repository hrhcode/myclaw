<p align="center">
  <img src="frontend/public/myclaw.svg" alt="MyClaw Logo" width="160">
</p>

<h1 align="center">MyClaw</h1>

<p align="center">
  <strong>Personal Agent Platform — Built with React + FastAPI + SQLite</strong>
</p>

<p align="center">
  <a href="README.md">中文</a> | <a href="README_EN.md">English</a>
</p>

---

MyClaw is a lightweight personal Agent platform delivered as a React + FastAPI web application. It has evolved from a single-session chat app into a personal Agent console with work sessions, automation, memory management, and cross-session collaboration.

## Current Status

- Backend has completed core personal edition capabilities
- Backend API has passed local regression testing
- Backend tests have been added for `session / automation / memory / tool executor`
- Frontend has completed closed-loop pages for sessions, automation, and memory
- Frontend core navigation and main page copy have been unified in Chinese

## Core Capabilities

### 1. Chat & Agent Runtime

- Streaming chat responses (SSE)
- Each reply retains run traces and tool call events
- Chat commands: `/new` `/reset` `/compact` `/status`

### 2. Work Sessions

- Create, switch, rename, delete work sessions
- Set a default work session
- Each session independently maintains:
  - `workspace_path` — local working directory
  - `model / provider` — model configuration
  - `tool_profile` / `tool_allow` / `tool_deny` — tool filtering
  - `max_iterations` — Agent loop limit
  - `context_summary` — context summary
  - `memory_auto_extract` / `memory_threshold` — memory strategy

### 3. Skills & Prompt Injection

- Automatic local skill discovery
- Enable/disable skills per work session
- Supports project-level prompt files: `AGENTS.md`, `TOOLS.md`

### 4. Cross-Session Collaboration

- `sessions_list` — view all work sessions
- `sessions_history` — query other session histories
- `sessions_send` — dispatch tasks to other sessions
- `session_status` — get session status

### 5. Automation

- Create, edit, enable/disable, delete automation tasks
- Supported schedules: fixed interval / daily / weekly
- Results are written to the corresponding session history and run records

### 6. Long-Term Memory

- List, search, filter, sort long-term memories
- Source categories: manual creation / session summary / auto-extraction
- Configurable retrieval parameters: top-k, minimum score, hybrid search weights, MMR reranking, temporal decay

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

## Project Structure

```text
myclaw/
├─ frontend/
│  ├─ src/
│  │  ├─ components/
│  │  │  ├─ chat/             # Chat page
│  │  │  ├─ conversations/    # Conversation history page
│  │  │  ├─ sessions/         # Work sessions page
│  │  │  ├─ automations/      # Automation page
│  │  │  ├─ memory/           # Memory page
│  │  │  ├─ settings/         # Settings page
│  │  │  ├─ tools/            # Tools page
│  │  │  └─ layout/           # Layout components
│  │  ├─ contexts/            # React Context (AppContext, ThemeContext)
│  │  ├─ services/            # API layer (axios + fetch SSE)
│  │  └─ types/               # TypeScript type definitions
│  └─ package.json
├─ backend/
│  ├─ app/
│  │  ├─ agent_loop/          # Agent execution engine (controller.py + prompting.py)
│  │  ├─ api/                 # API routes (mounted under /api)
│  │  ├─ core/                # Core configuration
│  │  ├─ dao/                 # Data access layer
│  │  ├─ models/              # ORM models
│  │  ├─ schemas/             # Pydantic schemas
│  │  ├─ services/            # Business logic layer
│  │  ├─ tools/               # Tool system (registry → executor → profiles)
│  │  └─ main.py              # Application entry point
│  ├─ tests/                  # Unit tests
│  └─ requirements.txt
├─ docs/                      # Project documentation
├─ start_all.ps1              # One-click startup script (Windows)
└─ README.md
```

## Database Schema

### conversations

| Field | Type | Description |
| --- | --- | --- |
| id | INTEGER | Primary key, auto-increment |
| title | TEXT | Conversation title |
| created_at | DATETIME | Creation time |
| updated_at | DATETIME | Update time |

### messages

| Field | Type | Description |
| --- | --- | --- |
| id | INTEGER | Primary key |
| conversation_id | INTEGER | Foreign key to conversation |
| role | TEXT | Role (user / assistant) |
| content | TEXT | Message content |
| embedding | BLOB | Vector embedding |
| created_at | DATETIME | Creation time |

### long_term_memory

| Field | Type | Description |
| --- | --- | --- |
| id | INTEGER | Primary key |
| key | TEXT | Memory key (optional) |
| content | TEXT | Memory content |
| embedding | BLOB | Vector embedding |
| importance | FLOAT | Importance score (0-1) |
| source | TEXT | Memory source |
| created_at | DATETIME | Creation time |

## Tool System

The tool system uses a registry pattern for dynamic tool registration and management:

- **Register tools**: Register new tools via `ToolRegistry`
- **Execute tools**: Execute tool calls via `ToolExecutor`
- **Tool filtering**: Support allow / deny lists to control available tools

### Built-in Tools

| Tool Name | Description |
| --- | --- |
| `get_current_time` | Get current time |
| `browser_start` | Start browser |
| `browser_navigate` | Navigate to URL |
| `browser_snapshot` | Get page snapshot |
| `browser_screenshot` | Take page or element screenshot |
| `browser_click` | Click page element |
| `browser_type` | Type text in element |
| `browser_hover` | Hover over page element |
| `browser_wait` | Wait for condition |
| `browser_scroll` | Scroll the page |
| `browser_press` | Simulate keyboard key press |
| `browser_select` | Select option in dropdown |
| `browser_history` | Navigate browser history (back / forward) |
| `browser_stop` | Stop browser |
| `web_search` | Web search |

## Memory Search Features

- **Hybrid Search**: Combines vector similarity and text matching
- **MMR Reranking**: Maximal Marginal Relevance for diverse results
- **Temporal Decay**: Time-based relevance scoring
- **Configurable Parameters**: `top_k`, `min_score`, `vector_weight` / `text_weight`, `mmr_lambda`, `half_life_days`

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
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — Frontend
cd frontend
npm run dev
```

### 3. Configure API Key

1. Open [http://localhost:5173](http://localhost:5173)
2. Navigate to Settings
3. Enter your model API Key
4. Save configuration

## API Reference

### Chat

| Endpoint | Method | Description |
| --- | --- | --- |
| `/api/chat/stream` | POST | Streaming chat (SSE) |

### Work Sessions

| Endpoint | Method | Description |
| --- | --- | --- |
| `/api/sessions` | GET / POST | List / Create work sessions |
| `/api/sessions/{id}` | PUT / DELETE | Update / Delete work session |
| `/api/sessions/{id}/status` | GET | Get session status |
| `/api/sessions/{id}/dispatch` | POST | Dispatch task to session |
| `/api/sessions/{id}/history-summary` | GET | Get session history summary |

### Skills

| Endpoint | Method | Description |
| --- | --- | --- |
| `/api/skills` | GET | Get available skills |
| `/api/sessions/{id}/skills` | GET / PUT | Get / Update session skills |

### Automation

| Endpoint | Method | Description |
| --- | --- | --- |
| `/api/automations` | GET / POST | List / Create automation tasks |
| `/api/automations/{id}` | PUT / DELETE | Update / Delete automation task |
| `/api/automations/{id}/runs` | GET | Get run records |

### Memory

| Endpoint | Method | Description |
| --- | --- | --- |
| `/api/memory/long-term` | GET / POST | Long-term memory list / create |
| `/api/memory/long-term/{id}` | PUT / DELETE | Update / Delete long-term memory |
| `/api/memory/search` | POST | Semantic memory search |

After starting the backend, visit [http://localhost:8000/docs](http://localhost:8000/docs) for the full API documentation (Swagger UI).

## Testing

Backend tests can be run in the `backend` directory:

```powershell
$env:PYTHONPATH='D:\Project\Me\myclaw-new\myclaw\backend'
python -m unittest discover -s tests -p "test_*.py"
```

Tests that have been added and passed:

- `test_session_service.py`
- `test_automation_service.py`
- `test_memory_api.py`
- `test_tool_executor.py`
- `test_agent_loop_prompting.py`
- `test_time_tool.py`

Frontend build verification:

```powershell
cd frontend
npm run build
```

## Known Boundaries

- Currently designed for single-user personal use; team, multi-tenant, and multi-channel support are not included
- Security approval, sandbox isolation, and privilege escalation controls are not a focus of this phase
- Canvas, voice, mobile nodes, and plugin marketplace are not included
- Historical chat content in English will be displayed as-is and will not be translated by the UI

## Development Tips

- Use work sessions to isolate different projects
- Prefer automation over manual repeated triggering for long-running tasks
- Configure `workspace_path` and local skills for fixed project directories

## License

MIT
