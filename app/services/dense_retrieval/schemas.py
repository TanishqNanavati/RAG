"""
Pydantic schemas for Phase 3 dense retrieval pipeline.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.services.ingestion.schemas import ChunkMetadata


class SearchResult(BaseModel):
    """Represents a semantically retrieved document chunk with similarity score."""
    id: str = Field(..., description="Unique identifier of the chunk.")
    text: str = Field(..., description="Text content of the chunk.")
    score: float = Field(..., description="Cosine similarity score (0.0 to 1.0).")
    metadata: ChunkMetadata = Field(..., description="Associated chunk metadata.")


class SearchRequest(BaseModel):
    """Request schema for semantic search endpoint."""
    query: str = Field(..., min_length=1, example="What are ethical concerns of AI?", description="User search query.")
    k: int = Field(default=5, ge=1, le=50, example=5, description="Number of top chunks to retrieve.")


class SearchResponse(BaseModel):
    """Response schema for semantic search endpoint."""
    query: str = Field(..., description="The original search query.")
    results: List[SearchResult] = Field(default_factory=list, description="List of top matching chunks.")


class IndexResponse(BaseModel):
    """Response schema for document indexing endpoint."""
    status: str = Field(..., example="success")
    chunks_indexed: int = Field(..., example=120, description="Total number of chunks successfully indexed.")
