"""
Modular prompt template definitions for the LLM-as-a-Judge evaluation layer.
"""

import json
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class EvaluatorPrompts:
    """Encapsulates system and user prompt designs for strict RAG answer evaluation."""

    SYSTEM_PROMPT = """You are a strict, objective, and highly capable evaluator for a Retrieval-Augmented Generation (RAG) system.
Your sole task is to verify whether a generated answer is truthful to the provided context and whether its inline citations are used correctly.

CRITICAL INSTRUCTIONS:
1. NO OUTSIDE KNOWLEDGE: You must act as if you know nothing about the world. You only know what is in the provided context chunks.
2. DETECT HALLUCINATIONS: If the generated answer makes any claim, fact, or statement that is not explicitly present in the provided chunks, you must heavily penalize the faithfulness score and list the specific hallucinated claim in the issues list.
3. VERIFY CITATIONS: The generated answer contains inline citations like [1] or [2]. You must verify that the sentence immediately preceding the citation is actually supported by the specific chunk referenced by that ID. Penalize the citation score for weak, mismatched, or entirely missing citations.

OUTPUT FORMAT:
You must output ONLY valid JSON. Do not use markdown blocks (e.g., ```json). Return exactly this JSON structure:
{
  "faithfulness_score": <float between 0.0 and 1.0>,
  "citation_score": <float between 0.0 and 1.0>,
  "issues": ["<string describing specific hallucination or citation mismatch>", ...]
}"""

    @staticmethod
    def build_user_prompt(query: str, answer: str, citation_mapping: Dict[str, str]) -> str:
        """
        Constructs the user prompt containing the query, answer, and context chunks.

        Args:
            query: The original user search query.
            answer: The generated answer text to be evaluated.
            citation_mapping: Dictionary mapping citation IDs to chunk text.

        Returns:
            Formatted user prompt string.
        """
        context_blocks = []
        for cit_id, cit_text in citation_mapping.items():
            context_blocks.append(f"CHUNK {cit_id}:\n{cit_text}\n")
        
        formatted_context = "\n".join(context_blocks)

        user_prompt = f"""Evaluate the following generated answer based ONLY on the provided context chunks.

ORIGINAL USER QUERY:
{query}

PROVIDED CONTEXT CHUNKS:
{formatted_context if formatted_context else "NO CONTEXT PROVIDED."}

GENERATED ANSWER TO EVALUATE:
{answer}

Evaluate the faithfulness and citation correctness, and provide the JSON output now."""

        logger.debug(f"Built evaluator user prompt for query: '{query}'")
        return user_prompt
