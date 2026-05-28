"""
Abstract base class definitions establishing the modular Re-Ranking interface.
Designed for future extensibility (Cohere, Jina AI, LLM rerankers).
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from app.services.hybrid_retrieval.schemas import HybridRetrievedChunk
from app.reranking.models import RerankedChunk


class BaseReRanker(ABC):
    """Abstract interface for document chunk re-ranking engines."""

    @abstractmethod
    def rerank(
        self,
        query: str,
        chunks: List[HybridRetrievedChunk],
        top_k: Optional[int] = None
    ) -> List[RerankedChunk]:
        """
        Re-scores and reorders candidate chunks based on query relevance.

        Args:
            query: Input search query string.
            chunks: List of stage-1 retrieved candidate chunks.
            top_k: Optional number of top chunks to return after reranking.

        Returns:
            List of RerankedChunk schemas sorted descending by rerank_score.
        """
        pass
