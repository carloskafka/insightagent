# 🤖 InsightAgent

> Full-stack AI chat platform for learning agentic development with Python.

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
| 💬 **AI Chat** | Natural language conversations through a custom Python agent runtime |
| 🤖 **Agentic Tools** | Agent decides when to search the web, calculate, or use retrieved document context |
| 🎤 **Voice Input** | Speech-to-text endpoint for voice-based interaction |
| 🔊 **Text-to-Speech** | Read any message aloud with one click |
| 📄 **RAG** | Document upload with semantic search via Qdrant + sentence-transformers |
| 🔍 **Web Search** | Google Custom Search integration available to the platform |
| 🧮 **Calculator** | Safe expression evaluation inside the agent flow |
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
│   ├── agents/            # Agent orchestration and runtime logic
│   ├── core/              # Config, security, database, factory, middleware
│   ├── integrations/      # External providers and infrastructure adapters
│   ├── models/            # SQLAlchemy entities
│   ├── repositories/      # Persistence logic
│   ├── routers/           # FastAPI route modules
│   ├── schemas/           # Request/response models
│   ├── services/          # Application and use-case logic
│   ├── adk_agent.py       # Experimental Google ADK agent module
│   ├── main.py            # ASGI entrypoint
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
- Custom Python agent runtime under `app/agents/`
- [Google ADK](https://github.com/google/adk-python) experimental module kept in `app/adk_agent.py`
- OpenRouter-backed LLM integration
- PostgreSQL + SQLAlchemy (conversation persistence)
- [Qdrant](https://qdrant.tech/) (vector database for RAG)
- Redis (cache + rate limiting)
- SpeechRecognition-based transcription endpoint
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

## 🤖 How the Agent Works

The main chat flow currently uses the custom runtime in `app/agents/runtime.py`. On each user message, the backend decides between a few simple capabilities before falling back to the LLM:

```
User message
     │
     ▼
 Python agent runtime
     │
     ├── search handling              → Google Custom Search
     ├── math handling                → safe evaluation
     ├── RAG context lookup           → Qdrant semantic search
     └── fallback generation          → LLM response
     │
     ▼
 Final response
```

There is also an `app/adk_agent.py` module in the repository as part of my ongoing learning process with Google ADK, but it is not the primary runtime path used by `app.main` today.

---

## 🚀 Running locally

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- API keys depending on which integrations you want to enable

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
OPENROUTER_API_KEY=...          # Main LLM integration
JWT_SECRET=your-secret-key

# Optional — enables web search tool
GOOGLE_SEARCH_API_KEY=...
GOOGLE_CX=...
```

If you want to experiment with the separate `app/adk_agent.py` module, you can also provide:

```env
GOOGLE_API_KEY=...
```

### 3. Start the containers

```bash
docker compose up --build
```

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

POST  /chat                Send a message through the agent runtime
GET   /conversations       List user conversations
GET   /conversations/{id}  Get conversation with messages
DELETE /conversations/{id} Delete a conversation

POST  /upload              Upload document (indexed into RAG)
POST  /voice               Audio → speech-to-text → agent → response
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
| `OPENROUTER_API_KEY` | Main LLM provider key | — |
| `GOOGLE_API_KEY` | Optional key for the experimental ADK module | — |
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
pytest -q
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
