"""
Score normalization and fusion utilities for hybrid retrieval.
Performs Min-Max normalization and weighted score merging across disparate retrieval scales.
"""

import logging
from typing import List, Dict, Any, Optional
from app.services.dense_retrieval.schemas import SearchResult as DenseResult
from app.services.bm25_retrieval.schemas import RetrievedChunk as BM25Result
from app.services.hybrid_retrieval.schemas import HybridRetrievedChunk

logger = logging.getLogger(__name__)


class ScoreFusionEngine:
    """Engine handling Min-Max normalization and duplicate merging for hybrid search."""

    @staticmethod
    def min_max_normalize(scores: List[float]) -> List[float]:
        """
        Normalizes a list of raw scores to the range [0.0, 1.0] using Min-Max scaling.

        Args:
            scores: List of raw floating-point scores.

        Returns:
            List of normalized floating-point scores.
        """
        if not scores:
            return []

        min_score = min(scores)
        max_score = max(scores)

        # Edge case: All scores are identical or only 1 score exists
        if max_score == min_score:
            logger.debug(f"min_score equals max_score ({min_score}). Returning 1.0 for all positive scores.")
            return [1.0 if s > 0 else 0.0 for s in scores]

        normalized = [(s - min_score) / (max_score - min_score) for s in scores]
        return normalized

    @classmethod
    def fuse_results(
        cls,
        dense_results: List[DenseResult],
        bm25_results: List[BM25Result],
        dense_weight: float = 0.5,
        bm25_weight: float = 0.5,
        top_k: int = 5
    ) -> List[HybridRetrievedChunk]:
        """
        Normalizes scores from both retrievers, merges duplicate chunks, computes
        weighted final hybrid scores, and returns the top-k ranked results.

        Args:
            dense_results: List of SearchResult objects from DenseRetriever.
            bm25_results: List of RetrievedChunk objects from BM25Retriever.
            dense_weight: Weight for dense retrieval scores (0.0 to 1.0).
            bm25_weight: Weight for BM25 retrieval scores (0.0 to 1.0).
            top_k: Number of final ranked chunks to return.

        Returns:
            List of HybridRetrievedChunk schemas sorted descending by hybrid score.
        """
        logger.info(f"Fusing {len(dense_results)} dense results and {len(bm25_results)} BM25 results (weights: dense={dense_weight}, bm25={bm25_weight}).")

        # 1. Extract raw scores and normalize
        dense_scores = [res.score for res in dense_results]
        bm25_scores = [res.score for res in bm25_results]

        norm_dense = cls.min_max_normalize(dense_scores)
        norm_bm25 = cls.min_max_normalize(bm25_scores)

        # 2. Merge unique chunks using dictionary mapping chunk.id -> dict of attributes
        merged_map: Dict[str, Dict[str, Any]] = {}

        # Process Dense results
        for res, norm_s in zip(dense_results, norm_dense):
            merged_map[res.id] = {
                "id": res.id,
                "text": res.text,
                "metadata": res.metadata,
                "dense_score": norm_s,
                "bm25_score": 0.0,
                "retrieval_sources": ["dense"]
            }

        # Process BM25 results
        for res, norm_s in zip(bm25_results, norm_bm25):
            if res.id in merged_map:
                # Duplicate exists: update bm25 score and append source
                merged_map[res.id]["bm25_score"] = norm_s
                merged_map[res.id]["retrieval_sources"].append("bm25")
            else:
                # New unique chunk from BM25
                merged_map[res.id] = {
                    "id": res.id,
                    "text": res.text,
                    "metadata": res.metadata,
                    "dense_score": 0.0,
                    "bm25_score": norm_s,
                    "retrieval_sources": ["bm25"]
                }

        logger.info(f"Merged unique chunks count: {len(merged_map)}")

        # 3. Compute weighted hybrid scores and instantiate Pydantic models
        hybrid_chunks: List[HybridRetrievedChunk] = []
        for data in merged_map.values():
            d_score = data["dense_score"]
            b_score = data["bm25_score"]
            
            # Weighted final score formula
            final_score = (dense_weight * d_score) + (bm25_weight * b_score)
            
            hybrid_chunks.append(HybridRetrievedChunk(
                id=data["id"],
                text=data["text"],
                score=final_score,
                dense_score=d_score if "dense" in data["retrieval_sources"] else None,
                bm25_score=b_score if "bm25" in data["retrieval_sources"] else None,
                metadata=data["metadata"],
                retrieval_sources=data["retrieval_sources"]
            ))

        # 4. Sort descending by final hybrid score and slice top-k
        hybrid_chunks.sort(key=lambda x: x.score, reverse=True)
        final_top_k = hybrid_chunks[:top_k]
        
        logger.info(f"Final top-k returned: {len(final_top_k)}")
        return final_top_k
