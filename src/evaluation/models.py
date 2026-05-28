"""
Pydantic data models for Phase 9 Self-Evaluation and Verification Module.
Defines the structured output representing the LLM-as-a-Judge evaluation results.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class EvaluationResult(BaseModel):
    """Structured response from the LLM evaluator detailing faithfulness and citation accuracy."""
    faithfulness_score: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Score indicating how well the answer is grounded in the provided context (0.0 = completely hallucinated, 1.0 = fully grounded)."
    )
    citation_score: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Score indicating whether the inline citations properly support their adjacent claims (0.0 = completely incorrect, 1.0 = perfectly cited)."
    )
    issues: List[str] = Field(
        default_factory=list, 
        description="List of specific issues detected, such as hallucinated facts, unsupported statements, or mismatched citations."
    )
