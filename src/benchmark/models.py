"""
Pydantic models for the Offline Evaluation Framework.
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class ExperimentConfig(BaseModel):
    embedding_model: str
    chunk_size: int
    reranker: str
    retrieval_strategy: str
    prompt_version: str


class BenchmarkDatasetItem(BaseModel):
    """Represents a single query-answer pair in the benchmark dataset."""
    id: str = Field(..., description="Unique identifier for the test case.")
    query: str = Field(..., description="The user query to test.")
    ground_truth_answer: str = Field(..., description="The expected correct answer.")
    expected_keywords: Optional[List[str]] = Field(None, description="Keywords expected in the answer.")
    expected_chunk_ids: Optional[List[str]] = Field(None, description="Chunk IDs expected to be retrieved.")
    metadata: Optional[Dict[str, str]] = Field(default_factory=dict)


class LatencyBreakdown(BaseModel):
    retrieval_ms: int
    rerank_ms: int
    generation_ms: int
    evaluation_ms: int
    total_ms: int


class QueryEvaluationRecord(BaseModel):
    """Detailed evaluation metrics for a single query."""
    query_id: str
    query: str
    generated_answer: str
    ground_truth: str
    retrieved_chunk_ids: List[str]
    retrieval_strategy: str
    faithfulness_score: float
    citation_score: float
    answer_quality_score: float
    answer_correctness: float
    answer_completeness: float
    answer_clarity: float
    answer_groundedness: float
    answerability_score: float
    recall_at_1: float
    recall_at_3: float
    recall_at_5: float
    mrr: float
    ndcg: float
    context_precision: float
    latency: LatencyBreakdown
    failures: List[str]
    passed: bool


class BenchmarkSummary(BaseModel):
    """Aggregated evaluation metrics across the entire dataset."""
    total_queries: int
    config: ExperimentConfig
    avg_faithfulness: float
    avg_citation_correctness: float
    avg_answer_quality: float
    avg_answerability: float
    recall_at_1: float
    recall_at_3: float
    recall_at_5: float
    avg_mrr: float
    avg_ndcg: float
    avg_context_precision: float
    hallucination_rate: float
    no_answer_rate: float
    avg_total_latency_ms: float
    failure_counts: Dict[str, int]
