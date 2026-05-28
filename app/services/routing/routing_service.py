"""
Central routing service and two-stage retrieval pipeline coordinating BaseRouter decisions,
underlying retrievers, and optional Cross-Encoder re-ranking.
"""

import logging
from typing import List, Dict, Any, Optional
from app.services.ingestion.schemas import DocumentChunk
from app.services.dense_retrieval.dense_retriever import DenseRetriever
from app.services.bm25_retrieval.bm25_retriever import BM25Retriever
from app.services.hybrid_retrieval.hybrid_retriever import HybridRetriever
from app.services.routing.strategy_router import BaseRouter, RuleBasedRouter
from app.services.routing.schemas import RoutedRetrievalResponse, RoutingDecision
from app.services.hybrid_retrieval.schemas import HybridRetrievedChunk
from app.reranking.interfaces import BaseReRanker
from app.reranking.reranker import CrossEncoderReRanker
from app.reranking.models import RerankedChunk

logger = logging.getLogger(__name__)


class RoutingService:
    """Service orchestrating dynamic query routing and retriever execution."""

    def __init__(
        self,
        dense_retriever: DenseRetriever,
        bm25_retriever: BM25Retriever,
        hybrid_retriever: HybridRetriever,
        router: BaseRouter = None
    ) -> None:
        self.dense_retriever = dense_retriever
        self.bm25_retriever = bm25_retriever
        self.hybrid_retriever = hybrid_retriever
        self.router: BaseRouter = router or RuleBasedRouter()
        logger.info("Initialized Central RoutingService")

    def add_documents(self, chunks: List[DocumentChunk]) -> int:
        if not chunks:
            logger.warning("RoutingService.add_documents called with empty chunk list.")
            return 0

        logger.info(f"RoutingService indexing {len(chunks)} chunks via HybridRetriever.")
        total_indexed = self.hybrid_retriever.add_documents(chunks)
        return total_indexed

    def route_query(self, query: str) -> RoutingDecision:
        return self.router.route(query)

    def search(self, query: str, k: int = 5, force_strategy: Optional[str] = None) -> RoutedRetrievalResponse:
        if not query.strip():
            raise ValueError("Search query cannot be empty.")

        logger.info(f'RoutingService executing search for query: "{query}" (k={k}, force_strategy={force_strategy})')

        if force_strategy:
            strategy = force_strategy
            reason = f"Forced retrieval strategy: {force_strategy} via Orchestrator."
            logger.info(reason)
        else:
            decision = self.router.route(query)
            strategy = decision.strategy
            reason = decision.reason
            logger.info(f"Selected strategy: {strategy}. Reason: {reason}")

        results: List[HybridRetrievedChunk] = []

        if strategy == "bm25":
            bm25_res = self.bm25_retriever.search(query, k=k)
            for r in bm25_res:
                results.append(HybridRetrievedChunk(
                    id=r.id,
                    text=r.text,
                    score=r.score,
                    dense_score=None,
                    bm25_score=r.score,
                    metadata=r.metadata,
                    retrieval_sources=["bm25"]
                ))

        elif strategy == "dense":
            dense_res = self.dense_retriever.search(query, k=k)
            for r in dense_res:
                results.append(HybridRetrievedChunk(
                    id=r.id,
                    text=r.text,
                    score=r.score,
                    dense_score=r.score,
                    bm25_score=None,
                    metadata=r.metadata,
                    retrieval_sources=["dense"]
                ))

        elif strategy == "hybrid":
            results = self.hybrid_retriever.search(query, k=k)

        else:
            raise RuntimeError(f"Unsupported routing strategy selected: '{strategy}'")

        logger.info(f"Retrieved {len(results)} chunks via '{strategy}' strategy.")

        return RoutedRetrievalResponse(
            query=query,
            strategy=strategy,
            reason=reason,
            results=results
        )


class RetrievalPipeline:
    """Production two-stage RAG pipeline combining Stage-1 Recall (Router+Retriever) and Stage-2 Precision (Re-Ranker)."""

    def __init__(
        self,
        routing_service: RoutingService,
        reranker: Optional[BaseReRanker] = None,
        enable_reranking: bool = True
    ) -> None:
        """
        Initializes the RetrievalPipeline with routing service and optional reranker.

        Args:
            routing_service: Instance of RoutingService.
            reranker: Instance of BaseReRanker (defaults to CrossEncoderReRanker).
            enable_reranking: Master toggle for Stage-2 re-ranking.
        """
        self.routing_service = routing_service
        self.enable_reranking = enable_reranking
        self.reranker = reranker or (CrossEncoderReRanker() if enable_reranking else None)
        logger.info(f"Initialized RetrievalPipeline (enable_reranking={enable_reranking})")

    def add_documents(self, chunks: List[DocumentChunk]) -> int:
        """Passes chunks to routing service for indexing."""
        return self.routing_service.add_documents(chunks)

    def route_query(self, query: str) -> RoutingDecision:
        """Passes query to routing service for strategy analysis."""
        return self.routing_service.route_query(query)

    def search(self, query: str, k: int = 10, top_k: int = 3, force_strategy: Optional[str] = None) -> RoutedRetrievalResponse:
        """
        Executes Stage-1 recall search (fetching k candidates) followed by optional
        Stage-2 CrossEncoder re-ranking (filtering down to top_k precise results).

        Args:
            query: User search query.
            k: Stage-1 recall candidate pool size.
            top_k: Stage-2 final precise chunk count.
            force_strategy: Optional retrieval strategy override.

        Returns:
            RoutedRetrievalResponse containing final re-ranked chunks.
        """
        logger.info(f"RetrievalPipeline executing search for query: '{query}' (recall k={k}, precision top_k={top_k}, force_strategy={force_strategy})")
        
        # Stage 1: Recall retrieval via Router or forced strategy
        stage1_response = self.routing_service.search(query, k=k, force_strategy=force_strategy)
        candidate_chunks = stage1_response.results

        # Stage 2: Precision Re-Ranking (Optional)
        final_results: List[RerankedChunk] = []

        if self.enable_reranking and self.reranker:
            logger.info("Stage-2 Re-Ranking enabled. Executing CrossEncoder rerank.")
            final_results = self.reranker.rerank(query, candidate_chunks, top_k=top_k)
        else:
            logger.info("Stage-2 Re-Ranking disabled/bypass. Returning Stage-1 candidate chunks.")
            # Convert HybridRetrievedChunk to RerankedChunk with rerank_score=None for schema consistency
            for c in candidate_chunks[:top_k]:
                final_results.append(RerankedChunk(**c.model_dump(), rerank_score=None))

        return RoutedRetrievalResponse(
            query=stage1_response.query,
            strategy=stage1_response.strategy,
            reason=stage1_response.reason,
            results=final_results
        )
