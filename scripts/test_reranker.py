"""
Standalone script demonstrating Phase 7 Cross-Encoder Re-Ranking on a multi-page PDF document.
Uses PyMuPDF to generate a sample PDF, executes Stage-1 recall retrieval, compares chunk ordering
before and after Stage-2 Cross-Encoder re-ranking, and demonstrates the enable_reranking toggle.
"""

import os
import sys
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def create_sample_pdf(pdf_path: str) -> None:
    """Generates a 3-page sample PDF on space exploration using PyMuPDF."""
    doc = fitz.open()

    # Page 1 - Mars
    p1 = doc.new_page()
    p1.insert_text(fitz.Point(50, 50), "SECTION 1: MARS EXPLORATION\nThe Mars Rover Perseverance successfully landed in Jezero Crater. Its primary mission is to search for signs of ancient microbial life and collect rock core samples for future return to Earth.", fontsize=12)

    # Page 2 - JWST
    p2 = doc.new_page()
    p2.insert_text(fitz.Point(50, 50), "SECTION 2: DEEP SPACE OBSERVATION\nThe James Webb Space Telescope (JWST) operates at Lagrange Point 2. Equipped with advanced infrared instruments, JWST captures breathtaking images of the early universe, exoplanet atmospheres, and star formation. Unlike Hubble which observes primarily in optical and ultraviolet, JWST is optimized for infrared observation to peer through dense dust clouds.", fontsize=12)

    # Page 3 - Artemis
    p3 = doc.new_page()
    p3.insert_text(fitz.Point(50, 50), "SECTION 3: LUNAR MISSIONS\nThe Artemis II mission will carry four astronauts around the Moon. This crewed flight test paves the way for establishing a sustainable human presence on the lunar surface and preparing for future human missions to Mars.", fontsize=12)

    doc.save(pdf_path)
    doc.close()
    logger.info(f"Created 3-page sample PDF at: {pdf_path}")


def main() -> None:
    """Executes the re-ranking test workflow and compares chunk ordering before/after CrossEncoder scoring."""
    logger.info("--- Starting Multi-Page PDF Cross-Encoder Re-Ranking Test ---")

    pdf_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "space_exploration_rerank.pdf"))
    create_sample_pdf(pdf_file)

    try:
        # 1. Phase 2 Ingestion: Load and chunk PDF document
        ingestion_service = DocumentIngestionService(chunk_size=300, overlap=50)
        chunks = ingestion_service.ingest_file(pdf_file)
        logger.info(f"Ingestion produced {len(chunks)} chunks from PDF.")

        # 2. Initialize Retrievers, Router, RoutingService, and ReRanker
        embedding_service = EmbeddingService()
        dense_retriever = DenseRetriever(embedding_service)
        bm25_retriever = BM25Retriever()
        hybrid_retriever = HybridRetriever(dense_retriever, bm25_retriever)
        rule_router = RuleBasedRouter()
        
        routing_service = RoutingService(dense_retriever, bm25_retriever, hybrid_retriever, rule_router)
        cross_encoder = CrossEncoderReRanker()

        # 3. Initialize Two-Stage RetrievalPipeline (with reranking enabled)
        pipeline = RetrievalPipeline(routing_service, reranker=cross_encoder, enable_reranking=True)

        # Index documents
        total_indexed = pipeline.add_documents(chunks)
        logger.info(f"Successfully indexed {total_indexed} chunks.")

        # 4. Test Queries demonstrating re-ordering
        queries = [
            "How does JWST differ from Hubble?",
            "Compare Apollo and Artemis missions",
            "What technologies support lunar exploration?"
        ]

        for query in queries:
            logger.info(f"\n==================================================")
            logger.info(f'Executing Query: "{query}"')
            logger.info(f"==================================================")

            # A. Stage-1 Recall Search (Bypassing Re-Ranker to see initial order)
            stage1_res = routing_service.search(query, k=5)
            logger.info("\n--- BEFORE RE-RANKING (Stage-1 Recall Order) ---")
            for i, res in enumerate(stage1_res.results, 1):
                logger.info(f"[{i}] Chunk ID: {res.id} | Stage-1 Score: {res.score:.4f} | Page: {res.metadata.page}")
                logger.info(f"    Snippet: {res.text[:90]}...")

            # B. Stage-2 Precision Search (With CrossEncoder Re-Ranking)
            pipeline_res = pipeline.search(query, k=5, top_k=3)
            logger.info("\n--- AFTER CROSS-ENCODER RE-RANKING (Stage-2 Precision Order) ---")
            for i, res in enumerate(pipeline_res.results, 1):
                logger.info(f"[{i}] Chunk ID: {res.id} | ReRank Score: {res.rerank_score:.4f} | Stage-1 Score: {res.score:.4f} | Page: {res.metadata.page}")
                logger.info(f"    Snippet: {res.text[:90]}...")

        # 5. Demonstrate Toggle OFF
        logger.info(f"\n==================================================")
        logger.info("Demonstrating Toggle OFF (enable_reranking=False)")
        logger.info(f"==================================================")
        pipeline_disabled = RetrievalPipeline(routing_service, reranker=cross_encoder, enable_reranking=False)
        off_res = pipeline_disabled.search("How does JWST differ from Hubble?", k=5, top_k=3)
        for i, res in enumerate(off_res.results, 1):
            logger.info(f"[{i}] Chunk ID: {res.id} | ReRank Score: {res.rerank_score} | Stage-1 Score: {res.score:.4f}")

    finally:
        # Clean up sample PDF file
        if os.path.exists(pdf_file):
            os.remove(pdf_file)
        logger.info("\n--- Re-Ranking Test Finished & Cleaned Up ---")


if __name__ == "__main__":
    main()
