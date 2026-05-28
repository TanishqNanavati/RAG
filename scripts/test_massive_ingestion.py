import fitz
import os
import sys
import time
import logging

# Add project root to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.services.dense_retrieval.dense_retriever import DenseRetriever
from app.services.dense_retrieval.embedding_service import EmbeddingService
from app.services.bm25_retrieval.bm25_retriever import BM25Retriever
from app.services.hybrid_retrieval.hybrid_retriever import HybridRetriever
from app.services.routing.routing_service import RoutingService, RetrievalPipeline
from app.services.ingestion.ingestion_service import DocumentIngestionService
from app.reranking.reranker import CrossEncoderReRanker

from src.generation.answer_generator import AnswerGenerator
from src.evaluation.evaluator import SelfEvaluator
from src.retrieval_filtering.confidence_analyzer import RetrievalConfidenceAnalyzer
from app.services.orchestration.orchestrator import AdaptiveRAGOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_1000_page_pdf(pdf_path: str):
    logger.info(f"Generating 1,000-page PDF at {pdf_path}...")
    doc = fitz.open()
    for i in range(1, 1001):
        page = doc.new_page()
        text = f"This is page {i} of the massive document.\nThe highly confidential secret code for page {i} is OMEGA_{i}.\nAccess is restricted to level {i % 5} personnel."
        page.insert_text(fitz.Point(50, 50), text, fontsize=12)
    doc.save(pdf_path)
    doc.close()
    logger.info("PDF generation complete.")

def main():
    os.makedirs("evaluations/datasets", exist_ok=True)
    pdf_path = "evaluations/datasets/massive_1000_pages.pdf"
    
    if not os.path.exists(pdf_path):
        create_1000_page_pdf(pdf_path)

    logger.info("Initializing Retrieval Pipeline...")
    embedding_service = EmbeddingService()
    dense_retriever = DenseRetriever(embedding_service)
    
    bm25_retriever = BM25Retriever()
    
    hybrid_retriever = HybridRetriever(dense_retriever=dense_retriever, bm25_retriever=bm25_retriever)
    routing_service = RoutingService(dense_retriever, bm25_retriever, hybrid_retriever)
    reranker = CrossEncoderReRanker()
    pipeline = RetrievalPipeline(routing_service=routing_service, reranker=reranker)

    ingestion_service = DocumentIngestionService(chunk_size=300, overlap=50)

    # STREAMING INGESTION TEST
    logger.info("--- Starting Streaming Ingestion ---")
    start_time = time.time()
    
    batch_count = 0
    total_chunks = 0
    
    # Stream in batches of 200 chunks (safe memory footprint)
    for chunk_batch in ingestion_service.ingest_file_in_batches(pdf_path, batch_size=200):
        batch_count += 1
        total_chunks += len(chunk_batch)
        logger.info(f"Processing Batch {batch_count} | Chunks in batch: {len(chunk_batch)} | Total chunks so far: {total_chunks}")
        pipeline.add_documents(chunk_batch)
        
    ingestion_time = time.time() - start_time
    logger.info(f"--- Streaming Ingestion Complete in {ingestion_time:.2f}s ---")
    logger.info(f"Total chunks ingested safely: {total_chunks}")

    logger.info("Initializing Orchestrator for querying...")
    generator = AnswerGenerator()
    evaluator = SelfEvaluator()
    
    orchestrator = AdaptiveRAGOrchestrator(
        retrieval_pipeline=pipeline,
        answer_generator=generator,
        self_evaluator=evaluator
    )

    test_queries = [
        "What is the highly confidential secret code for page 42?",
        "What is the highly confidential secret code for page 999?",
        "What personnel access level is required for page 500?"
    ]

    for q in test_queries:
        print(f"\n=======================================================")
        print(f"QUERY: {q}")
        print(f"=======================================================")
        res = orchestrator.execute_query(q)
        print(f"\nANSWER:\n{res.answer}")
        print(f"\nSTRATEGY USED: {res.metadata.selected_strategy}")
        print(f"RETRIEVAL LATENCY: {res.metadata.attempts[-1].pipeline_ms}ms")
        print(f"FAITHFULNESS SCORE: {res.evaluation.faithfulness_score}")
        print(f"=======================================================\n")

if __name__ == "__main__":
    main()
