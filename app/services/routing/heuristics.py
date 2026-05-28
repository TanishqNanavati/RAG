"""
Rule-based routing heuristics determining the optimal retrieval strategy.
"""

import logging
from typing import Tuple
from app.services.routing.schemas import QueryFeatures

logger = logging.getLogger(__name__)


class RoutingHeuristics:
    """Evaluates query features against modular routing rules."""

    @staticmethod
    def evaluate(features: QueryFeatures) -> Tuple[str, str]:
        """
        Applies routing rules to determine strategy and human-readable explanation.

        Args:
            features: QueryFeatures Pydantic model containing extracted indicators.

        Returns:
            Tuple of (strategy_name, explanation_reason).
        """
        # RULE 3 — HYBRID RETRIEVAL
        # Use Hybrid if it's a comparison query or a complex technical semantic query
        if features.is_comparison_query:
            reason = "Comparative query detected requiring both exact entity matching and semantic evaluation."
            logger.info(f"Routing strategy selected: hybrid. Reason: {reason}")
            return "hybrid", reason

        if features.has_technical_terms and features.is_semantic_query and not features.is_short_query:
            reason = "Complex technical query detected with mixed semantic and keyword intent."
            logger.info(f"Routing strategy selected: hybrid. Reason: {reason}")
            return "hybrid", reason

        # RULE 1 — BM25 RETRIEVAL
        # Use BM25 if it's a short factual query, acronym-heavy, or exact entity lookup
        if features.contains_acronym and features.is_short_query:
            reason = "Short acronym-heavy factual query requiring exact keyword precision."
            logger.info(f"Routing strategy selected: bm25. Reason: {reason}")
            return "bm25", reason

        if features.is_short_query and not features.contains_question_words:
            reason = "Short factual keyword lookup without natural language question semantics."
            logger.info(f"Routing strategy selected: bm25. Reason: {reason}")
            return "bm25", reason

        # RULE 2 — DENSE RETRIEVAL
        # Default fallback for natural language questions, long sentences, and explanatory intent
        if features.is_semantic_query or features.contains_question_words:
            reason = "Natural language question requiring deep semantic understanding and conceptual matching."
            logger.info(f"Routing strategy selected: dense. Reason: {reason}")
            return "dense", reason

        # Fallback default
        reason = "Defaulting to dense semantic retrieval for general natural language query."
        logger.info(f"Routing strategy selected: dense. Reason: {reason}")
        return "dense", reason
