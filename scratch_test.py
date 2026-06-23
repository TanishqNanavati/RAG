import asyncio
import logging
from app.services.orchestration.orchestrator import RAGOrchestrator
from app.services.dense_retrieval.dense_retriever import DenseRetriever
from app.services.bm25_retrieval.bm25_retriever import BM25Retriever
from app.services.hybrid_retrieval.hybrid_retriever import HybridRetriever
from app.services.hybrid_retrieval.score_fusion import ScoreFusionEngine
from app.reranking.cross_encoder import CrossEncoderReranker
from src.retrieval_filtering.confidence_analyzer import RetrievalConfidenceAnalyzer
from src.retrieval_filtering.chunk_filters import ExactDuplicateFilter
from src.generation.answer_generator import AnswerGenerator
from src.evaluation.evaluator import SelfEvaluator
from app.services.dense_retrieval.vector_store import faiss_store
from app.services.bm25_retrieval.bm25_index import bm25_store
from app.services.embeddings import EmbeddingService
from app.api.orchestration_routes import get_orchestrator
from app.api.ingestion_routes import ingest_document

async def test():
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Needs a document to be ingested first
    # So we bypass and just query the existing memory if it exists.
    # Wait, if I am running a script, it's a NEW python process, so FAISS memory is empty!
    pass

if __name__ == "__main__":
    asyncio.run(test())
