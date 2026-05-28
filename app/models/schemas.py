"""
Pydantic schemas for API requests and responses.
Defines data structures for queries, retrieval results, citations, and evaluation metrics.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Schema for health check endpoint response."""
    status: str = Field(..., example="ok")
    environment: str = Field(..., example="dev")


class Citation(BaseModel):
    """Schema representing a source citation for generated answers."""
    source_id: str = Field(..., description="Unique identifier of the source chunk or document.")
    text_snippet: str = Field(..., description="Excerpt from the source text supporting the claim.")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional source metadata (e.g., page, title).")


class SelfEvaluation(BaseModel):
    """Schema for self-evaluation scores of the generated response."""
    faithfulness_score: float = Field(..., ge=0.0, le=1.0, description="Score indicating how well the answer aligns with retrieved context.")
    citation_correctness_score: float = Field(..., ge=0.0, le=1.0, description="Score indicating correctness and relevance of citations.")
    passed: bool = Field(..., description="Whether the response passed the defined quality thresholds.")


class RAGRequest(BaseModel):
    """Schema for incoming RAG query requests."""
    query: str = Field(..., min_length=1, description="The user query to be answered.")
    strategy: Optional[str] = Field(default="auto", description="Retrieval strategy: 'dense', 'bm25', 'hybrid', or 'auto' (router).")
    enable_evaluation: bool = Field(default=True, description="Whether to run self-evaluation and iterative re-retrieval.")


class RAGResponse(BaseModel):
    """Schema for RAG query responses."""
    query: str = Field(..., description="The original user query.")
    answer: str = Field(..., description="The generated answer.")
    citations: List[Citation] = Field(default_factory=list, description="List of sources cited in the answer.")
    retrieval_strategy_used: str = Field(..., description="The actual retrieval strategy employed.")
    evaluation: Optional[SelfEvaluation] = Field(default=None, description="Self-evaluation results if enabled.")
    iterations: int = Field(default=1, description="Number of RAG rounds executed.")
