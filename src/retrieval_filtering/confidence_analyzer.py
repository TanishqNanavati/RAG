"""
Retrieval Confidence Analyzer to evaluate the quality of retrieved context.
Prevents irrelevant chunks from causing hallucinations and saves LLM API costs.
"""

import logging
from typing import List
from app.reranking.models import RerankedChunk
from src.retrieval_filtering.models import RetrievalConfidenceResult
from app.core.config import settings

logger = logging.getLogger(__name__)


class RetrievalConfidenceAnalyzer:
    """Analyzes retrieval and reranking scores to act as an early-exit safeguard."""

    def __init__(self) -> None:
        self.min_rerank_score = settings.min_rerank_score
        self.min_avg_rerank_score = settings.min_avg_rerank_score
        logger.info(f"Initialized RetrievalConfidenceAnalyzer (min_rerank={self.min_rerank_score}, min_avg={self.min_avg_rerank_score})")

    def analyze(self, reranked_chunks: List[RerankedChunk]) -> RetrievalConfidenceResult:
        """
        Calculates heuristics on the chunk scores to determine if they are safe to send to the LLM.

        Args:
            reranked_chunks: Candidate chunks scored by CrossEncoder.

        Returns:
            RetrievalConfidenceResult indicating whether to proceed with generation.
        """
        if not reranked_chunks:
            logger.warning("Confidence Analyzer received 0 chunks. Flagging as low confidence.")
            return RetrievalConfidenceResult(
                is_confident=False,
                confidence_score=0.0,
                reason="No chunks retrieved.",
                top_rerank_score=None,
                avg_rerank_score=None,
                top_dense_score=None,
                retrieval_quality="low"
            )

        rerank_scores = [c.rerank_score for c in reranked_chunks if c.rerank_score is not None]
        top_rerank = max(rerank_scores) if rerank_scores else -99.0
        avg_rerank = sum(rerank_scores) / len(rerank_scores) if rerank_scores else -99.0

        dense_scores = [c.dense_score for c in reranked_chunks if getattr(c, 'dense_score', None) is not None]
        top_dense = max(dense_scores) if dense_scores else 0.0

        # Heuristic Logic
        if top_rerank < self.min_rerank_score or avg_rerank < self.min_avg_rerank_score:
            quality = "low"
            is_confident = False
            reason = f"Top rerank ({top_rerank:.2f}) or average ({avg_rerank:.2f}) below threshold."
        elif top_rerank > 0.0:  # CrossEncoder logits > 0 generally indicate positive entailment
            quality = "high"
            is_confident = True
            reason = "Strong semantic alignment with query."
        else:
            quality = "medium"
            is_confident = True
            reason = "Partial relevance. Acceptable for generation but may lack complete details."

        logger.info(f"Retrieval Quality Evaluated as: {quality.upper()} | Confident: {is_confident} | Reason: {reason}")

        return RetrievalConfidenceResult(
            is_confident=is_confident,
            confidence_score=top_rerank,
            reason=reason,
            top_rerank_score=top_rerank,
            avg_rerank_score=avg_rerank,
            top_dense_score=top_dense,
            retrieval_quality=quality
        )
