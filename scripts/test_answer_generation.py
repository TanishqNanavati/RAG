"""
Standalone script demonstrating Phase 8 Answer Generation with Citations on a multi-page PDF document.
Uses PyMuPDF to generate a sample PDF, executes Stage-1 recall retrieval, Stage-2 CrossEncoder re-ranking,
and generates the final grounded LLM answer with validated inline citations.
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
from src.generation.answer_generator import AnswerGenerator

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
    """Executes the full RAG pipeline: Ingestion -> Retrieval -> Re-Ranking -> Answer Generation."""
    logger.info("--- Starting Multi-Page PDF Answer Generation with Citations Test ---")

    pdf_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "space_exploration_gen.pdf"))
    create_sample_pdf(pdf_file)

    try:
        # 1. Phase 2 Ingestion: Load and chunk PDF document
        ingestion_service = DocumentIngestionService(chunk_size=300, overlap=50)
        chunks = ingestion_service.ingest_file(pdf_file)
        logger.info(f"Ingestion produced {len(chunks)} chunks from PDF.")

        # 2. Initialize Pipeline Components
        embedding_service = EmbeddingService()
        dense_retriever = DenseRetriever(embedding_service)
        bm25_retriever = BM25Retriever()
        hybrid_retriever = HybridRetriever(dense_retriever, bm25_retriever)
        rule_router = RuleBasedRouter()
        
        routing_service = RoutingService(dense_retriever, bm25_retriever, hybrid_retriever, rule_router)
        cross_encoder = CrossEncoderReRanker()
        pipeline = RetrievalPipeline(routing_service, reranker=cross_encoder, enable_reranking=True)
        
        answer_generator = AnswerGenerator(temperature=0.2)

        # Index documents
        total_indexed = pipeline.add_documents(chunks)
        logger.info(f"Successfully indexed {total_indexed} chunks.")

        # 3. Test Queries demonstrating grounded generation
        queries = [
            "How does JWST differ from Hubble?",
            "What is the primary mission of Perseverance?",
            "What is Artemis II?"
        ]

        for query in queries:
            logger.info(f"\n==================================================")
            logger.info(f'Executing Full Pipeline for Query:\n"{query}"')
            logger.info(f"==================================================")

            # A. Retrieve & Re-Rank Chunks
            pipeline_res = pipeline.search(query, k=5, top_k=2)
            top_chunks = pipeline_res.results
            logger.info(f"Retrieved & Re-Ranked top {len(top_chunks)} chunks.")

            # B. Generate Answer with Citations
            gen_result = answer_generator.generate_answer(query, top_chunks)

            logger.info("\n--- GENERATED ANSWER ---")
            logger.info(gen_result.answer)

            logger.info("\n--- CITATION MAPPING ---")
            for cit_id, cit_text in gen_result.citations.items():
                logger.info(f"{cit_id} -> {cit_text[:100]}...")

            if gen_result.invalid_citations_detected:
                logger.warning(f"Invalid Citations Detected: {gen_result.invalid_citations_detected}")
            else:
                logger.info("Validation: All citations are valid and grounded.")

    finally:
        # Clean up sample PDF file
        if os.path.exists(pdf_file):
            os.remove(pdf_file)
        logger.info("\n--- Answer Generation Test Finished & Cleaned Up ---")


if __name__ == "__main__":
    main()
