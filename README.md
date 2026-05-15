# 🤖 InsightAgent

> Full-stack AI chat platform — voice, documents, web search, and more.

![Stack](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18.2-61DAFB?style=flat-square&logo=react&logoColor=black)
![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=flat-square&logo=python&logoColor=white)
![Google ADK](https://img.shields.io/badge/Google%20ADK-Gemini%202.5%20Flash-4285F4?style=flat-square&logo=google&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)

---

## ✨ Features

| Feature | Description |
|---|---|
| 💬 **AI Chat** | Natural language conversations powered by **Gemini 2.5 Flash** via Google ADK |
| 🤖 **Agentic Tools** | Agent autonomously decides when to search the web, calculate, or query documents |
| 🎤 **Voice Input** | Local Whisper transcription — auto-stops on silence detection via Web Audio API |
| 🔊 **Text-to-Speech** | Read any message aloud with one click |
| 📄 **RAG** | Document upload with semantic search via Qdrant + sentence-transformers |
| 🔍 **Web Search** | Google Custom Search integration (tool available to the agent) |
| 🧮 **Calculator** | Safe AST-based evaluation of math expressions (agent tool) |
| 🔐 **Authentication** | JWT-based user registration and login |
| 📝 **History** | Conversations persisted per user in PostgreSQL |
| ⚡ **WebSocket** | Real-time message channel |
| 🛡️ **Rate Limiting** | Endpoint protection via Redis |

---

## 🖼️ UI

- Modern design with dark sidebar and clean chat area
- Fully responsive — works on desktop and mobile
- Animated typing indicator and message animations
- Prompt suggestion chips on the welcome screen
- Consistent Lucide icons throughout

---

## 🏗️ Architecture

```
insightagent/
├── app/                    # Python backend (FastAPI)
│   ├── main.py             # Routes and endpoints (async)
│   ├── adk_agent.py        # Google ADK agent + Gemini runner
│   ├── tools.py            # ADK tools: web_search, safe_calculate, search_documents_rag
│   ├── rag.py              # RAG pipeline with Qdrant
│   ├── auth.py             # JWT + bcrypt
│   ├── db.py               # SQLAlchemy models (User, Conversation, Message)
│   ├── memory.py           # Conversation history management
│   ├── tts.py              # Text-to-speech (gTTS)
│   ├── utils.py            # Speech-to-text (local Whisper)
│   ├── rate_limit.py       # Rate limiting middleware (Redis)
│   └── requirements.txt
├── frontend/               # React 18 + Vite
│   ├── src/
│   │   ├── App.jsx         # Main component
│   │   └── App.css         # Styles with CSS custom properties
│   └── package.json
├── k8s/                    # Kubernetes manifests
├── .github/workflows/      # CI/CD (GitHub Actions)
├── Dockerfile
└── docker-compose.yml
```

### Full stack

**Backend**
- [FastAPI](https://fastapi.tiangolo.com/) + Uvicorn (async endpoints)
- [Google ADK](https://github.com/google/adk-python) — agent orchestration framework
- Gemini 2.5 Flash — LLM (free tier via Google AI Studio)
- PostgreSQL + SQLAlchemy (conversation persistence)
- [Qdrant](https://qdrant.tech/) (vector database for RAG)
- Redis (cache + rate limiting)
- [Whisper](https://github.com/openai/whisper) `tiny` model (local transcription, no API needed)
- sentence-transformers `all-MiniLM-L6-v2` (document embeddings)

**Frontend**
- React 18 + Vite
- [Lucide React](https://lucide.dev/) (icons)
- Native WebSocket
- Web Audio API (silence detection for voice input)

**Infrastructure**
- Docker + Docker Compose (local dev)
- Kubernetes (production)
- GitHub Actions (CI/CD)

---

## 🤖 How the ADK agent works

The agent is built with [Google ADK](https://github.com/google/adk-python) and uses **Gemini 2.5 Flash** as the underlying model. On each user message, the agent autonomously decides which tools to invoke:

```
User message
     │
     ▼
 LlmAgent (Gemini 2.5 Flash)
     │
     ├── web_search(query)           → Google Custom Search API
     ├── safe_calculate(expression)  → AST-safe math evaluator
     └── search_documents_rag(query) → Qdrant semantic search
     │
     ▼
 Final response
```

Conversation history is stored in PostgreSQL and injected into each ADK session, so the agent retains memory across server restarts.

---

## 🚀 Running locally

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- A [Google AI Studio](https://aistudio.google.com/) API key (free)

### 1. Clone the repository

```bash
git clone https://github.com/carloskafka/insightagent.git
cd insightagent
```

### 2. Set up environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in:

```env
GOOGLE_API_KEY=AIza...          # Google AI Studio key (required)
JWT_SECRET=your-secret-key

# Optional — enables web search tool
GOOGLE_SEARCH_API_KEY=...
GOOGLE_CX=...
```

### 3. Start the containers

```bash
docker compose up --build
```

> On the first run, the Whisper `tiny` model (~72 MB) is downloaded automatically during the build and baked into the image.

### 4. Open in your browser

| Service | URL |
|---|---|
| **Frontend** | http://localhost:3000 |
| **API** | http://localhost:8000 |
| **Swagger UI** | http://localhost:8000/docs |

---

## 📡 API Endpoints

```
POST  /signup              Register a new user
POST  /login               Authenticate (returns JWT)
GET   /me                  Current user profile

POST  /chat                Send a message (handled by ADK agent)
GET   /conversations       List user conversations
GET   /conversations/{id}  Get conversation with messages
DELETE /conversations/{id} Delete a conversation

POST  /upload              Upload document (indexed into RAG)
POST  /voice               Audio → Whisper → ADK agent → response
POST  /tts                 Text → audio (mp3)

POST  /rag/add             Add document to vector index
GET   /rag/search          Semantic search
GET   /search              Google search
GET   /health              Health check
WS    /ws                  Real-time WebSocket
```

---

## ⚙️ Environment variables

| Variable | Description | Default |
|---|---|---|
| `GOOGLE_API_KEY` | Google AI Studio API key (Gemini) | — |
| `JWT_SECRET` | Secret for signing JWT tokens | `supersecretkey` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:password@db:5432/chatbot` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |
| `QDRANT_URL` | Qdrant URL | `http://qdrant:6333` |
| `GOOGLE_SEARCH_API_KEY` | Google Custom Search key (optional) | — |
| `GOOGLE_CX` | Search engine ID (optional) | — |
| `RATE_LIMIT_REQUESTS` | Max requests per window | `10` |
| `RATE_LIMIT_WINDOW` | Rate limit window in seconds | `60` |

---

## 🧪 Tests

```bash
docker compose exec api pytest
```

---

## ☸️ Kubernetes deploy

Manifests available in `k8s/deployment.yaml` with:
- 2 backend replicas
- ConfigMap and Secrets for configuration
- PersistentVolumeClaims for PostgreSQL and Qdrant
- Ingress configured for `chatbot.local`

```bash
kubectl apply -f k8s/deployment.yaml
```

---

## 🔄 CI/CD

The `.github/workflows/deploy.yml` pipeline runs automatically:

1. `pytest` on pull requests
2. Docker image build
3. Push to Docker Hub
4. Deploy to Kubernetes cluster

---

## 📄 License

MIT © [Carlos Kafka](https://github.com/carloskafka)
