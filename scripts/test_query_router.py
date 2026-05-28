"""
Standalone script demonstrating Phase 6 Intelligent Query Routing on a multi-page PDF document.
Uses PyMuPDF to generate a sample PDF, indexes it via RoutingService, and executes
various query types (short factual, semantic, complex comparative) to verify dynamic routing.
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
from app.services.routing.routing_service import RoutingService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def create_sample_pdf(pdf_path: str) -> None:
    """Generates a 3-page sample PDF on space exploration using PyMuPDF."""
    doc = fitz.open()

    # Page 1
    p1 = doc.new_page()
    p1.insert_text(fitz.Point(50, 50), "SECTION 1: MARS EXPLORATION\nThe Mars Rover Perseverance successfully landed in Jezero Crater. Its primary mission is to search for signs of ancient microbial life and collect rock core samples for future return to Earth.", fontsize=12)

    # Page 2
    p2 = doc.new_page()
    p2.insert_text(fitz.Point(50, 50), "SECTION 2: DEEP SPACE OBSERVATION\nThe James Webb Space Telescope (JWST) operates at Lagrange Point 2. Equipped with advanced infrared instruments, JWST captures breathtaking images of the early universe, exoplanet atmospheres, and star formation.", fontsize=12)

    # Page 3
    p3 = doc.new_page()
    p3.insert_text(fitz.Point(50, 50), "SECTION 3: LUNAR MISSIONS\nThe Artemis II mission will carry four astronauts around the Moon. This crewed flight test paves the way for establishing a sustainable human presence on the lunar surface and preparing for future human missions to Mars.", fontsize=12)

    doc.save(pdf_path)
    doc.close()
    logger.info(f"Created 3-page sample PDF at: {pdf_path}")


def main() -> None:
    """Executes the query routing test workflow across multiple distinct query types."""
    logger.info("--- Starting Multi-Page PDF Intelligent Query Routing Test ---")

    pdf_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "space_exploration_routing.pdf"))
    create_sample_pdf(pdf_file)

    try:
        # 1. Phase 2 Ingestion: Load and chunk PDF document
        ingestion_service = DocumentIngestionService(chunk_size=300, overlap=50)
        chunks = ingestion_service.ingest_file(pdf_file)
        logger.info(f"Ingestion produced {len(chunks)} chunks from PDF.")

        # 2. Initialize Retrievers, Router, and RoutingService
        embedding_service = EmbeddingService()
        dense_retriever = DenseRetriever(embedding_service)
        bm25_retriever = BM25Retriever()
        hybrid_retriever = HybridRetriever(dense_retriever, bm25_retriever)
        rule_router = RuleBasedRouter()
        
        routing_service = RoutingService(dense_retriever, bm25_retriever, hybrid_retriever, rule_router)

        # 3. Index into System
        total_indexed = routing_service.add_documents(chunks)
        logger.info(f"Successfully indexed {total_indexed} chunks via RoutingService.")

        # 4. Test Queries demonstrating BM25, Dense, and Hybrid dynamic routing
        queries = [
            # Short Factual (BM25)
            "JWST",
            "Artemis II",
            "Perseverance rover",
            # Semantic (Dense)
            "How do astronauts survive in deep space?",
            "What technologies support lunar exploration?",
            # Complex Comparative (Hybrid)
            "Compare Apollo and Artemis missions",
            "How does JWST differ from Hubble telescope?"
        ]

        for query in queries:
            logger.info(f"\n==================================================")
            logger.info(f'Executing Routed Search for Query:\n"{query}"')
            logger.info(f"==================================================")

            # Execute Search via RoutingService
            response = routing_service.search(query, k=2)
            
            logger.info(f"Selected Strategy: {response.strategy.upper()}")
            logger.info(f"Routing Reason: {response.reason}")
            logger.info(f"Retrieved Chunks Count: {len(response.results)}")
            
            for i, res in enumerate(response.results, 1):
                logger.info(f"\n[{i}] Chunk ID: {res.id} | Page: {res.metadata.page} | Sources: {res.retrieval_sources}")
                logger.info(f"    Score: {res.score:.4f}")
                logger.info(f"    Snippet: {res.text[:120]}...")

    finally:
        # Clean up sample PDF file
        if os.path.exists(pdf_file):
            os.remove(pdf_file)
        logger.info("\n--- Query Routing Test Finished & Cleaned Up ---")


if __name__ == "__main__":
    main()
