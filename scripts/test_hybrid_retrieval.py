"""
Standalone script demonstrating Phase 5 Hybrid Retrieval on a multi-page PDF document.
Uses PyMuPDF to generate a sample PDF, indexes it in Dense, BM25, and Hybrid systems,
and compares retrieval rankings side-by-side across various queries.
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
    """Executes the hybrid retrieval test workflow and compares rankings side-by-side."""
    logger.info("--- Starting Multi-Page PDF Hybrid Retrieval Test ---")

    pdf_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "space_exploration_hybrid.pdf"))
    create_sample_pdf(pdf_file)

    try:
        # 1. Phase 2 Ingestion: Load and chunk PDF document
        ingestion_service = DocumentIngestionService(chunk_size=300, overlap=50)
        chunks = ingestion_service.ingest_file(pdf_file)
        logger.info(f"Ingestion produced {len(chunks)} chunks from PDF.")

        # 2. Initialize Retrievers
        embedding_service = EmbeddingService()
        dense_retriever = DenseRetriever(embedding_service)
        bm25_retriever = BM25Retriever()
        hybrid_retriever = HybridRetriever(dense_retriever, bm25_retriever, dense_weight=0.5, bm25_weight=0.5)

        # 3. Index into Hybrid System (indexes into both Dense and BM25)
        total_indexed = hybrid_retriever.add_documents(chunks)
        logger.info(f"Successfully indexed {total_indexed} chunks into both Dense and BM25 stores.")

        # 4. Side-by-Side Comparison Queries
        queries = [
            "JWST infrared telescope",
            "Perseverance rover",
            "lunar astronauts",
            "deep space observation"
        ]

        for query in queries:
            logger.info(f"\n==================================================")
            logger.info(f'Executing Query: "{query}"')
            logger.info(f"==================================================")

            # Dense Search
            dense_res = dense_retriever.search(query, k=2)
            logger.info("\n--- DENSE RETRIEVAL RESULTS ---")
            for i, res in enumerate(dense_res, 1):
                logger.info(f"[{i}] Score: {res.score:.4f} | Chunk ID: {res.id} | Page: {res.metadata.page}")

            # BM25 Search
            bm25_res = bm25_retriever.search(query, k=2)
            logger.info("\n--- BM25 KEYWORD RESULTS ---")
            for i, res in enumerate(bm25_res, 1):
                logger.info(f"[{i}] Score: {res.score:.4f} | Chunk ID: {res.id} | Page: {res.metadata.page}")

            # Hybrid Search
            hybrid_res = hybrid_retriever.search(query, k=2, dense_weight=0.6, bm25_weight=0.4)
            logger.info("\n--- HYBRID RETRIEVAL RESULTS (Dense=0.6, BM25=0.4) ---")
            for i, res in enumerate(hybrid_res, 1):
                logger.info(f"[{i}] Final Score: {res.score:.4f} | Sources: {res.retrieval_sources} | Chunk ID: {res.id} | Page: {res.metadata.page}")
                logger.info(f"    Dense Score (Norm): {res.dense_score} | BM25 Score (Norm): {res.bm25_score}")
                logger.info(f"    Snippet: {res.text[:100]}...")

    finally:
        # Clean up sample PDF file
        if os.path.exists(pdf_file):
            os.remove(pdf_file)
        logger.info("\n--- Hybrid Test Finished & Cleaned Up ---")


if __name__ == "__main__":
    main()
