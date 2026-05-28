"""
Pydantic schemas for Phase 6 Intelligent Query Routing pipeline.
Defines query features, routing decisions, and routed search responses.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.services.hybrid_retrieval.schemas import HybridRetrievedChunk


class QueryFeatures(BaseModel):
    """Extracted linguistic and structural features of an incoming search query."""
    token_count: int = Field(..., description="Number of whitespace-delimited tokens in the query.")
    contains_acronym: bool = Field(..., description="Whether the query contains uppercase acronyms (e.g., JWST).")
    is_short_query: bool = Field(..., description="Whether the query is short (<= 4 tokens).")
    has_technical_terms: bool = Field(..., description="Whether domain-specific technical terms are present.")
    is_semantic_query: bool = Field(..., description="Whether the query exhibits natural language question semantics.")
    contains_question_words: bool = Field(..., description="Whether question words (how, what, why, etc.) are present.")
    is_comparison_query: bool = Field(..., description="Whether comparison or differential intent keywords exist.")


class RoutingDecision(BaseModel):
    """Structured decision output from the strategy router."""
    strategy: str = Field(..., example="bm25", description="Selected retrieval strategy ('bm25', 'dense', 'hybrid').")
    reason: str = Field(..., example="Short factual keyword query with acronym detected.", description="Human-readable explanation of the routing decision.")
    features: QueryFeatures = Field(..., description="The query features that informed the decision.")


class RouteRequest(BaseModel):
    """Request schema for the standalone routing decision endpoint."""
    query: str = Field(..., min_length=1, example="What is Artemis II?", description="Incoming search query.")


class RouteSearchRequest(BaseModel):
    """Request schema for the full routed search endpoint."""
    query: str = Field(..., min_length=1, example="Compare Artemis and Apollo radiation risks", description="Incoming search query.")
    k: int = Field(default=5, ge=1, le=50, example=5, description="Number of top chunks to retrieve.")


class RoutedRetrievalResponse(BaseModel):
    """Unified response schema containing routing metadata and retrieved chunks."""
    query: str = Field(..., description="The original search query.")
    strategy: str = Field(..., example="hybrid", description="The dynamically selected retrieval strategy.")
    reason: str = Field(..., example="Comparative query with mixed retrieval intent.", description="Explanation for strategy selection.")
    results: List[HybridRetrievedChunk] = Field(default_factory=list, description="List of top matching chunks from the selected retriever.")
