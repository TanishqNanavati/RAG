"""
Standalone script demonstrating Phase 10 Adaptive Retry and Self-Healing Generation.
Tests the orchestrator's ability to retry retrieval strategies when hallucinations are detected.
"""

import os
import sys
import json
import logging
import fitz  # PyMuPDF

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.ingestion.ingestion_service import DocumentIngestionService
from app.services.dense_retrieval.embedding_service import EmbeddingService
from app.services.dense_retrieval.dense_retriever import DenseRetriever
from app.services.bm25_retrieval.bm25_retriever import BM25Retriever
from app.services.hybrid_retrieval.hybrid_retriever import HybridRetriever
from app.services.routing.strategy_router import RuleBasedRouter
from app.services.routing.routing_service import RoutingService, RetrievalPipeline
from app.reranking.reranker import CrossEncoderReRanker
from src.generation.answer_generator import AnswerGenerator
from src.evaluation.evaluator import SelfEvaluator
from app.services.orchestration.orchestrator import AdaptiveRAGOrchestrator

# Filter out verbose HTTP logs to clearly see the orchestration flow
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def create_sample_pdf(pdf_path: str) -> None:
    """Generates a sample PDF on space exploration."""
    doc = fitz.open()

    p1 = doc.new_page()
    p1.insert_text(fitz.Point(50, 50), "SECTION 1: MARS EXPLORATION\nThe Mars Rover Perseverance landed in Jezero Crater to search for signs of ancient microbial life.", fontsize=12)

    p2 = doc.new_page()
    p2.insert_text(fitz.Point(50, 50), "SECTION 2: DEEP SPACE\nThe James Webb Space Telescope (JWST) operates at Lagrange Point 2 and uses infrared instruments to peer through dust clouds.", fontsize=12)

    doc.save(pdf_path)
    doc.close()
    logger.info(f"Created sample PDF at: {pdf_path}")


def main() -> None:
    """Executes the self-healing orchestration test."""
    print("\n" + "="*70)
    print("--- Starting Phase 10 Self-Healing Orchestrator Test ---")
    print("="*70)

    pdf_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "space_exploration_orch.pdf"))
    create_sample_pdf(pdf_file)

    try:
        # 1. Pipeline Initialization
        ingestion_service = DocumentIngestionService(chunk_size=300, overlap=50)
        chunks = ingestion_service.ingest_file(pdf_file)
        
        embedding_service = EmbeddingService()
        dense_retriever = DenseRetriever(embedding_service)
        bm25_retriever = BM25Retriever()
        hybrid_retriever = HybridRetriever(dense_retriever, bm25_retriever)
        rule_router = RuleBasedRouter()
        
        routing_service = RoutingService(dense_retriever, bm25_retriever, hybrid_retriever, rule_router)
        cross_encoder = CrossEncoderReRanker()
        pipeline = RetrievalPipeline(routing_service, reranker=cross_encoder, enable_reranking=True)
        
        # We set evaluator temp to 0.0 for consistent judging
        answer_generator = AnswerGenerator(temperature=0.2)
        self_evaluator = SelfEvaluator(temperature=0.0)

        # 2. Orchestrator Initialization
        # We set a strict faithfulness threshold of 0.8
        orchestrator = AdaptiveRAGOrchestrator(
            retrieval_pipeline=pipeline,
            answer_generator=answer_generator,
            self_evaluator=self_evaluator,
            faithfulness_threshold=0.8,
            max_retries=2
        )

        pipeline.add_documents(chunks)

        # 3. Test Orchestration with multiple queries
        queries = [
            "Where does the James Webb Space Telescope operate?",  # In-context
            "What is the best recipe for baking chocolate chip cookies?"  # Out-of-context
        ]

        for i, query in enumerate(queries, 1):
            print(f"\n\n{'='*50}")
            print(f">>> EXECUTING QUERY {i}: {query}")
            print(f"{'='*50}")
            
            result = orchestrator.execute_query(query, k=5, top_k=2)

            print("\n=== FINAL ORCHESTRATED RESULT ===")
            print(f"WINNING STRATEGY : {result.metadata.selected_strategy.upper()}")
            print(f"TOTAL RETRIES    : {result.metadata.total_retries}")
            print(f"\nANSWER:\n{result.answer}")
            
            print("\nMETADATA LOG:")
            print(json.dumps(result.metadata.model_dump(), indent=2))

    finally:
        if os.path.exists(pdf_file):
            os.remove(pdf_file)
        print("\n--- Orchestrator Test Finished ---")


if __name__ == "__main__":
    main()
