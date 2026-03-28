<p align="center">
  <h1 align="center">MyClaw - AI Chat Assistant</h1>
  <p align="center">
    <a href="README_CN.md">简体中文</a> | English
  </p>
</p>

An intelligent conversational AI assistant based on GLM-4.7-Flash, featuring semantic memory search, long-term memory management, and real-time log monitoring.

## ✨ Features

- 🚀 **Modern Chat UI** - Clean and responsive interface with streaming output
- 🧠 **Semantic Memory Search** - Vector-based hybrid search for messages and long-term memories
- 💾 **Long-term Memory Management** - Store and retrieve important information persistently
- 📊 **Real-time Log Monitoring** - WebSocket-based live log streaming with history view
- 🌙 **Dark Mode** - Full dark theme support
- 💬 **Conversation Management** - Create, switch, and delete conversations
- 📝 **Markdown Rendering** - Rich text display with syntax highlighting
- ⚙️ **Frontend Configuration** - Configure API Key directly in the UI

## 🛠 Tech Stack

| Layer     | Technology                                 |
| --------- | ------------------------------------------ |
| Frontend  | React 19 + TypeScript + Vite + TailwindCSS |
| Backend   | Python + FastAPI + SQLAlchemy (Async)      |
| Database  | SQLite with sqlite-vec extension           |
| AI Model  | GLM-4.7-Flash (Zhipu AI)                   |
| Embedding | sentence-transformers                      |

## 📁 Project Structure

```
myclaw/
├── frontend/                      # Frontend application
│   ├── src/
│   │   ├── components/            # React components
│   │   │   ├── chat/              # Chat page & message components
│   │   │   ├── conversations/     # Conversation list page
│   │   │   ├── memory/            # Memory search & management
│   │   │   ├── settings/          # Settings page
│   │   │   └── layout/            # Layout components
│   │   ├── contexts/              # React contexts
│   │   ├── hooks/                 # Custom hooks
│   │   ├── services/              # API services
│   │   └── types/                 # TypeScript definitions
│   └── package.json
│
├── backend/                       # Backend application
│   ├── app/
│   │   ├── api/                   # API routes
│   │   │   ├── chat.py            # Chat endpoints
│   │   │   ├── history.py         # Conversation history
│   │   │   ├── memory.py          # Memory search & long-term memory
│   │   │   ├── config.py          # Configuration management
│   │   │   └── logs.py            # Log streaming
│   │   ├── services/              # Business logic
│   │   ├── models.py              # SQLAlchemy models
│   │   ├── schemas.py             # Pydantic schemas
│   │   ├── database.py            # Database configuration
│   │   ├── llm_service.py         # LLM integration
│   │   ├── vector_search_service.py # Vector search
│   │   └── main.py                # Application entry
│   └── requirements.txt
│
├── start_all.ps1                  # One-click start script (Windows)
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Zhipu AI API Key

### 1. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 3. Start Services

**Option A: One-click Start (Windows)**

```powershell
.\start_all.ps1
```

**Option B: Manual Start**

```bash
# Terminal 1 - Backend
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### 4. Configure API Key

1. Open <http://localhost:5173>
2. Navigate to Settings
3. Enter your Zhipu AI API Key
4. Save configuration

## 📚 API Documentation

After starting the backend, access the API documentation at:

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>

### Key Endpoints

| Endpoint                           | Method    | Description               |
| ---------------------------------- | --------- | ------------------------- |
| `/api/chat/stream`                 | POST      | Streaming chat with AI    |
| `/api/conversations`               | GET/POST  | List/Create conversations |
| `/api/conversations/{id}`          | DELETE    | Delete a conversation     |
| `/api/conversations/{id}/messages` | GET       | Get conversation messages |
| `/api/memory/search`               | POST      | Semantic memory search    |
| `/api/memory/long-term`            | GET/POST  | Long-term memory CRUD     |
| `/api/logs/stream`                 | WebSocket | Real-time log streaming   |
| `/api/config`                      | GET/PUT   | Configuration management  |

## 🗄 Database Schema

### conversations

| Field       | Type     | Description                 |
| ----------- | -------- | --------------------------- |
| id          | INTEGER  | Primary key, auto-increment |
| title       | TEXT     | Conversation title          |
| created\_at | DATETIME | Creation time               |
| updated\_at | DATETIME | Update time                 |

### messages

| Field            | Type     | Description                 |
| ---------------- | -------- | --------------------------- |
| id               | INTEGER  | Primary key                 |
| conversation\_id | INTEGER  | Foreign key to conversation |
| role             | TEXT     | Role (user/assistant)       |
| content          | TEXT     | Message content             |
| embedding        | BLOB     | Vector embedding            |
| created\_at      | DATETIME | Creation time               |

### long\_term\_memory

| Field       | Type     | Description            |
| ----------- | -------- | ---------------------- |
| id          | INTEGER  | Primary key            |
| key         | TEXT     | Memory key (optional)  |
| content     | TEXT     | Memory content         |
| embedding   | BLOB     | Vector embedding       |
| importance  | FLOAT    | Importance score (0-1) |
| source      | TEXT     | Memory source          |
| created\_at | DATETIME | Creation time          |

## 🔧 Memory Search Features

The application supports advanced memory search capabilities:

- **Hybrid Search**: Combines vector similarity and text matching
- **MMR Reranking**: Maximal Marginal Relevance for diverse results
- **Temporal Decay**: Time-based relevance scoring
- **Configurable Parameters**:
  - `top_k`: Number of results
  - `min_score`: Minimum similarity threshold
  - `vector_weight` / `text_weight`: Hybrid search weights
  - `mmr_lambda`: MMR balance parameter
  - `half_life_days`: Temporal decay half-life

## 📝 Development

### Frontend

```bash
cd frontend
npm run dev      # Development server
npm run build    # Production build
npm run preview  # Preview production build
npm run lint     # Run ESLint
```

### Backend

```bash
cd backend
python -m uvicorn app.main:app --reload  # Development with hot reload
```

## ⚠️ Notes

1. Keep your API Key secure and never share it
2. API Key is stored in browser's localStorage
3. Each conversation calls the Zhipu AI API, monitor your usage
4. Database file is created automatically on first run
5. Vector embeddings are generated asynchronously after message save

## 📄 License

MIT License

