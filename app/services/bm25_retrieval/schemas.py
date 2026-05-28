"""
Pydantic schemas for Phase 4 BM25 keyword retrieval pipeline.
Designed to match Phase 3 Dense schemas exactly for future hybrid retrieval.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.services.ingestion.schemas import ChunkMetadata


class RetrievedChunk(BaseModel):
    """Represents a BM25 retrieved document chunk with relevance score."""
    id: str = Field(..., description="Unique identifier of the chunk.")
    text: str = Field(..., description="Text content of the chunk.")
    score: float = Field(..., description="BM25 Okapi relevance score (unbounded positive float).")
    metadata: ChunkMetadata = Field(..., description="Associated chunk metadata.")


class BM25SearchRequest(BaseModel):
    """Request schema for BM25 keyword search endpoint."""
    query: str = Field(..., min_length=1, example="What is the Artemis II mission?", description="User keyword search query.")
    k: int = Field(default=5, ge=1, le=50, example=5, description="Number of top chunks to retrieve.")


class BM25SearchResponse(BaseModel):
    """Response schema for BM25 keyword search endpoint."""
    query: str = Field(..., description="The original search query.")
    results: List[RetrievedChunk] = Field(default_factory=list, description="List of top matching chunks.")


class BM25IndexResponse(BaseModel):
    """Response schema for BM25 document indexing endpoint."""
    status: str = Field(..., example="success")
    chunks_indexed: int = Field(..., example=120, description="Total number of chunks successfully indexed.")
    document_name: str = Field(..., example="space_exploration.pdf", description="Name of the indexed document.")
