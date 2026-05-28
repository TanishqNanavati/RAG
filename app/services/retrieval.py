"""
Retrieval service implementing BM25, dense, hybrid strategies, and a query router.
"""

import logging
from typing import List, Dict, Any
from app.core.config import settings
from app.services.embeddings import EmbeddingService

logger = logging.getLogger(__name__)


class RetrievalService:
    """Service handling multi-strategy document retrieval and routing."""

    def __init__(self, embedding_service: EmbeddingService) -> None:
        """
        Initializes the retrieval service with required clients and helpers.
        
        Args:
            embedding_service: Instance of EmbeddingService for dense retrieval.
        """
        self.embedding_service = embedding_service
        logger.info("Initialized RetrievalService")

    def route_query(self, query: str) -> str:
        """
        Determines the optimal retrieval strategy for a given query.

        Args:
            query: The input user query.

        Returns:
            Selected strategy name ('dense', 'bm25', or 'hybrid').
        """
        logger.debug(f"Routing query: '{query}'")
        # Simple heuristic router: e.g., keyword-heavy queries -> bm25, semantic -> dense/hybrid
        if any(kw in query.lower() for kw in ["exact", "id", "code", "number"]):
            return "bm25"
        return "hybrid"

    def retrieve_bm25(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Performs keyword search using BM25 (Whoosh/Elasticsearch fallback)."""
        logger.info(f"Executing BM25 retrieval for query: '{query}'")
        # Placeholder for Whoosh search
        return [{"source_id": "doc-1", "text": "BM25 sample result matching keyword.", "score": 0.85}]

    def retrieve_dense(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Performs semantic vector search using Qdrant/FAISS."""
        logger.info(f"Executing dense retrieval for query: '{query}'")
        vector = self.embedding_service.get_embedding(query)
        # Placeholder for Qdrant search using vector
        return [{"source_id": "doc-2", "text": "Dense sample result matching semantics.", "score": 0.91}]

    def retrieve_hybrid(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Combines BM25 and dense retrieval using Reciprocal Rank Fusion (RRF)."""
        logger.info(f"Executing hybrid retrieval for query: '{query}'")
        bm25_res = self.retrieve_bm25(query, top_k=settings.top_k_bm25)
        dense_res = self.retrieve_dense(query, top_k=settings.top_k_dense)
        
        # Placeholder for RRF merging logic
        combined = bm25_res + dense_res
        return combined[:top_k]

    def search(self, query: str, strategy: str = "auto") -> List[Dict[str, Any]]:
        """
        Main entry point for executing retrieval based on strategy.

        Args:
            query: The user query.
            strategy: 'dense', 'bm25', 'hybrid', or 'auto'.

        Returns:
            List of retrieved document dictionaries.
        """
        if strategy == "auto":
            strategy = self.route_query(query)
            logger.info(f"Router selected strategy: {strategy}")

        if strategy == "bm25":
            return self.retrieve_bm25(query, settings.top_k_bm25)
        elif strategy == "dense":
            return self.retrieve_dense(query, settings.top_k_dense)
        else:
            return self.retrieve_hybrid(query, max(settings.top_k_dense, settings.top_k_bm25))
