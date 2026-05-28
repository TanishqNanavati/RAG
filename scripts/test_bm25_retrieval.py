"""
Standalone script demonstrating Phase 4 BM25 keyword retrieval on a multi-page PDF document.
Uses PyMuPDF to generate a sample PDF, ingests it, indexes it in BM25Okapi, and verifies exact keyword matching.
"""

import os
import sys
import logging
import fitz  # PyMuPDF

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.ingestion.ingestion_service import DocumentIngestionService
from app.services.bm25_retrieval.bm25_retriever import BM25Retriever

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
    """Executes the BM25 keyword retrieval test workflow on a multi-page PDF."""
    logger.info("--- Starting Multi-Page PDF BM25 Keyword Retrieval Test ---")

    pdf_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "space_exploration_bm25.pdf"))
    create_sample_pdf(pdf_file)

    try:
        # 1. Phase 2 Ingestion: Load and chunk PDF document
        ingestion_service = DocumentIngestionService(chunk_size=300, overlap=50)
        chunks = ingestion_service.ingest_file(pdf_file)
        logger.info(f"Ingestion produced {len(chunks)} chunks from PDF.")

        # 2. Phase 4 Indexing: Initialize BM25 retriever and index chunks
        retriever = BM25Retriever()
        
        total_indexed = retriever.add_documents(chunks)
        logger.info(f"Indexed {total_indexed} chunks into BM25 index")

        # 3. Keyword Search Queries demonstrating exact match, acronyms, and technical terms
        queries = [
            "JWST infrared telescope",
            "Perseverance rover",
            "Artemis II"
        ]

        for query in queries:
            logger.info(f"\n==================================================")
            logger.info(f'Executing BM25 query: "{query}"')
            logger.info(f"==================================================")
            
            results = retriever.search(query, k=1)
            logger.info(f"Retrieved {len(results)} matching chunks")

            for res in results:
                logger.info(f"Score: {res.score:.4f}")
                logger.info(f"Chunk ID: {res.id}")
                logger.info(f"Text Snippet: {res.text}")
                logger.info(f"Metadata: {res.metadata.model_dump()}")

    finally:
        # Clean up sample PDF file
        if os.path.exists(pdf_file):
            os.remove(pdf_file)
        logger.info("\n--- BM25 Test Finished & Cleaned Up ---")


if __name__ == "__main__":
    main()
