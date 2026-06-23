"""
Offline Evaluator Runner.
Executes batch evaluation over datasets and computes aggregate metrics.
"""

import os
import csv
import json
import time
import logging
from datetime import datetime
from typing import List, Dict

from app.services.orchestration.orchestrator import AdaptiveRAGOrchestrator
from app.core.config import settings
from src.benchmark.models import (
    BenchmarkDatasetItem, QueryEvaluationRecord, BenchmarkSummary, 
    ExperimentConfig, LatencyBreakdown
)
from src.benchmark.metrics.retrieval_metrics import (
    calculate_recall_at_k, calculate_mrr, calculate_ndcg, calculate_context_precision
)
from src.benchmark.metrics.answer_quality import LLMAnswerJudge

logger = logging.getLogger(__name__)


class BenchmarkRunner:
    """Executes the full RAG pipeline across a dataset and aggregates evaluation metrics."""

    def __init__(self, orchestrator: AdaptiveRAGOrchestrator) -> None:
        self.orchestrator = orchestrator
        self.answer_judge = LLMAnswerJudge()
        
    def run_benchmark(self, dataset: List[BenchmarkDatasetItem], output_dir: str = "evaluations") -> BenchmarkSummary:
        """Runs the benchmark pipeline for the given dataset and saves reports."""
        records: List[QueryEvaluationRecord] = []
        logger.info(f"Starting benchmark run on {len(dataset)} queries.")

        for item in dataset:
            logger.info(f"Evaluating Query ID: {item.id}")
            start_time = time.time()
            
            # 1. Execute end-to-end pipeline
            result = self.orchestrator.execute_query(item.query)
            total_latency = int((time.time() - start_time) * 1000)

            # 2. Extract orchestrator metadata
            winning_attempt = next((a for a in result.metadata.attempts if a.strategy == result.metadata.selected_strategy), result.metadata.attempts[-1])
            qual_map = {"high": 1.0, "medium": 0.5, "low": 0.0}
            answerability = qual_map.get(winning_attempt.retrieval_quality, 0.0)

            retrieved_ids = [getattr(chunk, "id", "") for chunk in result.chunks]
            expected_ids = item.expected_chunk_ids or []
            
            # 3. Calculate Retrieval Metrics
            recall_1 = calculate_recall_at_k(retrieved_ids, expected_ids, 1)
            recall_3 = calculate_recall_at_k(retrieved_ids, expected_ids, 3)
            recall_5 = calculate_recall_at_k(retrieved_ids, expected_ids, 5)
            mrr = calculate_mrr(retrieved_ids, expected_ids)
            ndcg = calculate_ndcg(retrieved_ids, expected_ids)
            ctx_prec = calculate_context_precision(retrieved_ids, expected_ids)

            # 4. Answer Quality
            quality_res = self.answer_judge.evaluate(
                query=item.query, 
                generated_answer=result.answer, 
                ground_truth=item.ground_truth_answer
            )
            
            passed = (quality_res.score >= 0.7) and (result.evaluation.faithfulness_score >= 0.7)

            # 5. Categorize Failures
            failures = []
            if recall_5 == 0.0 and expected_ids: failures.append("retrieval_miss")
            if "not available in the provided documents" not in result.answer.lower() and result.evaluation.faithfulness_score < 0.7: failures.append("hallucination")
            if quality_res.completeness < 0.7: failures.append("incomplete_answer")
            if result.evaluation.citation_score < 0.7: failures.append("citation_error")
            if answerability == 0.0: failures.append("low_confidence")
            if total_latency > 15000: failures.append("timeout")

            # 6. Latency
            latency = LatencyBreakdown(
                retrieval_ms=winning_attempt.pipeline_ms, # Pipeline covers both right now
                rerank_ms=0,
                generation_ms=winning_attempt.generation_ms,
                evaluation_ms=winning_attempt.evaluation_ms,
                total_ms=total_latency
            )

            record = QueryEvaluationRecord(
                query_id=item.id,
                query=item.query,
                generated_answer=result.answer,
                ground_truth=item.ground_truth_answer,
                retrieved_chunk_ids=retrieved_ids,
                retrieval_strategy=result.metadata.selected_strategy,
                faithfulness_score=result.evaluation.faithfulness_score,
                citation_score=result.evaluation.citation_score,
                answer_quality_score=quality_res.score,
                answer_correctness=quality_res.correctness,
                answer_completeness=quality_res.completeness,
                answer_clarity=quality_res.clarity,
                answer_groundedness=quality_res.groundedness,
                answerability_score=answerability,
                recall_at_1=recall_1,
                recall_at_3=recall_3,
                recall_at_5=recall_5,
                mrr=mrr,
                ndcg=ndcg,
                context_precision=ctx_prec,
                latency=latency,
                failures=failures,
                passed=passed
            )
            records.append(record)
            
        summary = self._aggregate_results(records)
        self._save_reports(summary, records, output_dir)
        return summary

    def _aggregate_results(self, records: List[QueryEvaluationRecord]) -> BenchmarkSummary:
        total = len(records)
        config = ExperimentConfig(
            embedding_model=settings.embedding_model,
            chunk_size=300, # Example hardcode or could pull from config
            reranker="cross-encoder/ms-marco-MiniLM-L-6-v2",
            retrieval_strategy="adaptive",
            prompt_version="v1.1"
        )
        if total == 0:
            return BenchmarkSummary(
                total_queries=0, config=config, avg_faithfulness=0, avg_citation_correctness=0,
                avg_answer_quality=0, avg_answerability=0,
                recall_at_1=0, recall_at_3=0, recall_at_5=0, avg_mrr=0, avg_ndcg=0, avg_context_precision=0,
                hallucination_rate=0, no_answer_rate=0, avg_total_latency_ms=0, failure_counts={}
            )

        no_answer_count = sum(1 for r in records if "not available in the provided documents" in r.generated_answer.lower())
        hallucination_count = sum(1 for r in records if "hallucination" in r.failures)
        
        failure_counts = {}
        for r in records:
            for f in r.failures:
                failure_counts[f] = failure_counts.get(f, 0) + 1

        return BenchmarkSummary(
            total_queries=total,
            config=config,
            avg_faithfulness=sum(r.faithfulness_score for r in records) / total,
            avg_citation_correctness=sum(r.citation_score for r in records) / total,
            avg_answer_quality=sum(r.answer_quality_score for r in records) / total,
            avg_answerability=sum(r.answerability_score for r in records) / total,
            recall_at_1=sum(r.recall_at_1 for r in records) / total,
            recall_at_3=sum(r.recall_at_3 for r in records) / total,
            recall_at_5=sum(r.recall_at_5 for r in records) / total,
            avg_mrr=sum(r.mrr for r in records) / total,
            avg_ndcg=sum(r.ndcg for r in records) / total,
            avg_context_precision=sum(r.context_precision for r in records) / total,
            hallucination_rate=hallucination_count / total,
            no_answer_rate=no_answer_count / total,
            avg_total_latency_ms=sum(r.latency.total_ms for r in records) / total,
            failure_counts=failure_counts
        )

    def _save_reports(self, summary: BenchmarkSummary, records: List[QueryEvaluationRecord], output_dir: str) -> None:
        os.makedirs(os.path.join(output_dir, "reports"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "results"), exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON Summary
        summary_path = os.path.join(output_dir, "reports", f"summary_{timestamp}.json")
        with open(summary_path, "w") as f:
            json.dump(summary.model_dump(), f, indent=2)
            
        # JSON Detailed
        details_path = os.path.join(output_dir, "results", f"detailed_{timestamp}.json")
        with open(details_path, "w") as f:
            json.dump([r.model_dump() for r in records], f, indent=2)
            
        # CSV Leaderboard
        csv_path = os.path.join(output_dir, "reports", f"leaderboard_{timestamp}.csv")
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Query ID", "Passed", "Strategy", "Ans Quality", "Faithfulness", "Citation", 
                "Recall@5", "MRR", "Latency (ms)", "Failures"
            ])
            for r in records:
                writer.writerow([
                    r.query_id, r.passed, r.retrieval_strategy, f"{r.answer_quality_score:.2f}", 
                    f"{r.faithfulness_score:.2f}", f"{r.citation_score:.2f}", 
                    f"{r.recall_at_5:.2f}", f"{r.mrr:.2f}", r.latency.total_ms, "|".join(r.failures)
                ])
                
        logger.info(f"Evaluation reports saved to {output_dir}")
