"""
Retrieval metrics for benchmarking.
"""

from typing import List
import math

def calculate_recall_at_k(retrieved_chunk_ids: List[str], expected_chunk_ids: List[str], k: int) -> float:
    """
    Measures whether ANY of the expected chunks were retrieved within the top-k results.
    Returns 1.0 for success, 0.0 for failure.
    """
    if not expected_chunk_ids:
        return 1.0

    top_k_retrieved = retrieved_chunk_ids[:k]
    matched = set(expected_chunk_ids).intersection(set(top_k_retrieved))
    return 1.0 if len(matched) > 0 else 0.0

def calculate_mrr(retrieved_chunk_ids: List[str], expected_chunk_ids: List[str]) -> float:
    """Mean Reciprocal Rank of the first relevant chunk."""
    if not expected_chunk_ids:
        return 1.0
    for i, cid in enumerate(retrieved_chunk_ids):
        if cid in expected_chunk_ids:
            return 1.0 / (i + 1)
    return 0.0

def calculate_ndcg(retrieved_chunk_ids: List[str], expected_chunk_ids: List[str], k: int = 5) -> float:
    """Normalized Discounted Cumulative Gain (binary relevance)."""
    if not expected_chunk_ids:
        return 1.0
    dcg = 0.0
    for i, cid in enumerate(retrieved_chunk_ids[:k]):
        if cid in expected_chunk_ids:
            dcg += 1.0 / math.log2(i + 2)
    idcg = 0.0
    for i in range(min(len(expected_chunk_ids), k)):
        idcg += 1.0 / math.log2(i + 2)
    return dcg / idcg if idcg > 0 else 0.0

def calculate_context_precision(retrieved_chunk_ids: List[str], expected_chunk_ids: List[str]) -> float:
    """Percentage of retrieved chunks that are relevant."""
    if not expected_chunk_ids or not retrieved_chunk_ids:
        return 1.0 if not expected_chunk_ids else 0.0
    matched = set(retrieved_chunk_ids).intersection(set(expected_chunk_ids))
    return len(matched) / len(retrieved_chunk_ids)
