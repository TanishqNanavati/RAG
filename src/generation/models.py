"""
Data models for Phase 8 Grounded Answer Generation with Citations.
Defines structured outputs containing the generated answer and associated citation mappings.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.services.hybrid_retrieval.schemas import HybridRetrievedChunk
from app.reranking.models import RerankedChunk


class GeneratedAnswer(BaseModel):
    """Structured response containing the grounded LLM answer and explicit citation mapping."""
    answer: str = Field(..., description="The final grounded answer containing inline citations like [1], [2].")
    citations: Dict[str, str] = Field(..., description="Mapping of citation ID (e.g., '[1]') to the exact source chunk text.")
    invalid_citations_detected: List[str] = Field(default_factory=list, description="List of any invalid citation tags hallucinated by the LLM.")


class AnswerGenerationRequest(BaseModel):
    """Request schema for standalone answer generation API endpoint."""
    query: str = Field(..., min_length=1, example="How does JWST differ from Hubble?", description="User search query.")
    chunks: List[RerankedChunk] = Field(..., description="List of retrieved/re-ranked chunks to use as context.")
    temperature: Optional[float] = Field(default=0.2, ge=0.0, le=1.0, description="LLM sampling temperature.")
