"""
Strategy router definitions establishing BaseRouter interface and RuleBasedRouter implementation.
Designed for future ML-router extensibility.
"""

import logging
from abc import ABC, abstractmethod
from app.services.routing.schemas import RoutingDecision
from app.services.routing.query_analyzer import QueryAnalyzer
from app.services.routing.heuristics import RoutingHeuristics

logger = logging.getLogger(__name__)


class BaseRouter(ABC):
    """Abstract base class defining the extensible query routing interface."""

    @abstractmethod
    def route(self, query: str) -> RoutingDecision:
        """
        Analyzes a query string and returns a structured RoutingDecision.

        Args:
            query: Input search query string.

        Returns:
            RoutingDecision Pydantic model.
        """
        pass


class RuleBasedRouter(BaseRouter):
    """Concrete router implementation applying QueryAnalyzer and RoutingHeuristics."""

    def __init__(self) -> None:
        """Initializes underlying query analyzer instance."""
        self.analyzer = QueryAnalyzer()
        logger.info("Initialized RuleBasedRouter")

    def route(self, query: str) -> RoutingDecision:
        """
        Executes query analysis and evaluates heuristics to select retrieval strategy.

        Args:
            query: Input search query string.

        Returns:
            RoutingDecision containing strategy, explanation reason, and query features.
        """
        if not query or not query.strip():
            raise ValueError("Routing query cannot be empty.")

        logger.info(f'Executing query routing for: "{query}"')
        
        # 1. Analyze query features
        features = self.analyzer.analyze(query)
        
        # 2. Apply rule-based heuristics
        strategy, reason = RoutingHeuristics.evaluate(features)

        decision = RoutingDecision(
            strategy=strategy,
            reason=reason,
            features=features
        )

        return decision
