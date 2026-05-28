"""
Cross-encoder re-ranker implementation using sentence-transformers.
Performs deep attention-based relevance scoring on (query, chunk) pairs.
"""

import logging
from typing import List, Optional
import numpy as np
from sentence_transformers import CrossEncoder
from app.core.config import settings
from app.services.hybrid_retrieval.schemas import HybridRetrievedChunk
from app.reranking.interfaces import BaseReRanker
from app.reranking.models import RerankedChunk

logger = logging.getLogger(__name__)


class CrossEncoderReRanker(BaseReRanker):
    """Production re-ranker using sentence-transformers CrossEncoder models."""

    def __init__(self, model_name: Optional[str] = None, device: str = "cpu") -> None:
        """
        Initializes the CrossEncoder model once upon startup.

        Args:
            model_name: Name of the huggingface cross-encoder model.
            device: Execution device ('cpu' or 'cuda').
        """
        self.model_name = model_name or settings.rerank_model
        self.device = device
        logger.info(f"Initializing CrossEncoder reranker with model: {self.model_name} on device: {self.device}")
        
        try:
            self.model = CrossEncoder(self.model_name, device=self.device)
            logger.info("CrossEncoder reranker initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to load CrossEncoder model '{self.model_name}': {e}")
            raise RuntimeError(f"CrossEncoder initialization failed: {e}")

    def rerank(
        self,
        query: str,
        chunks: List[HybridRetrievedChunk],
        top_k: Optional[int] = None
    ) -> List[RerankedChunk]:
        """
        Constructs (query, chunk) pairs, executes CrossEncoder inference, attaches
        rerank scores, and returns sorted results.

        Args:
            query: Input search query string.
            chunks: List of stage-1 retrieved candidate chunks.
            top_k: Optional number of top chunks to return after reranking.

        Returns:
            List of RerankedChunk schemas sorted descending by rerank_score.
        """
        if not chunks:
            logger.warning("Reranker received empty chunk list. Returning empty list.")
            return []

        if not query or not query.strip():
            logger.warning("Reranker received empty query. Returning original chunks with 0.0 rerank score.")
            return [RerankedChunk(**c.model_dump(), rerank_score=0.0) for c in chunks]

        logger.info(f"Re-ranking {len(chunks)} retrieved chunks for query: '{query}'")

        # 1. Build query-chunk pairs
        pairs = [[query, chunk.text] for chunk in chunks]

        try:
            # 2. Run CrossEncoder inference
            scores = self.model.predict(pairs, show_progress_bar=False)
        except Exception as e:
            logger.error(f"CrossEncoder inference failed: {e}. Falling back to original scores.")
            return [RerankedChunk(**c.model_dump(), rerank_score=0.0) for c in chunks]

        # 3. Attach rerank scores to chunks
        reranked_chunks: List[RerankedChunk] = []
        for chunk, score in zip(chunks, scores):
            rerank_score = float(score)
            reranked_chunks.append(RerankedChunk(
                **chunk.model_dump(),
                rerank_score=rerank_score
            ))

        # 4. Sort chunks descending by rerank score
        reranked_chunks.sort(key=lambda x: (x.rerank_score is not None, x.rerank_score), reverse=True)

        if reranked_chunks:
            logger.info(f"Generated rerank scores. Top reranked score: {reranked_chunks[0].rerank_score:.4f}")

        # 5. Slice top-k if specified
        if top_k is not None and top_k > 0:
            reranked_chunks = reranked_chunks[:top_k]

        return reranked_chunks
