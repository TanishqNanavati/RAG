"""
Pydantic data models for Phase 10 Adaptive Retry Orchestration layer.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from src.evaluation.models import EvaluationResult
from src.retrieval_filtering.models import RetrievalConfidenceResult


class AttemptMetadata(BaseModel):
    """Tracks metrics and decisions for a single generation attempt."""
    attempt_number: int = Field(..., description="The sequence number of this attempt (1, 2, 3).")
    strategy: str = Field(..., description="The retrieval strategy used for this attempt (e.g., dense, hybrid).")
    faithfulness_score: float = Field(..., description="Evaluator faithfulness score for this attempt.")
    citation_score: float = Field(..., description="Evaluator citation correctness score for this attempt.")
    retry_triggered: bool = Field(..., description="Whether this attempt failed the threshold and triggered a retry.")
    retrieval_quality: Optional[str] = Field(None, description="Quality label from confidence analyzer.")
    retrieval_confidence_score: Optional[float] = Field(None, description="Score from confidence analyzer.")
    llm_generation_skipped: bool = Field(False, description="True if generation was aborted due to poor retrieval.")
    filter_reason: Optional[str] = Field(None, description="Reason if generation was skipped.")
    pipeline_ms: int = Field(0, description="Time spent in retrieval and reranking.")
    generation_ms: int = Field(0, description="Time spent in LLM answer generation.")
    evaluation_ms: int = Field(0, description="Time spent in self-evaluation.")


class OrchestrationMetadata(BaseModel):
    """Aggregated metadata for the complete self-healing execution flow."""
    attempts: List[AttemptMetadata] = Field(default_factory=list, description="Log of all retry attempts executed.")
    selected_strategy: str = Field(..., description="The retrieval strategy of the winning/returned answer.")
    total_retries: int = Field(..., description="Total number of retries executed after the initial attempt.")


class OrchestratedResponse(BaseModel):
    """Final unified response from the adaptive orchestration layer."""
    answer: str = Field(..., description="The best generated answer found.")
    citations: Dict[str, str] = Field(..., description="Citation mapping for the best answer.")
    evaluation: EvaluationResult = Field(..., description="Evaluation report for the best answer.")
    metadata: OrchestrationMetadata = Field(..., description="Metadata tracking the self-healing retry logic.")
    chunks: List[Any] = Field(default_factory=list, description="The final reranked chunks used to generate the answer.")
