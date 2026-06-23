"""
LLM-as-a-Judge module to evaluate answer quality compared to ground truth.
"""

import logging
import json
import re
from pydantic import BaseModel, Field
from openai import OpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)


class AnswerQualityScore(BaseModel):
    correctness: float = Field(..., description="Semantic correctness score from 0.0 to 1.0.")
    completeness: float = Field(..., description="Completeness score from 0.0 to 1.0.")
    clarity: float = Field(..., description="Clarity score from 0.0 to 1.0.")
    groundedness: float = Field(..., description="Groundedness score from 0.0 to 1.0.")
    score: float = Field(..., description="Overall normalized quality score from 0.0 to 1.0.")
    reasoning: str = Field(..., description="Brief reasoning for the given scores.")


class LLMAnswerJudge:
    """Uses an LLM to compare generated answers against ground-truth answers."""

    def __init__(self, temperature: float = 0.0) -> None:
        self.client = OpenAI(
            base_url=settings.openai_base_url,
            api_key=settings.gemini_api_key,
        )
        self.model = settings.gemini_model
        self.temperature = temperature

    def evaluate(self, query: str, generated_answer: str, ground_truth: str) -> AnswerQualityScore:
        if not ground_truth.strip():
            return AnswerQualityScore(correctness=1.0, completeness=1.0, clarity=1.0, groundedness=1.0, score=1.0, reasoning="No ground truth provided.")

        if "not available in the provided documents" in generated_answer.lower():
            return AnswerQualityScore(
                correctness=0.0, completeness=0.0, clarity=1.0, groundedness=1.0, score=0.0, 
                reasoning="Model gracefully declined to answer. Counted as 0 for correctness/completeness."
            )

        prompt = f"""You are an expert judge evaluating RAG system output.
Compare the GENERATED ANSWER to the GROUND TRUTH for the given QUERY.

QUERY: {query}
GROUND TRUTH: {ground_truth}
GENERATED ANSWER: {generated_answer}

INSTRUCTIONS:
Evaluate the answer on the following metrics (each 0.0 to 1.0):
1. correctness: Is it semantically correct ignoring minor wording?
2. completeness: Does it contain all key facts from the ground truth?
3. clarity: Is it easy to read and understand?
4. groundedness: Does it avoid hallucinating outside facts?
5. score: The overall average quality score.

IMPORTANT: Return your evaluation as a strict JSON object with NO markdown formatting, NO triple backticks, and NO other text:
{{
    "correctness": 0.9,
    "completeness": 0.8,
    "clarity": 1.0,
    "groundedness": 0.9,
    "score": 0.9,
    "reasoning": "Explanation here"
}}
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature
            )
            raw_text = response.choices[0].message.content or "{}"
            raw_text = raw_text.strip()
            if raw_text.startswith("```json"): raw_text = raw_text[7:]
            if raw_text.startswith("```"): raw_text = raw_text[3:]
            if raw_text.endswith("```"): raw_text = raw_text[:-3]
                
            data = json.loads(raw_text.strip())
            return AnswerQualityScore(
                correctness=float(data.get("correctness", 0.0)),
                completeness=float(data.get("completeness", 0.0)),
                clarity=float(data.get("clarity", 0.0)),
                groundedness=float(data.get("groundedness", 0.0)),
                score=float(data.get("score", 0.0)),
                reasoning=str(data.get("reasoning", "Parsed reasoning."))
            )
        except Exception as e:
            logger.error(f"Answer judge evaluation failed: {e}")
            return AnswerQualityScore(correctness=0.0, completeness=0.0, clarity=0.0, groundedness=0.0, score=0.0, reasoning=f"Failed: {str(e)}")
