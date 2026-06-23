"""
Main evaluator service executing the LLM-as-a-Judge self-verification step.
Analyzes generated answers against retrieved context to produce faithfulness and citation scores.
"""

import os
import time
import logging
from typing import Dict, Any, Optional
from openai import OpenAI
from app.core.config import settings
from src.evaluation.models import EvaluationResult
from src.evaluation.prompts import EvaluatorPrompts
from src.evaluation.metrics import EvaluationMetricsParser

logger = logging.getLogger(__name__)


class SelfEvaluator:
    """Evaluates RAG generated answers for grounding and citation accuracy."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.0
    ) -> None:
        """
        Initializes the OpenAI client for the evaluator. 
        Uses temperature=0.0 for maximum consistency and deterministic JSON formatting.
        """
        self.model_name = model_name or settings.gemini_model or "gpt-4o-mini"
        self.api_key = api_key or settings.gemini_api_key or os.environ.get("OPENAI_API_KEY", "dummy_key")
        self.base_url = base_url or settings.openai_base_url
        self.temperature = temperature

        logger.info(f"Initializing SelfEvaluator (Model: {self.model_name}, Temp: {self.temperature})")
        
        try:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client for SelfEvaluator: {e}")
            raise RuntimeError(f"SelfEvaluator initialization error: {e}")

    def evaluate(
        self,
        query: str,
        answer: str,
        citation_mapping: Dict[str, str]
    ) -> EvaluationResult:
        """
        Executes the LLM evaluation to score faithfulness and citation correctness.

        Args:
            query: Original search query.
            answer: Generated LLM answer.
            citation_mapping: Dictionary mapping citation IDs to chunk text.

        Returns:
            EvaluationResult detailing the self-verification scores and detected issues.
        """
        logger.info(f"Starting self-evaluation for query: '{query}'")
        start_time = time.time()

        system_prompt = EvaluatorPrompts.SYSTEM_PROMPT
        user_prompt = EvaluatorPrompts.build_user_prompt(query, answer, citation_mapping)

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature
            )
            raw_eval = response.choices[0].message.content or ""
            
        except Exception as e:
            logger.error(f"Evaluator LLM API call failed: {e}")
            return EvaluationResult(
                faithfulness_score=0.0,
                citation_score=0.0,
                issues=[f"Evaluator API failed: {str(e)}"]
            )

        # Parse and validate the JSON response
        eval_result = EvaluationMetricsParser.parse_llm_response(raw_eval)
        
        duration = time.time() - start_time
        logger.info(f"Evaluation completed in {duration:.2f}s. Faithfulness: {eval_result.faithfulness_score}, Citation: {eval_result.citation_score}")
        
        if eval_result.issues:
            logger.warning(f"Evaluator detected {len(eval_result.issues)} issues.")
            for issue in eval_result.issues:
                logger.warning(f"Issue: {issue}")

        return eval_result
