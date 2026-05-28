"""
Standalone script demonstrating Phase 9 Self-Evaluation and Verification on a multi-page PDF.
Shows evaluation on a properly grounded answer and an intentionally hallucinated answer.
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
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
    """Executes full RAG pipeline and performs self-evaluation on the output."""
    logger.info("--- Starting Phase 9 Self-Evaluation Test ---")

    pdf_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "space_exploration_eval.pdf"))
    create_sample_pdf(pdf_file)

    try:
        # 1. Ingestion
        ingestion_service = DocumentIngestionService(chunk_size=300, overlap=50)
        chunks = ingestion_service.ingest_file(pdf_file)
        
        # 2. Pipeline Init
        embedding_service = EmbeddingService()
        dense_retriever = DenseRetriever(embedding_service)
        bm25_retriever = BM25Retriever()
        hybrid_retriever = HybridRetriever(dense_retriever, bm25_retriever)
        rule_router = RuleBasedRouter()
        
        routing_service = RoutingService(dense_retriever, bm25_retriever, hybrid_retriever, rule_router)
        cross_encoder = CrossEncoderReRanker()
        pipeline = RetrievalPipeline(routing_service, reranker=cross_encoder, enable_reranking=True)
        
        answer_generator = AnswerGenerator(temperature=0.2)
        evaluator = SelfEvaluator(temperature=0.0)

        # Index
        pipeline.add_documents(chunks)

        query = "Where does the JWST operate and what does it do?"
        logger.info(f"\n==================================================")
        logger.info(f'Executing TEST 1: Valid Grounded Generation')
        logger.info(f"==================================================")

        # Retrieve, Rerank, Generate
        pipeline_res = pipeline.search(query, k=5, top_k=2)
        gen_result = answer_generator.generate_answer(query, pipeline_res.results)
        
        logger.info("\n--- GENERATED ANSWER ---")
        logger.info(gen_result.answer)
        
        # Evaluate
        eval_result = evaluator.evaluate(query, gen_result.answer, gen_result.citations)
        logger.info("\n--- EVALUATION REPORT ---")
        logger.info(json.dumps(eval_result.model_dump(), indent=2))


        logger.info(f"\n==================================================")
        logger.info(f'Executing TEST 2: Intentionally Hallucinated Answer')
        logger.info(f"==================================================")
        
        hallucinated_answer = "The James Webb Space Telescope operates in low Earth orbit alongside the Hubble telescope [1]. It was launched by SpaceX in 2024 and primarily searches for alien mega-structures [2]."
        
        logger.info("\n--- HALLUCINATED ANSWER ---")
        logger.info(hallucinated_answer)
        
        eval_result_hallucination = evaluator.evaluate(query, hallucinated_answer, gen_result.citations)
        logger.info("\n--- EVALUATION REPORT (EXPECTING LOW SCORES) ---")
        logger.info(json.dumps(eval_result_hallucination.model_dump(), indent=2))

    finally:
        if os.path.exists(pdf_file):
            os.remove(pdf_file)
        logger.info("\n--- Evaluation Test Finished ---")


if __name__ == "__main__":
    main()
