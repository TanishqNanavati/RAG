"""
Answer generator service executing LLM API calls and validating inline citations.
Designed with clean provider abstractions for future compatibility (OpenAI, Ollama, Anthropic, Groq).
"""

import re
import os
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI
from app.core.config import settings
from src.generation.models import GeneratedAnswer
from src.generation.prompt_template import PromptTemplate

logger = logging.getLogger(__name__)


class AnswerGenerator:
    """Service generating grounded LLM answers with validated inline citations."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.2
    ) -> None:
        """
        Initializes the LLM client and generation settings.
        Supports standard OpenAI as well as Gemini OpenAI-compatible endpoints.

        Args:
            model_name: LLM model identifier.
            api_key: API key.
            base_url: Base URL for OpenAI client.
            temperature: Sampling temperature.
        """
        # Default to gemini_model if using Google base URL, otherwise gpt-4o-mini
        self.model_name = model_name or settings.gemini_model or "gpt-4o-mini"
        self.api_key = api_key or settings.gemini_api_key or os.environ.get("OPENAI_API_KEY", "dummy_key")
        self.base_url = base_url or settings.openai_base_url
        self.temperature = temperature

        logger.info(f"Initializing AnswerGenerator (Model: {self.model_name}, Base URL: {self.base_url}, Temp: {self.temperature})")
        
        try:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            logger.info("OpenAI client initialized successfully for AnswerGenerator.")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise RuntimeError(f"LLM Client initialization error: {e}")

    def validate_citations(self, answer_text: str, valid_citations: Dict[str, str]) -> List[str]:
        """
        Scans the generated answer for citation tags and validates them against provided IDs.

        Args:
            answer_text: Raw answer string returned by the LLM.
            valid_citations: Dictionary mapping valid citation IDs (e.g. '[1]') to chunk text.

        Returns:
            List of any invalid citation tags hallucinated by the LLM.
        """
        # Find all citation tags like [1], [2], [12]
        found_tags = re.findall(r'\[\d+\]', answer_text)
        invalid_tags: List[str] = []

        for tag in found_tags:
            if tag not in valid_citations:
                invalid_tags.append(tag)
                logger.warning(f"Hallucinated/Invalid citation detected in LLM response: {tag}")

        if not invalid_tags:
            logger.info(f"Citation validation successful. All {len(found_tags)} inline citations match valid context chunks.")

        return invalid_tags

    def generate_answer(self, query: str, chunks: List[Any]) -> GeneratedAnswer:
        """
        Generates a grounded answer from retrieved chunks using the configured LLM API.

        Args:
            query: User search query.
            chunks: List of candidate chunk objects.

        Returns:
            GeneratedAnswer Pydantic model containing answer, citations, and validation metadata.
        """
        if not chunks:
            logger.warning("generate_answer called with empty chunk list. Returning insufficient context message.")
            return GeneratedAnswer(
                answer="The provided context is insufficient to answer the query.",
                citations={},
                invalid_citations_detected=[]
            )

        if not query or not query.strip():
            raise ValueError("Query cannot be empty for answer generation.")

        logger.info(f"Executing answer generation for query: '{query}' using {len(chunks)} chunks.")

        # 1. Create prompts and assign citation IDs
        system_prompt, user_prompt, citation_mapping = PromptTemplate.create_prompts(query, chunks)
        logger.info("Citation assignment complete. Sending request to LLM API.")

        try:
            # 2. Execute LLM API call
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature
            )
            
            raw_answer = response.choices[0].message.content or ""
            logger.info("LLM response received successfully.")

        except Exception as e:
            logger.error(f"LLM API generation failed: {e}")
            # Return graceful fallback without crashing pipeline
            return GeneratedAnswer(
                answer=f"An error occurred during LLM answer generation: {str(e)}",
                citations=citation_mapping,
                invalid_citations_detected=[]
            )

        # 3. Validate citations used by LLM
        invalid_citations = self.validate_citations(raw_answer, citation_mapping)

        # 4. Return structured response model
        return GeneratedAnswer(
            answer=raw_answer.strip(),
            citations=citation_mapping,
            invalid_citations_detected=invalid_citations
        )
