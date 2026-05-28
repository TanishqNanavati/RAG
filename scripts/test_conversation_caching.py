import sys
import os
import time
import logging

# Add project root to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app
from app.api.orchestration_routes import pipeline
from app.services.ingestion.ingestion_service import DocumentIngestionService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = TestClient(app)

def run_test():
    # 1. Generate a test PDF
    print("\n--- Generating test PDF ---")
    import fitz
    os.makedirs("evaluations/datasets", exist_ok=True)
    pdf_path = "evaluations/datasets/caching_test.pdf"
    doc = fitz.open()
    for i in range(1, 11):
        page = doc.new_page()
        text = f"This is page {i} of the special report.\nThe secret key for page {i} is ALPHA_{i}.\n"
        page.insert_text(fitz.Point(50, 50), text, fontsize=12)
    doc.save(pdf_path)
    doc.close()
    print(f"Generated PDF at {pdf_path}")

    # 2. Ingest the document directly into the orchestration pipeline's memory
    print("\n--- Ingesting document into orchestration pipeline memory ---")
    ingestion_service = DocumentIngestionService(chunk_size=300, overlap=50)
    # Stream and add
    total_chunks = 0
    for chunk_batch in ingestion_service.ingest_file_in_batches(pdf_path, batch_size=50):
        pipeline.add_documents(chunk_batch)
        total_chunks += len(chunk_batch)
    print(f"Successfully indexed {total_chunks} chunks.")

    session_id = "test-session-redis-cache"

    # Query 1: First turn (Cache Miss, Saved to DB)
    q1 = "What is the secret key for page 3?"
    print(f"\n=======================================================")
    print(f"QUERY 1: {q1} (Expect: Cache Miss, RAG pipeline executes)")
    print(f"=======================================================")
    t0 = time.time()
    resp1 = client.post("/api/v1/query", json={"query": q1, "session_id": session_id})
    d1 = resp1.json()
    print(f"ANSWER: {d1['answer']}")
    print(f"IS CACHED: {d1.get('is_cached')}")
    print(f"STRATEGY USED: {d1.get('strategy_used')}")
    print(f"LATENCY: {time.time() - t0:.2f}s")

    # Query 2: Repeated Turn (Cache Hit)
    print(f"\n=======================================================")
    print(f"QUERY 2: {q1} (Expect: Cache Hit from Redis or fallback, extremely fast)")
    print(f"=======================================================")
    t0 = time.time()
    resp2 = client.post("/api/v1/query", json={"query": q1, "session_id": session_id})
    d2 = resp2.json()
    print(f"ANSWER: {d2['answer']}")
    print(f"IS CACHED: {d2.get('is_cached')}")
    print(f"LATENCY: {time.time() - t0:.4f}s")

    # Query 3: Follow-up Turn (Expect Query Rewriting context translation)
    q3 = "What about page 8?"
    print(f"\n=======================================================")
    print(f"QUERY 3: {q3} (Expect: Context translation query rewrite using DB history)")
    print(f"=======================================================")
    t0 = time.time()
    resp3 = client.post("/api/v1/query", json={"query": q3, "session_id": session_id})
    d3 = resp3.json()
    print(f"ANSWER: {d3['answer']}")
    print(f"IS CACHED: {d3.get('is_cached')}")
    print(f"LATENCY: {time.time() - t0:.2f}s")

    # Query 4: Check Session History API
    print(f"\n=======================================================")
    print(f"QUERY 4: Retrieving Session History from SQLite DB")
    print(f"=======================================================")
    resp4 = client.get(f"/api/v1/history/{session_id}")
    history = resp4.json()
    for msg in history:
        print(f"  [{msg['role'].upper()}]: {msg['content']}")

if __name__ == "__main__":
    run_test()
