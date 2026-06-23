"""
Metrics utility module for LLM JSON parsing and validation.
Ensures evaluator outputs conform to the expected schema and gracefully handles LLM formatting errors.
"""

import json
import logging
import re
from typing import Any, Dict
from pydantic import ValidationError
from src.evaluation.models import EvaluationResult

logger = logging.getLogger(__name__)


class EvaluationMetricsParser:
    """Handles parsing and validation of the evaluator LLM response."""

    @staticmethod
    def parse_llm_response(raw_response: str) -> EvaluationResult:
        """
        Extracts JSON from the LLM response, handles common formatting issues,
        and validates it against the EvaluationResult Pydantic model.

        Args:
            raw_response: Raw text output from the evaluator LLM.

        Returns:
            EvaluationResult model.
        """
        cleaned_response = raw_response.strip()

        # Remove markdown JSON code blocks if the LLM ignored instructions
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
        
        cleaned_response = cleaned_response.strip()

        try:
            parsed_dict = json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode evaluator LLM JSON: {e}. Raw response: {raw_response}")
            # Fallback for completely mangled responses
            return EvaluationResult(
                faithfulness_score=0.0,
                citation_score=0.0,
                issues=[f"LLM output was not valid JSON: {str(e)}"]
            )

        try:
            # Validate through Pydantic
            eval_result = EvaluationResult(**parsed_dict)
            return eval_result
        except ValidationError as e:
            logger.error(f"Evaluator LLM JSON failed schema validation: {e}")
            return EvaluationResult(
                faithfulness_score=0.0,
                citation_score=0.0,
                issues=["LLM JSON output did not match expected EvaluationResult schema.", str(e)]
            )
