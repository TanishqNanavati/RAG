"""
FAISS vector store wrapper class for dense retrieval.
Manages vector indexing and in-memory metadata preservation.
"""

import logging
from typing import List, Dict, Any
import numpy as np
import faiss
from app.services.ingestion.schemas import DocumentChunk
from app.services.dense_retrieval.schemas import SearchResult

logger = logging.getLogger(__name__)


class FAISSVectorStore:
    """Wrapper class for FAISS vector index maintaining separate chunk metadata storage."""

    def __init__(self, dimension: int) -> None:
        """
        Initializes an exact inner-product FAISS index (IndexFlatIP) for cosine similarity.

        Args:
            dimension: Vector embedding dimension.
        """
        self.dimension = dimension
        # IndexFlatIP calculates inner product. Since vectors are normalized, IP == Cosine Similarity.
        self.index = faiss.IndexFlatIP(dimension)
        self.chunk_records: Dict[int, DocumentChunk] = {}
        logger.info(f"Initialized FAISS IndexFlatIP (dimension={dimension})")

    def add_embeddings(self, vectors: np.ndarray, chunks: List[DocumentChunk]) -> int:
        """
        Adds embedding vectors to FAISS index and stores chunk records in memory.

        Args:
            vectors: 2D numpy array of shape (num_chunks, dimension).
            chunks: List of DocumentChunk schemas.

        Returns:
            Total number of vectors currently in the index.
        """
        if vectors.shape[0] != len(chunks):
            raise ValueError("Number of vectors must match number of chunks.")
        if vectors.shape[1] != self.dimension:
            raise ValueError(f"Vector dimension mismatch. Expected {self.dimension}, got {vectors.shape[1]}")

        start_id = self.index.ntotal
        logger.info(f"Adding {len(chunks)} vectors to FAISS index (starting at ID {start_id}).")

        # Add vectors to FAISS index
        self.index.add(vectors)

        # Map sequential FAISS integer IDs to original DocumentChunk objects
        for i, chunk in enumerate(chunks):
            faiss_id = start_id + i
            self.chunk_records[faiss_id] = chunk

        logger.info(f"FAISS index total vectors: {self.index.ntotal}")
        return self.index.ntotal

    def search(self, query_vector: np.ndarray, k: int = 5) -> List[SearchResult]:
        """
        Searches FAISS index for top-k most similar vectors.

        Args:
            query_vector: 1D numpy array representing the query embedding.
            k: Number of top results to retrieve.

        Returns:
            List of SearchResult schemas containing text, score, and metadata.
        """
        if self.index.ntotal == 0:
            logger.warning("Search attempted on empty FAISS index.")
            return []

        # Ensure query_vector is 2D shape (1, dimension)
        if query_vector.ndim == 1:
            query_vector = np.expand_dims(query_vector, axis=0)

        # Search FAISS index
        scores, indices = self.index.search(query_vector, k)

        results: List[SearchResult] = []
        for score, faiss_id in zip(scores[0], indices[0]):
            if faiss_id == -1 or faiss_id not in self.chunk_records:
                continue

            chunk = self.chunk_records[faiss_id]
            results.append(SearchResult(
                id=chunk.id,
                text=chunk.text,
                score=float(score),
                metadata=chunk.metadata
            ))

        return results
