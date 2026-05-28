"""
Adaptive Orchestrator implementing self-healing, evaluation-driven RAG logic.
Detects hallucinations via SelfEvaluator and dynamically retries alternate retrieval strategies.
"""

import logging
import time
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.services.routing.routing_service import RetrievalPipeline
from src.generation.answer_generator import AnswerGenerator
from src.evaluation.evaluator import SelfEvaluator
from src.retrieval_filtering.confidence_analyzer import RetrievalConfidenceAnalyzer
from src.retrieval_filtering.chunk_filters import ChunkFilters
from src.generation.models import GeneratedAnswer
from src.evaluation.models import EvaluationResult
from app.services.orchestration.models import (
    OrchestratedResponse,
    AttemptMetadata,
    OrchestrationMetadata
)

logger = logging.getLogger(__name__)


class AdaptiveRAGOrchestrator:
    """Production-grade orchestrator that evaluates and retries RAG generation if quality is poor."""

    def __init__(
        self,
        retrieval_pipeline: RetrievalPipeline,
        answer_generator: AnswerGenerator,
        self_evaluator: SelfEvaluator,
        faithfulness_threshold: float = 0.7,
        max_retries: int = 2
    ) -> None:
        """
        Initializes the self-healing orchestrator.

        Args:
            retrieval_pipeline: Configured 2-stage retrieval pipeline.
            answer_generator: LLM generation service.
            self_evaluator: LLM-as-a-Judge evaluation service.
            faithfulness_threshold: Minimum score required to accept an answer.
            max_retries: Maximum number of retries allowed (total attempts = max_retries + 1).
        """
        self.retrieval_pipeline = retrieval_pipeline
        self.answer_generator = answer_generator
        self.self_evaluator = self_evaluator
        self.faithfulness_threshold = faithfulness_threshold
        self.max_retries = max_retries
        self.confidence_analyzer = RetrievalConfidenceAnalyzer()

        # Pre-defined deterministic retry order when forced
        self.retry_order = ["dense", "hybrid", "bm25"]
        
        logger.info(f"Initialized AdaptiveRAGOrchestrator (threshold={faithfulness_threshold}, max_retries={max_retries})")

    def _select_best_attempt(self, all_responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Selects the best historical attempt if all retries failed the threshold.
        Prioritizes faithfulness_score, then tie-breaks on citation_score.
        """
        def sort_key(resp: Dict[str, Any]) -> tuple:
            # Prefer responses that actually generated an answer
            skipped = resp.get("llm_generation_skipped", False)
            eval_res = resp["evaluation"]
            return (not skipped, eval_res.faithfulness_score, eval_res.citation_score)

        sorted_responses = sorted(all_responses, key=sort_key, reverse=True)
        return sorted_responses[0]

    def execute_query(self, user_query: str, k: int = 10, top_k: int = 3, strategy: str = "auto") -> OrchestratedResponse:
        """
        Executes the full adaptive, self-healing RAG flow.

        Args:
            user_query: User search query.
            k: Stage-1 recall candidate pool size.
            top_k: Stage-2 final precise chunk count for generation.
            strategy: Explicit strategy or 'auto'.

        Returns:
            OrchestratedResponse containing the best answer, citations, evaluation, and retry metadata.
        """
        if not user_query.strip():
            raise ValueError("Query cannot be empty.")

        logger.info(f"--- Starting Orchestrated Execution for: '{user_query}' ---")

        all_responses: List[Dict[str, Any]] = []
        attempt_logs: List[AttemptMetadata] = []
        
        if strategy != "auto" and strategy in ["dense", "bm25", "hybrid"]:
            retry_order = [strategy]
            total_attempts_allowed = 1
        else:
            retry_order = self.retry_order
            total_attempts_allowed = self.max_retries + 1

        for attempt in range(1, total_attempts_allowed + 1):
            current_strategy = retry_order[attempt - 1]
            logger.info(f"[INFO] Attempt {attempt} using {current_strategy} retrieval")

            # 1. Retrieve & Re-Rank
            t0 = time.time()
            pipeline_res = self.retrieval_pipeline.search(
                query=user_query,
                k=k,
                top_k=top_k,
                force_strategy=current_strategy
            )
            pipeline_ms = int((time.time() - t0) * 1000)
            
            # Deduplicate chunks
            pipeline_res.results = ChunkFilters.deduplicate(pipeline_res.results)

            # Analyze Retrieval Confidence
            confidence = self.confidence_analyzer.analyze(pipeline_res.results)

            generation_ms = 0
            evaluation_ms = 0

            if not confidence.is_confident:
                logger.warning(f"[WARNING] Retrieval confidence is LOW: {confidence.reason}. Skipping LLM generation.")
                gen_res = GeneratedAnswer(
                    answer="The information is not available in the provided documents.",
                    citations={},
                    invalid_citations_detected=[]
                )
                eval_res = EvaluationResult(
                    faithfulness_score=1.0,
                    citation_score=1.0,
                    issues=["Retrieval confidence was too low. Answer generation skipped."]
                )
                llm_generation_skipped = True
                filter_reason = confidence.reason
            else:
                llm_generation_skipped = False
                filter_reason = None
                
                # 2. Generate Grounded Answer
                t1 = time.time()
                gen_res = self.answer_generator.generate_answer(user_query, pipeline_res.results)
                generation_ms = int((time.time() - t1) * 1000)
                logger.info("[INFO] Answer generation completed")

                # 3. Evaluate Faithfulness & Citations
                t2 = time.time()
                eval_res = self.self_evaluator.evaluate(user_query, gen_res.answer, gen_res.citations)
                evaluation_ms = int((time.time() - t2) * 1000)
                logger.info(f"[INFO] Faithfulness score: {eval_res.faithfulness_score} | Citation score: {eval_res.citation_score}")

            # 4. Store attempt data
            response_data = {
                "answer": gen_res.answer,
                "citations": gen_res.citations,
                "evaluation": eval_res,
                "strategy": current_strategy,
                "chunks": pipeline_res.results,
                "llm_generation_skipped": llm_generation_skipped
            }
            all_responses.append(response_data)

            # 5. Decide to Return or Retry
            retry_needed = (not confidence.is_confident) or (eval_res.faithfulness_score < self.faithfulness_threshold)
            retry_triggered = retry_needed and attempt < total_attempts_allowed

            attempt_logs.append(AttemptMetadata(
                attempt_number=attempt,
                strategy=current_strategy,
                faithfulness_score=eval_res.faithfulness_score,
                citation_score=eval_res.citation_score,
                retry_triggered=retry_triggered,
                retrieval_quality=confidence.retrieval_quality,
                retrieval_confidence_score=confidence.confidence_score,
                llm_generation_skipped=llm_generation_skipped,
                filter_reason=filter_reason,
                pipeline_ms=pipeline_ms,
                generation_ms=generation_ms,
                evaluation_ms=evaluation_ms
            ))

            if retry_needed:
                if retry_triggered:
                    logger.warning(f"[WARNING] Quality below threshold. Retrying...")
                else:
                    logger.warning(f"[WARNING] Max retries reached. All attempts failed threshold.")
            else:
                logger.info(f"[INFO] Accepting answer from attempt {attempt}. Quality meets thresholds.")
                break

        # 6. Build Final Response
        best_response = self._select_best_attempt(all_responses)
        winning_strategy = best_response["strategy"]
        total_retries = len(attempt_logs) - 1
        
        logger.info(f"--- Orchestration Finished | Winner Strategy: {winning_strategy} | Total Retries: {total_retries} ---")

        metadata = OrchestrationMetadata(
            attempts=attempt_logs,
            selected_strategy=winning_strategy,
            total_retries=total_retries
        )

        return OrchestratedResponse(
            answer=best_response["answer"],
            citations=best_response["citations"],
            evaluation=best_response["evaluation"],
            metadata=metadata,
            chunks=best_response["chunks"]
        )
