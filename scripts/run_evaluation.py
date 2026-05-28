"""
Runner script for the Offline Evaluation Framework (Phase 13).
Executes the RAG pipeline over a batch dataset and outputs evaluation metrics.
"""

import os
import sys
import json
import logging
import argparse
import fitz

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.services.ingestion.ingestion_service import DocumentIngestionService
from app.api.orchestration_routes import orchestrator, pipeline
from src.benchmark.evaluator_runner import BenchmarkRunner
from src.benchmark.models import BenchmarkDatasetItem

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def create_sample_pdf(pdf_path: str, num_facts: int = 100) -> None:
    doc = fitz.open()
    facts_per_page = 10
    total_pages = (num_facts + facts_per_page - 1) // facts_per_page
    
    for page_idx in range(total_pages):
        page = doc.new_page()
        y = 50
        for i in range(facts_per_page):
            fact_id = page_idx * facts_per_page + i + 1
            if fact_id > num_facts:
                break
            text = f"SECTION {fact_id}: FACT_{fact_id}.\nThe secret keyword for this section is ALPHA_{fact_id} and its associated value is {fact_id * 100}."
            page.insert_text(fitz.Point(50, y), text, fontsize=10)
            y += 40
    doc.save(pdf_path)
    doc.close()


def create_sample_dataset(dataset_path: str, chunks: list, num_facts: int = 100) -> None:
    dataset = []
    
    # Map facts to the specific chunk ID they ended up in
    chunk_map = {}
    for c in chunks:
        text = getattr(c, "text", "") if hasattr(c, "text") else c.get("text", "")
        c_id = getattr(c, "id", "") if hasattr(c, "id") else c.get("id", "")
        
        for i in range(1, num_facts + 1):
            if f"ALPHA_{i}" in text:
                chunk_map[i] = c_id

    # Generate 100 valid queries
    for i in range(1, num_facts + 1):
        chunk_id = chunk_map.get(i, "")
        dataset.append({
            "id": f"q{i}",
            "query": f"What is the associated value for the secret keyword ALPHA_{i}?",
            "ground_truth_answer": f"The value for ALPHA_{i} is {i * 100}.",
            "expected_keywords": [f"ALPHA_{i}", str(i * 100)],
            "expected_chunk_ids": [chunk_id] if chunk_id else []
        })
        
    # Inject a few out-of-context "hallucination-trap" queries at the end
    dataset.append({
        "id": "q101",
        "query": "What is the capital of France?",
        "ground_truth_answer": "I do not know.",
        "expected_keywords": [],
        "expected_chunk_ids": []
    })
    
    with open(dataset_path, "w") as f:
        json.dump(dataset, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="RAG Offline Evaluation Runner")
    parser.add_argument("--dataset", type=str, default="evaluations/datasets/sample_dataset.json", help="Path to evaluation dataset")
    parser.add_argument("--output-dir", type=str, default="evaluations", help="Directory to save reports")
    args = parser.parse_args()

    print("\n" + "="*70)
    print("--- Starting Phase 13 Offline Benchmark Runner ---")
    print("="*70)

    os.makedirs(os.path.dirname(args.dataset), exist_ok=True)
    pdf_file = os.path.join(os.path.dirname(args.dataset), "eval_docs.pdf")

    try:
        if orchestrator is None:
            print("ERROR: Orchestrator failed to initialize.")
            sys.exit(1)

        print("\n[INFO] Ingesting documents to populate vector DB...")
        create_sample_pdf(pdf_file)
        ingestion_service = DocumentIngestionService(chunk_size=300, overlap=50)
        chunks = ingestion_service.ingest_file(pdf_file)
        pipeline.add_documents(chunks)

        print(f"[INFO] Generating sample dataset at {args.dataset}...")
        create_sample_dataset(args.dataset, chunks)

        with open(args.dataset, "r") as f:
            raw_data = json.load(f)
            dataset = [BenchmarkDatasetItem(**item) for item in raw_data]

        print("\n[INFO] Initializing Benchmark Runner...")
        runner = BenchmarkRunner(orchestrator)
        
        print(f"\n[INFO] Executing Pipeline for {len(dataset)} queries. This may take a moment...\n")
        summary = runner.run_benchmark(dataset, output_dir=args.output_dir)

        print("\n" + "="*70)
        print("--- BENCHMARK SUMMARY ---")
        print("="*70)
        print(json.dumps(summary.model_dump(), indent=2))
        print(f"\nDetailed reports saved to: {args.output_dir}/reports/ and {args.output_dir}/results/")

    finally:
        if os.path.exists(pdf_file):
            os.remove(pdf_file)

if __name__ == "__main__":
    main()
