"""
Pydantic data models for Retrieval Confidence Filtering.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class RetrievalConfidenceResult(BaseModel):
    """Result of analyzing retrieval and reranking scores to determine context quality."""
    is_confident: bool = Field(..., description="True if retrieval is strong enough to answer, False if too weak.")
    confidence_score: float = Field(..., description="Aggregated confidence score (usually top rerank score).")
    reason: str = Field(..., description="Explanation of the confidence determination.")
    top_rerank_score: Optional[float] = Field(None, description="Highest cross-encoder score among chunks.")
    avg_rerank_score: Optional[float] = Field(None, description="Average cross-encoder score.")
    top_dense_score: Optional[float] = Field(None, description="Highest dense semantic similarity score.")
    retrieval_quality: Literal["high", "medium", "low"] = Field(..., description="Categorical quality label.")
