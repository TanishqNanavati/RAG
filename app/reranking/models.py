"""
Pydantic data models for Phase 7 Cross-Encoder Re-Ranking pipeline.
Extends retrieved chunk schemas to include dedicated re-ranking scores.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.services.hybrid_retrieval.schemas import HybridRetrievedChunk


class RerankedChunk(HybridRetrievedChunk):
    """Extended document chunk schema containing both original retrieval score and cross-encoder rerank score."""
    rerank_score: Optional[float] = Field(None, description="Cross-encoder relevance score predicting query-chunk alignment.")


class RerankRequest(BaseModel):
    """Request schema for standalone re-ranking endpoint."""
    query: str = Field(..., min_length=1, example="How does JWST differ from Hubble?", description="User search query.")
    chunks: List[HybridRetrievedChunk] = Field(..., description="List of candidate chunks retrieved during stage-1 recall.")
    top_k: Optional[int] = Field(default=3, ge=1, le=50, example=3, description="Number of top reranked chunks to return.")


class RerankResponse(BaseModel):
    """Response schema for standalone re-ranking endpoint."""
    query: str = Field(..., description="The original search query.")
    results: List[RerankedChunk] = Field(default_factory=list, description="List of top chunks sorted descending by rerank score.")
