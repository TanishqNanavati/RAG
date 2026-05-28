# RAG Workspace — AI Document Intelligence

> **Production-grade, multi-turn RAG system** with adaptive retrieval, semantic caching, self-healing orchestration, and a premium Next.js frontend with JWT authentication.

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat&logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-15-black?style=flat&logo=next.js&logoColor=white)
![Qdrant](https://img.shields.io/badge/Qdrant-VectorDB-DC143C?style=flat)
![Redis](https://img.shields.io/badge/Redis-Cache-DC382D?style=flat&logo=redis&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green?style=flat)

---

## ✨ Features

| Feature | Description |
|---|---|
| **Multi-Strategy Retrieval** | BM25, Dense (Qdrant), and Hybrid — switchable per query |
| **Adaptive Orchestration** | Self-healing pipeline retries with alternate strategy on low-quality answers |
| **2-Stage Re-Ranking** | Broad recall (k=10) → CrossEncoder precision rerank (top_k=3) |
| **Semantic Cache** | Redis cache keyed on `query + strategy` to skip redundant LLM calls |
| **Multi-Turn Conversations** | LLM-powered query rewriting for contextual follow-ups |
| **User Authentication** | JWT auth with per-user chat session isolation |
| **Strategy Comparison** | Side-by-side BM25 vs Dense vs Hybrid analysis with pie charts |
| **Self-Evaluation** | LLM-as-a-Judge faithfulness & citation scoring on every answer |
| **Document Ingestion** | PDF, TXT, MD, DOCX, PPTX — chunked, embedded, and dual-indexed |
| **User Profile & Stats** | Per-user query count, session count, and RAG performance metrics |

---

## 🏗 Architecture

```
User Query
    │
    ▼
Query Rewriter (LLM-powered, uses conversation history)
    │
    ▼
Redis Semantic Cache ─── HIT ──▶ Return Cached Response
    │ MISS
    ▼
Adaptive RAG Orchestrator
    │
    ├── Strategy: bm25 / dense / hybrid / auto
    ▼
RetrievalPipeline — Stage 1: Recall (k=10)
    ├── BM25Retriever       (sparse, keyword)
    ├── DenseRetriever      (Qdrant, semantic)
    └── HybridRetriever     (RRF score fusion)
    │
    ▼
CrossEncoder Re-Ranker — Stage 2: Precision (top_k=3)
    │
    ▼
Confidence Analyzer ─── LOW ──▶ "Not available in documents"
    │ HIGH
    ▼
AnswerGenerator (Gemini / OpenAI-compatible API)
    │
    ▼
SelfEvaluator (Faithfulness + Citation Score)
    │
    ├── PASS ──▶ Cache & Return Answer
    └── FAIL ──▶ Retry with alternate strategy (max 2 retries)
```

**Stack:**

| Layer | Technology |
|---|---|
| Backend | FastAPI, SQLAlchemy, SQLite, uvicorn |
| Vector DB | Qdrant (Docker) |
| Cache | Redis (Docker) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (local) |
| Reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2` (local) |
| LLM | Gemini via OpenAI-compatible API |
| Frontend | Next.js 15, TypeScript, Tailwind CSS, Zustand |

---

## 📦 Project Structure

```
rag/
├── app/
│   ├── main.py                      # FastAPI entrypoint & lifecycle
│   ├── api/
│   │   ├── auth_routes.py           # /register, /login, /me, /me/stats
│   │   ├── orchestration_routes.py  # /query, /sessions, /history
│   │   └── ingestion_routes.py      # /ingest
│   ├── core/                        # config.py, db.py, security.py
│   ├── models/                      # User, ChatSession, ChatMessage
│   └── services/
│       ├── orchestration/           # AdaptiveRAGOrchestrator, ConversationManager
│       ├── dense_retrieval/         # Qdrant embedding + vector search
│       ├── bm25_retrieval/          # BM25Okapi sparse retrieval
│       ├── hybrid_retrieval/        # RRF score fusion
│       ├── routing/                 # Strategy router + RetrievalPipeline
│       └── cache/                   # RedisSemanticCache
├── src/
│   ├── generation/                  # AnswerGenerator + prompt templates
│   └── evaluation/                  # SelfEvaluator (LLM-as-a-judge)
├── frontend/
│   └── src/
│       ├── components/              # Sidebar, ChatArea, ContextPanel, etc.
│       ├── store/useChatStore.ts    # Zustand global state
│       └── services/api.ts          # All backend API calls
├── scripts/                         # CLI test scripts
├── docker-compose.yml               # Qdrant + Redis services
├── requirements.txt
├── .env.example                     # Environment variable template
└── run.sh                           # One-command startup script
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- Docker & Docker Compose (for Qdrant & Redis)
- A [Gemini API key](https://aistudio.google.com/app/apikey)

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/TanishqNanavati/RAG.git
cd RAG

# 2. Configure environment
cp .env.example .env
# Edit .env — fill in GEMINI_API_KEY and generate a JWT_SECRET:
# python -c "import secrets; print(secrets.token_hex(32))"

# 3. Python virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 4. Frontend dependencies
cd frontend && npm install && cd ..

# 5. Start everything
chmod +x run.sh
./run.sh
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3005 |
| Backend API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |

> **Note:** `run.sh` automatically starts Docker (Qdrant + Redis), the FastAPI backend with hot-reload, and the Next.js dev server.

---

## ⚙️ Environment Variables

Copy `.env.example` to `.env` and fill in the required values:

| Variable | Required | Default | Description |
|---|---|---|---|
| `GEMINI_API_KEY` | ✅ | — | Gemini API key |
| `JWT_SECRET` | ✅ | — | JWT signing secret (generate a random hex) |
| `GEMINI_MODEL` | | `gemini-2.0-flash` | LLM model name |
| `OPENAI_BASE_URL` | | Gemini endpoint | OpenAI-compatible base URL |
| `QDRANT_URL` | | `http://localhost:6333` | Qdrant vector DB URL |
| `QDRANT_COLLECTION` | | `rag_chunks` | Collection name |
| `REDIS_HOST` | | `localhost` | Redis host |
| `DATABASE_URL` | | `sqlite:///./rag.db` | Database path |
| `EMBEDDING_MODEL` | | `all-MiniLM-L6-v2` | Sentence transformer model |
| `RERANK_MODEL` | | `cross-encoder/ms-marco-MiniLM-L-6-v2` | CrossEncoder reranker |

---

## 🔌 API Reference

> Full interactive docs at `http://localhost:8000/docs`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/v1/auth/register` | — | Register new user |
| `POST` | `/api/v1/auth/login` | — | Login, returns JWT token |
| `GET` | `/api/v1/auth/me` | 🔒 | Current user info |
| `GET` | `/api/v1/auth/me/stats` | 🔒 | User query & RAG statistics |
| `POST` | `/api/v1/ingest` | 🔒 | Upload & index a document |
| `POST` | `/api/v1/query` | 🔒 | Run RAG query (`strategy`: `bm25`/`dense`/`hybrid`/`auto`) |
| `GET` | `/api/v1/sessions` | 🔒 | List all user's chat sessions |
| `PUT` | `/api/v1/sessions/{id}` | 🔒 | Rename a session |
| `GET` | `/api/v1/history/{session_id}` | 🔒 | Get messages for a session |
| `POST` | `/api/v1/compare` | 🔒 | Compare strategies on a single query |

**Query payload example:**
```json
{
  "query": "What is Node.js?",
  "session_id": "session_abc123",
  "strategy": "hybrid"
}
```

---

## 🛠 Development

```bash
# Backend only (hot-reload)
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Frontend only
cd frontend && npm run dev

# Type-check frontend
cd frontend && npx tsc --noEmit

# Start only Docker services
docker-compose up -d

# Run a test script (example)
python scripts/test_hybrid_retrieval.py
```

---

## 🧠 How It Works

1. **Ingest** — Upload a document → parsed, chunked, embedded (`all-MiniLM-L6-v2`), stored in Qdrant (vector) and BM25 index (sparse).
2. **Query** — User sends a question with a chosen strategy. If a prior conversation exists, the query is rewritten by an LLM to be standalone.
3. **Cache** — A Redis lookup is performed using `query + strategy` as the key. Cache hit → instant response.
4. **Retrieve** — The selected strategy fetches top-k chunks. Hybrid uses Reciprocal Rank Fusion (RRF) to merge BM25 + dense scores.
5. **Rerank** — A CrossEncoder scores all retrieved chunks against the query; top-3 are kept.
6. **Generate** — The LLM generates a grounded answer with inline citations.
7. **Evaluate** — A second LLM call scores faithfulness and citation accuracy. If below threshold, the orchestrator retries with a different strategy.

---

## 📄 License

MIT © [Tanishq Nanavati](https://github.com/TanishqNanavati)
