"""
FastAPI routes for Phase 11 Complete RAG System API Layer.
Exposes the fully orchestrated, self-healing pipeline via production-ready REST endpoints.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.security import get_current_user
from app.models.user import User, GuestUsage
from app.models.chat import ChatSession

from app.core.db import get_db, engine, Base
from app.services.cache.redis_cache import RedisSemanticCache
from app.services.orchestration.conversation_manager import ConversationManager
from app.services.dense_retrieval.embedding_service import EmbeddingService
from app.services.dense_retrieval.dense_retriever import DenseRetriever
from app.services.bm25_retrieval.bm25_retriever import BM25Retriever
from app.services.hybrid_retrieval.hybrid_retriever import HybridRetriever
from app.services.routing.strategy_router import RuleBasedRouter
from app.services.routing.routing_service import RoutingService, RetrievalPipeline
from app.reranking.reranker import CrossEncoderReRanker
from src.generation.answer_generator import AnswerGenerator
from src.evaluation.evaluator import SelfEvaluator
from src.evaluation.models import EvaluationResult
from app.services.orchestration.orchestrator import AdaptiveRAGOrchestrator

logger = logging.getLogger(__name__)
router = APIRouter()

# Create DB Tables on Startup
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
except Exception as e:
    logger.error(f"Failed to initialize database tables: {e}")

# Singletons (initialized once per app startup)
from app.core.shared_state import embedding_service, dense_retriever, bm25_retriever, hybrid_retriever

try:
    rule_router = RuleBasedRouter()
    routing_service = RoutingService(dense_retriever, bm25_retriever, hybrid_retriever, rule_router)
    cross_encoder = CrossEncoderReRanker()
    pipeline = RetrievalPipeline(routing_service, reranker=cross_encoder, enable_reranking=True)
    answer_generator = AnswerGenerator(temperature=0.2)
    self_evaluator = SelfEvaluator(temperature=0.0)
    orchestrator = AdaptiveRAGOrchestrator(
        retrieval_pipeline=pipeline,
        answer_generator=answer_generator,
        self_evaluator=self_evaluator,
        faithfulness_threshold=0.7,
        max_retries=2
    )
    redis_cache = RedisSemanticCache()
    conversation_manager = ConversationManager()
except Exception as e:
    logger.critical(f"Failed to initialize core RAG components during startup: {e}")
    orchestrator = None


class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    strategy: Optional[str] = "auto"


class CitationDetail(BaseModel):
    chunk_id: str
    text: str


class Scores(BaseModel):
    faithfulness: float
    citation_correctness: float


class RetrievalConfidence(BaseModel):
    score: Optional[float]
    quality: Optional[str]


class LatencyMetrics(BaseModel):
    pipeline_ms: int
    generation_ms: int
    evaluation_ms: int
    total_ms: int


class QueryMetadata(BaseModel):
    retries: int
    selected_strategy: str
    latencies: LatencyMetrics
    retrieval_filtered: bool
    filter_reason: Optional[str]


class QueryResponse(BaseModel):
    query: str
    session_id: Optional[str] = None
    answer: str
    citations: Dict[str, CitationDetail]
    strategy_used: str
    scores: Scores
    retrieval_confidence: RetrievalConfidence
    metadata: QueryMetadata
    is_cached: bool = False


class DebugResponse(BaseModel):
    query: str
    retrieval_strategy: str
    retrieval_confidence: RetrievalConfidence
    generation_skipped: bool
    reason: Optional[str]
    retrieved_chunks: List[Dict[str, Any]]
    reranked_chunks: List[Dict[str, Any]]
    generated_answer: str
    evaluation: Dict[str, Any]
    orchestrator_log: List[str]


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: str


class SessionResponse(BaseModel):
    id: str
    title: Optional[str] = None
    created_at: str


class SessionUpdate(BaseModel):
    title: str


@router.post("/query", response_model=QueryResponse, summary="Execute Full RAG Pipeline")
async def execute_query(
    request: QueryRequest,
    x_session_id: str = Header(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> QueryResponse:
    """
    Main entry point for grounded question answering.
    Executes query rewriting, caching, retrieval, generation, evaluation, and saves history.
    """
    if orchestrator is None:
        raise HTTPException(status_code=500, detail="RAG Orchestrator failed to initialize.")

    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    if not current_user:
        session_id_to_use = x_session_id or request.session_id
        if not session_id_to_use:
            raise HTTPException(status_code=400, detail="X-Session-ID header or session_id in body required for guests.")
        guest = db.query(GuestUsage).filter(GuestUsage.session_id == session_id_to_use).first()
        if not guest:
            guest = GuestUsage(session_id=session_id_to_use)
            db.add(guest)
            db.commit()
            db.refresh(guest)
        if guest.message_count >= 3:
            raise HTTPException(status_code=403, detail="Guest message limit reached. Please log in.")
        guest.message_count += 1
        db.commit()
        user_id_param = None
    else:
        user_id_param = current_user.id

    try:
        start_time = time.time()
        
        # 1. Conversation History & Query Rewriting
        target_query = request.query
        if request.session_id:
            target_query = conversation_manager.rewrite_query(db, request.session_id, request.query)

        cache_key = f"{target_query}::{request.strategy}"

        # 2. Redis Cache Lookup
        cached_response = redis_cache.get(cache_key)
        if cached_response:
            # Reconstruct response payload
            response_payload = QueryResponse(**cached_response)
            response_payload.is_cached = True
            
            # Save user interaction to DB even on Cache Hit
            if request.session_id:
                conversation_manager.add_message(db, request.session_id, "user", request.query, user_id=user_id_param)
                conversation_manager.add_message(db, request.session_id, "assistant", response_payload.answer, user_id=user_id_param)
            
            return response_payload

        # 3. Cache Miss: Execute RAG Pipeline
        result = orchestrator.execute_query(target_query, strategy=request.strategy)
        total_time_ms = int((time.time() - start_time) * 1000)

        # Reconstruct structured citations with exact chunk mappings
        citation_details = {}
        for cit_id, cit_text in result.citations.items():
            chunk_id = "unknown"
            for chunk in result.chunks:
                chunk_text = getattr(chunk, "text", "") if hasattr(chunk, "text") else chunk.get("text", "")
                if chunk_text == cit_text:
                    chunk_id = getattr(chunk, "id", "unknown") if hasattr(chunk, "id") else chunk.get("id", "unknown")
                    break
            citation_details[cit_id] = CitationDetail(chunk_id=chunk_id, text=cit_text)

        winning_attempt = next((a for a in result.metadata.attempts if a.strategy == result.metadata.selected_strategy), result.metadata.attempts[-1])

        response_payload = QueryResponse(
            query=request.query,
            session_id=request.session_id,
            answer=result.answer,
            citations=citation_details,
            strategy_used=result.metadata.selected_strategy,
            scores=Scores(
                faithfulness=result.evaluation.faithfulness_score,
                citation_correctness=result.evaluation.citation_score
            ),
            retrieval_confidence=RetrievalConfidence(
                score=winning_attempt.retrieval_confidence_score,
                quality=winning_attempt.retrieval_quality
            ),
            metadata=QueryMetadata(
                retries=result.metadata.total_retries,
                selected_strategy=result.metadata.selected_strategy,
                latencies=LatencyMetrics(
                    pipeline_ms=winning_attempt.pipeline_ms,
                    generation_ms=winning_attempt.generation_ms,
                    evaluation_ms=winning_attempt.evaluation_ms,
                    total_ms=total_time_ms
                ),
                retrieval_filtered=winning_attempt.llm_generation_skipped,
                filter_reason=winning_attempt.filter_reason
            ),
            is_cached=False
        )

        # 4. Save to Database
        if request.session_id:
            conversation_manager.add_message(db, request.session_id, "user", request.query, user_id=user_id_param)
            conversation_manager.add_message(db, request.session_id, "assistant", result.answer, user_id=user_id_param)

        # 5. Save to Cache
        redis_cache.set(cache_key, response_payload.model_dump())

        return response_payload
    except Exception as e:
        logger.error(f"Full RAG pipeline failed: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/history/{session_id}", response_model=List[MessageResponse], summary="Retrieve Chat Session History")
async def get_chat_history(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves conversation history from SQLite."""
    from app.models.chat import ChatSession
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if session and session.user_id:
        if not current_user or session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to view this session.")
            
    history = conversation_manager.get_history(db, session_id, limit=50)
    return [
        MessageResponse(
            id=msg.id,
            role=msg.role,
            content=msg.content,
            created_at=msg.created_at.isoformat()
        )
        for msg in history
    ]


