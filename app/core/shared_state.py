import logging
from app.services.dense_retrieval.embedding_service import EmbeddingService
from app.services.dense_retrieval.dense_retriever import DenseRetriever
from app.services.bm25_retrieval.bm25_retriever import BM25Retriever
from app.services.hybrid_retrieval.hybrid_retriever import HybridRetriever

logger = logging.getLogger(__name__)

logger.info("Initializing Shared RAG Retriever Singletons...")

try:
    embedding_service = EmbeddingService()
    dense_retriever = DenseRetriever(embedding_service)
    bm25_retriever = BM25Retriever()
    hybrid_retriever = HybridRetriever(dense_retriever, bm25_retriever)
    logger.info("Shared RAG Retriever Singletons initialized successfully.")
except Exception as e:
    logger.critical(f"Failed to initialize shared retriever singletons: {e}")
    raise e
