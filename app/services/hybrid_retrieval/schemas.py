"""
Pydantic schemas for Phase 5 Hybrid Retrieval pipeline.
Provides detailed tracking of individual retriever scores, weights, and combined rankings.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator
from app.services.ingestion.schemas import ChunkMetadata


class HybridRetrievedChunk(BaseModel):
    """Represents a document chunk retrieved via hybrid search with merged scores."""
    id: str = Field(..., description="Unique identifier of the chunk.")
    text: str = Field(..., description="Text content of the chunk.")
    score: float = Field(..., description="Final weighted hybrid score (0.0 to 1.0).")
    dense_score: Optional[float] = Field(None, description="Normalized dense cosine similarity score.")
    bm25_score: Optional[float] = Field(None, description="Normalized BM25 Okapi score.")
    metadata: ChunkMetadata = Field(..., description="Associated chunk metadata.")
    retrieval_sources: List[str] = Field(..., example=["dense", "bm25"], description="Which retrievers found this chunk.")


class HybridSearchRequest(BaseModel):
    """Request schema for hybrid search endpoint with configurable weights."""
    query: str = Field(..., min_length=1, example="JWST infrared telescope", description="User search query.")
    k: int = Field(default=5, ge=1, le=50, example=5, description="Number of top chunks to retrieve.")
    dense_weight: float = Field(default=0.5, ge=0.0, le=1.0, example=0.6, description="Weight assigned to dense semantic retrieval.")
    bm25_weight: float = Field(default=0.5, ge=0.0, le=1.0, example=0.4, description="Weight assigned to BM25 keyword retrieval.")

    @field_validator("bm25_weight")
    def validate_weights(cls, bm25_weight: float, info: Any) -> float:
        """Validates that dense_weight + bm25_weight equals 1.0."""
        dense_weight = info.data.get("dense_weight", 0.5)
        total = dense_weight + bm25_weight
        if abs(total - 1.0) > 1e-5:
            raise ValueError(f"dense_weight ({dense_weight}) + bm25_weight ({bm25_weight}) must equal 1.0. Got {total}")
        return bm25_weight


class HybridSearchResponse(BaseModel):
    """Response schema for hybrid search endpoint."""
    query: str = Field(..., description="The original search query.")
    results: List[HybridRetrievedChunk] = Field(default_factory=list, description="List of top matching hybrid chunks.")


class HybridIndexResponse(BaseModel):
    """Response schema for hybrid document indexing endpoint."""
    status: str = Field(..., example="success")
    chunks_indexed: int = Field(..., example=120, description="Total number of chunks successfully indexed in both retrievers.")
