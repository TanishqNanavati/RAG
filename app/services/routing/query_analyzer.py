"""
Query analyzer service extracting linguistic, structural, and semantic features.
"""

import re
import logging
from typing import Dict, Any, Set
from app.services.routing.schemas import QueryFeatures

logger = logging.getLogger(__name__)


class QueryAnalyzer:
    """Analyzes search queries to extract routing features using regex and heuristics."""

    def __init__(self) -> None:
        """Initializes domain keyword sets and regex patterns."""
        self.question_words: Set[str] = {"how", "what", "why", "when", "where", "which", "who", "whom", "whose"}
        self.comparison_words: Set[str] = {"compare", "comparison", "differ", "differs", "difference", "versus", "vs", "better", "worse", "against"}
        self.technical_terms: Set[str] = {
            "rover", "telescope", "radiation", "habitat", "orbit", "trajectory", "infrared",
            "lunar", "solar", "microbial", "core", "atmosphere", "exoplanet", "lagrange", "instrument",
            "autonomous", "lethal", "oversight", "privacy", "consent", "dilemma", "moral"
        }
        # Matches uppercase acronyms of 2+ characters
        self.acronym_pattern = re.compile(r'\b[A-Z]{2,}\b')
        logger.info("Initialized QueryAnalyzer")

    def analyze(self, query: str) -> QueryFeatures:
        """
        Processes a raw query string into structured QueryFeatures.

        Args:
            query: Raw input search query string.

        Returns:
            QueryFeatures Pydantic model populated with extracted indicators.
        """
        if not query or not query.strip():
            logger.warning("QueryAnalyzer received empty query.")
            return QueryFeatures(
                token_count=0, contains_acronym=False, is_short_query=True,
                has_technical_terms=False, is_semantic_query=False,
                contains_question_words=False, is_comparison_query=False
            )

        clean_query = query.strip()
        tokens = clean_query.split()
        token_count = len(tokens)
        lower_tokens = set(t.lower() for t in tokens)

        # 1. Length features
        is_short_query = token_count <= 4

        # 2. Acronym detection
        contains_acronym = bool(self.acronym_pattern.search(clean_query))

        # 3. Technical terms detection
        has_technical_terms = bool(lower_tokens.intersection(self.technical_terms))

        # 4. Question words detection
        contains_question_words = bool(lower_tokens.intersection(self.question_words))

        # 5. Comparison intent detection
        is_comparison_query = bool(lower_tokens.intersection(self.comparison_words))

        # 6. Semantic intent indicator (either explicit question words or long explanatory sentence)
        is_semantic_query = contains_question_words or token_count >= 6

        features = QueryFeatures(
            token_count=token_count,
            contains_acronym=contains_acronym,
            is_short_query=is_short_query,
            has_technical_terms=has_technical_terms,
            is_semantic_query=is_semantic_query,
            contains_question_words=contains_question_words,
            is_comparison_query=is_comparison_query
        )

        logger.debug(f"Query analyzed: {features.model_dump()}")
        return features