@router.get("/sessions", response_model=List[SessionResponse], summary="Retrieve User Chat Sessions")
async def get_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve all chat sessions for the logged-in user."""
    from app.models.chat import ChatSession
    sessions = db.query(ChatSession).filter(ChatSession.user_id == current_user.id).order_by(ChatSession.created_at.desc()).all()
    return [
        SessionResponse(
            id=s.id,
            title=s.title,
            created_at=s.created_at.isoformat()
        )
        for s in sessions
    ]


@router.put("/sessions/{session_id}", response_model=SessionResponse, summary="Rename Chat Session")
async def update_session(
    session_id: str,
    update: SessionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update the title of a chat session."""
    from app.models.chat import ChatSession
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session.title = update.title
    db.commit()
    db.refresh(session)
    return SessionResponse(
        id=session.id,
        title=session.title,
        created_at=session.created_at.isoformat()
    )


@router.post("/query/evaluation-only", response_model=EvaluationResult, summary="Run Evaluation Only")
@router.post("/debug", response_model=DebugResponse, summary="Debugging Endpoint for Full RAG Pipeline")
async def debug_query(request: QueryRequest) -> DebugResponse:
    if orchestrator is None:
        raise HTTPException(status_code=500, detail="RAG Orchestrator failed to initialize.")

    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        result = orchestrator.execute_query(request.query)
        
        reranked_chunks_debug = []
        for chunk in result.chunks:
            c_dict = {
                "chunk_id": getattr(chunk, "id", "unknown"),
                "text": getattr(chunk, "text", ""),
                "score": getattr(chunk, "score", 0.0),
                "rerank_score": getattr(chunk, "rerank_score", None)
            }
            reranked_chunks_debug.append(c_dict)

        orchestrator_log = []
        for attempt in result.metadata.attempts:
            orchestrator_log.append(
                f"Attempt {attempt.attempt_number} using {attempt.strategy} retrieval "
                f"(Faithfulness: {attempt.faithfulness_score}, Citation: {attempt.citation_score})"
            )
            if attempt.retry_triggered:
                orchestrator_log.append("Evaluation failed threshold. Retrying...")
            else:
                orchestrator_log.append("Evaluation passed threshold or max retries reached. Answer accepted.")

        winning_attempt = next((a for a in result.metadata.attempts if a.strategy == result.metadata.selected_strategy), result.metadata.attempts[-1])

        return DebugResponse(
            query=request.query,
            retrieval_strategy=result.metadata.selected_strategy,
            retrieval_confidence=RetrievalConfidence(
                score=winning_attempt.retrieval_confidence_score,
                quality=winning_attempt.retrieval_quality
            ),
            generation_skipped=winning_attempt.llm_generation_skipped,
            reason=winning_attempt.filter_reason,
            retrieved_chunks=reranked_chunks_debug,
            reranked_chunks=reranked_chunks_debug,
            generated_answer=result.answer,
            evaluation={
                "faithfulness": result.evaluation.faithfulness_score,
                "citation_correctness": result.evaluation.citation_score,
                "issues": result.evaluation.issues
            },
            orchestrator_log=orchestrator_log
        )
    except Exception as e:
        logger.error(f"Debug pipeline failed: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
