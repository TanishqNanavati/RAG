"""
Dense retriever service coordinating embedding generation and FAISS vector indexing.
"""

import logging
from typing import List
from app.services.ingestion.schemas import DocumentChunk
from app.services.retrieval.embedding_service import EmbeddingService
from app.services.retrieval.vector_store import FAISSVectorStore
from app.services.retrieval.schemas import SearchResult

logger = logging.getLogger(__name__)


class DenseRetriever:
    """Service coordinating semantic embedding generation, FAISS indexing, and retrieval."""

    def __init__(self, embedding_service: EmbeddingService) -> None:
        """
        Initializes retriever with embedding service and creates FAISS vector store.

        Args:
            embedding_service: Instance of EmbeddingService.
        """
        self.embedding_service = embedding_service
        self.vector_store = FAISSVectorStore(dimension=self.embedding_service.dimension)
        logger.info("Initialized DenseRetriever")

    def add_documents(self, chunks: List[DocumentChunk]) -> int:
        """
        Extracts chunk texts, generates dense embeddings, and stores them in FAISS.

        Args:
            chunks: List of DocumentChunk schemas from Phase 2 ingestion.

        Returns:
            Total number of chunks indexed.
        """
        if not chunks:
            logger.warning("add_documents called with empty chunk list.")
            return 0

        logger.info(f"Generating embeddings for {len(chunks)} chunks.")
        texts = [chunk.text for chunk in chunks]
        vectors = self.embedding_service.embed_texts(texts)

        total_indexed = self.vector_store.add_embeddings(vectors, chunks)
        return total_indexed

    def search(self, query: str, k: int = 5) -> List[SearchResult]:
        """
        Embeds query string, searches FAISS vector store, and returns top-k matching chunks.

        Args:
            query: User search query.
            k: Number of top chunks to retrieve.

        Returns:
            List of SearchResult schemas.
        """
        if not query.strip():
            raise ValueError("Search query cannot be empty.")

        logger.info(f"Executing dense semantic search for query: '{query}' (k={k})")
        query_vector = self.embedding_service.embed_text(query)
        results = self.vector_store.search(query_vector, k=k)
        
        logger.info(f"Dense search retrieved {len(results)} results.")
        return results
