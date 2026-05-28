# Production-Grade AI RAG Frontend Workspace

This is a modern, ChatGPT/Perplexity-style conversational AI workspace built specifically for interacting with your streaming RAG pipeline.

## 🚀 Key Features

* **3-Panel Layout**: Collapsible Sidebar (left), Chat Area with metadata stats (center), and RAG Context Panel (right).
* **Document Ingestion Feedback**: Live "Analyzing document..." state matching ChatGPT's document loader UX.
* **Persistent Sessions**: Integrated with the SQLite chat history database.
* **Redis Caching Indicators**: Live cache hit/miss badges showing latency comparison.
* **RAG Diagnostics Console**: Track Faithfulness score, recall latencies, and orchestrator logs in real time.
* **Evaluation Dashboard**: Clean visual charts showing average faithfulness, cache distribution, and latency trends.

---

## 🛠️ Tech Stack

* **Framework**: Next.js 15+ (App Router)
* **Language**: TypeScript
* **Styling**: TailwindCSS
* **State Management**: Zustand
* **Icons**: Lucide React
* **Charts**: Recharts
* **Markdown**: React Markdown

---

## 🏃 Getting Started

### 1. Install dependencies
Navigate to the `frontend` directory and install the packages:
```bash
cd frontend
npm install
```

### 2. Start the development server
```bash
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 🔌 API Connections

The frontend connects directly to your FastAPI endpoints running on `http://localhost:8000`:
* `POST /api/v1/query` — Submits query with history contexts.
* `GET /api/v1/history/{session_id}` — Loads conversation threads.
* `POST /api/v1/hybrid/index` — Ingests and indexes documents in both vector/keyword stores.
