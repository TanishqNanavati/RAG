"""
Educational standalone script demonstrating Phase 3 dense retrieval pipeline.
Loads a sample document, indexes it in FAISS, and runs semantic search.
"""

import os
import sys
import logging

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.ingestion.ingestion_service import DocumentIngestionService
from app.services.dense_retrieval.embedding_service import EmbeddingService
from app.services.dense_retrieval.dense_retriever import DenseRetriever

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    """Executes the dense retrieval test workflow."""
    logger.info("--- Starting Phase 3 Dense Retrieval Test ---")

    # 1. Create a mock ethics document
    sample_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "ai_ethics_sample.txt"))
    sample_text = (
        "Artificial intelligence presents significant societal challenges and ethical dilemmas. "
        "One major concern is algorithmic bias, where machine learning models perpetuate historical discrimination in hiring and lending. "
        "Another critical risk is the erosion of data privacy, as autonomous systems collect and analyze vast amounts of personal information without explicit user consent. "
        "Furthermore, the deployment of AI in autonomous weapons introduces severe moral questions regarding human oversight in lethal decision-making. "
        "Finally, economic displacement via job automation requires robust policy interventions to support reskilling workers."
    )
    with open(sample_file, "w", encoding="utf-8") as f:
        f.write(sample_text)
    logger.info(f"Created sample ethics document at: {sample_file}")

    try:
        # 2. Phase 2 Ingestion: Load and chunk document
        ingestion_service = DocumentIngestionService(chunk_size=200, overlap=50)
        chunks = ingestion_service.ingest_file(sample_file)
        logger.info(f"Ingestion produced {len(chunks)} chunks.")

        # 3. Phase 3 Indexing: Initialize retriever and index chunks in FAISS
        embedding_service = EmbeddingService()
        retriever = DenseRetriever(embedding_service)
        
        total_indexed = retriever.add_documents(chunks)
        logger.info(f"Successfully indexed {total_indexed} chunks in FAISS vector store.")

        # 4. Semantic Search: Query without exact keyword match
        query = "What are the ethical risks of artificial intelligence?"
        logger.info(f"\nExecuting Semantic Search for Query: '{query}'")
        
        results = retriever.search(query, k=3)

        logger.info("\n--- Top Semantic Search Results ---")
        for i, res in enumerate(results, 1):
            logger.info(f"\nResult {i} (Score: {res.score:.4f}):")
            logger.info(f"Chunk ID: {res.id}")
            logger.info(f"Text Snippet: {res.text}")
            logger.info(f"Metadata: {res.metadata.model_dump()}")

    finally:
        # Clean up sample file
        if os.path.exists(sample_file):
            os.remove(sample_file)
        logger.info("\n--- Test Finished & Cleaned Up ---")


if __name__ == "__main__":
    main()
