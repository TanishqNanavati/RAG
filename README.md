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
