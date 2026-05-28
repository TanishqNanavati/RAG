"""
FastAPI routes for Phase 6 Intelligent Query Routing and Phase 7 Cross-Encoder Re-Ranking APIs.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from app.services.dense_retrieval.embedding_service import EmbeddingService
from app.services.dense_retrieval.dense_retriever import DenseRetriever
from app.services.bm25_retrieval.bm25_retriever import BM25Retriever
from app.services.hybrid_retrieval.hybrid_retriever import HybridRetriever
from app.services.routing.strategy_router import RuleBasedRouter
from app.services.routing.routing_service import RoutingService, RetrievalPipeline
from app.services.routing.schemas import RoutingDecision, RouteRequest, RouteSearchRequest, RoutedRetrievalResponse
from app.reranking.models import RerankRequest, RerankResponse, RerankedChunk
from app.reranking.reranker import CrossEncoderReRanker

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/router", tags=["Query Router & Re-Ranker"])

# Dependency injection / Singleton initialization
from app.core.shared_state import dense_retriever, bm25_retriever, hybrid_retriever
rule_router = RuleBasedRouter()
routing_service = RoutingService(dense_retriever, bm25_retriever, hybrid_retriever, rule_router)
cross_encoder_reranker = CrossEncoderReRanker()
retrieval_pipeline = RetrievalPipeline(routing_service, reranker=cross_encoder_reranker, enable_reranking=True)


@router.post("/route", response_model=RoutingDecision, summary="Analyze Query and Select Strategy")
async def analyze_and_route_query(request: RouteRequest) -> RoutingDecision:
    logger.info(f"Received standalone routing request for query: '{request.query}'")
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        decision = retrieval_pipeline.route_query(request.query)
        return decision
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Routing analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Routing error: {str(e)}")


@router.post("/search", response_model=RoutedRetrievalResponse, summary="Two-Stage Routed Search & Re-Ranking")
async def intelligent_routed_search(request: RouteSearchRequest) -> RoutedRetrievalResponse:
    """
    Executes Stage-1 recall retrieval (BM25, Dense, or Hybrid) followed by Stage-2 Cross-Encoder re-ranking.
    """
    logger.info(f"Received intelligent routed search request for query: '{request.query}' (top_k={request.k})")
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty.")

    try:
        # Fetch larger candidate pool (k=10) then rerank down to top_k=request.k
        response = retrieval_pipeline.search(request.query, k=10, top_k=request.k)
        return response
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Routed search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Routed search error: {str(e)}")


@router.post("/rerank", response_model=RerankResponse, summary="Standalone Cross-Encoder Re-Ranking")
async def standalone_rerank(request: RerankRequest) -> RerankResponse:
    """
    Standalone endpoint accepting a query and candidate chunks, executing CrossEncoder inference,
    and returning re-scored and re-ordered results.
    """
    logger.info(f"Received standalone reranking request for query: '{request.query}' (chunks={len(request.chunks)})")
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        reranked = cross_encoder_reranker.rerank(request.query, request.chunks, top_k=request.top_k)
        return RerankResponse(query=request.query, results=reranked)
    except Exception as e:
        logger.error(f"Standalone reranking failed: {e}")
        raise HTTPException(status_code=500, detail=f"Reranking error: {str(e)}")
