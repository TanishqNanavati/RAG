"""
Test script utilizing FastAPI TestClient to demonstrate the Phase 11 Full RAG API endpoints.
It sets up the pipeline, indexes a PDF, and calls the API endpoints.
"""

import os
import sys
import json
import logging
from fastapi.testclient import TestClient
import fitz  # PyMuPDF

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import the fully initialized FastAPI app
from app.main import app

# We need the ingestion service to inject initial test data
from app.services.ingestion.ingestion_service import DocumentIngestionService
from app.api.orchestration_routes import pipeline

logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

client = TestClient(app)

def create_sample_pdf(pdf_path: str) -> None:
    doc = fitz.open()
    p1 = doc.new_page()
    p1.insert_text(fitz.Point(50, 50), "SECTION 1: MARS\nThe Perseverance Rover landed on Mars to hunt for signs of ancient life.", fontsize=12)
    p2 = doc.new_page()
    p2.insert_text(fitz.Point(50, 50), "SECTION 2: JWST\nThe James Webb Space Telescope uses powerful infrared instruments at Lagrange Point 2.", fontsize=12)
    doc.save(pdf_path)
    doc.close()

def main():
    print("\n" + "="*70)
    print("--- Starting Phase 11 FastAPI Endpoint Tests ---")
    print("="*70)

    pdf_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "api_test.pdf"))
    create_sample_pdf(pdf_file)

    try:
        print("\n[INFO] Ingesting documents directly into pipeline index...")
        ingestion_service = DocumentIngestionService(chunk_size=300, overlap=50)
        chunks = ingestion_service.ingest_file(pdf_file)
        pipeline.add_documents(chunks)
        print("[INFO] Indexing complete.\n")

        # ---------------------------------------------------------
        # TEST 1: POST /api/v1/query (Valid Grounded Query)
        # ---------------------------------------------------------
        print(f"{'='*60}\n>>> EXECUTING POST /api/v1/query\n{'='*60}")
        query1 = {"query": "What instruments does the JWST use?"}
        
        response1 = client.post("/api/v1/query", json=query1)
        if response1.status_code == 200:
            print("HTTP 200 OK")
            print(json.dumps(response1.json(), indent=2))
        else:
            print(f"FAILED: {response1.status_code} - {response1.text}")

        # ---------------------------------------------------------
        # TEST 2: POST /api/v1/debug (Hallucination Prevention/Retry logic)
        # ---------------------------------------------------------
        print(f"\n\n{'='*60}\n>>> EXECUTING POST /api/v1/debug (Out-of-Context Query)\n{'='*60}")
        query2 = {"query": "How do I build a time machine?"}
        
        response2 = client.post("/api/v1/debug", json=query2)
        if response2.status_code == 200:
            print("HTTP 200 OK")
            print(json.dumps(response2.json(), indent=2))
        else:
            print(f"FAILED: {response2.status_code} - {response2.text}")

        # ---------------------------------------------------------
        # TEST 3: GET /api/v1/health
        # ---------------------------------------------------------
        print(f"\n\n{'='*60}\n>>> EXECUTING GET /api/v1/health\n{'='*60}")
        response3 = client.get("/api/v1/health")
        if response3.status_code == 200:
            print("HTTP 200 OK")
            print(json.dumps(response3.json(), indent=2))
        else:
            print(f"FAILED: {response3.status_code} - {response3.text}")

    finally:
        if os.path.exists(pdf_file):
            os.remove(pdf_file)
        print("\n--- API Layer Test Finished ---")

if __name__ == "__main__":
    main()
