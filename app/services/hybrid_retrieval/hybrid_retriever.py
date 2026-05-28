"""
Hybrid retriever service coordinating DenseRetriever and BM25Retriever.
Executes both searches, normalizes scores, merges duplicates, and computes weighted final rankings.
"""

import logging
from typing import List, Optional
from app.services.ingestion.schemas import DocumentChunk
from app.services.dense_retrieval.dense_retriever import DenseRetriever
from app.services.bm25_retrieval.bm25_retriever import BM25Retriever
from app.services.hybrid_retrieval.score_fusion import ScoreFusionEngine
from app.services.hybrid_retrieval.schemas import HybridRetrievedChunk

logger = logging.getLogger(__name__)


class HybridRetriever:
    """Service coordinating Dense and BM25 retrievers to execute normalized hybrid search."""

    def __init__(
        self,
        dense_retriever: DenseRetriever,
        bm25_retriever: BM25Retriever,
        dense_weight: float = 0.5,
        bm25_weight: float = 0.5
    ) -> None:
        """
        Initializes HybridRetriever with underlying retriever instances and default weights.

        Args:
            dense_retriever: Instance of DenseRetriever.
            bm25_retriever: Instance of BM25Retriever.
            dense_weight: Default weight for dense retrieval.
            bm25_weight: Default weight for BM25 retrieval.
        """
        self.dense_retriever = dense_retriever
        self.bm25_retriever = bm25_retriever
        self.default_dense_weight = dense_weight
        self.default_bm25_weight = bm25_weight
        logger.info(f"Initialized HybridRetriever (default weights: dense={dense_weight}, bm25={bm25_weight})")

    def add_documents(self, chunks: List[DocumentChunk]) -> int:
        """
        Passes chunks to both DenseRetriever and BM25Retriever to ensure identical indexing.

        Args:
            chunks: List of DocumentChunk schemas from Phase 2 ingestion.

        Returns:
            Total number of chunks successfully indexed.
        """
        if not chunks:
            logger.warning("add_documents called with empty chunk list.")
            return 0

        logger.info(f"Executing hybrid indexing for {len(chunks)} chunks across both retrievers.")
        
        # Index in DenseRetriever
        dense_indexed = self.dense_retriever.add_documents(chunks)
        
        # Index in BM25Retriever
        bm25_indexed = self.bm25_retriever.add_documents(chunks)
        
        if dense_indexed != bm25_indexed:
            logger.warning(f"Indexing mismatch: Dense indexed {dense_indexed}, BM25 indexed {bm25_indexed}.")

        return dense_indexed

    def search(
        self,
        query: str,
        k: int = 5,
        dense_weight: Optional[float] = None,
        bm25_weight: Optional[float] = None
    ) -> List[HybridRetrievedChunk]:
        """
        Executes dense and BM25 searches, normalizes scores, merges duplicates,
        computes weighted final hybrid scores, and returns top-k chunks.

        Args:
            query: User search query.
            k: Number of top chunks to retrieve.
            dense_weight: Optional override for dense retrieval weight.
            bm25_weight: Optional override for BM25 retrieval weight.

        Returns:
            List of HybridRetrievedChunk schemas sorted descending by hybrid score.
        """
        if not query.strip():
            raise ValueError("Search query cannot be empty.")

        # Use overrides if provided, otherwise defaults
        d_weight = dense_weight if dense_weight is not None else self.default_dense_weight
        b_weight = bm25_weight if bm25_weight is not None else self.default_bm25_weight

        # Validate weights equal 1.0
        if abs((d_weight + b_weight) - 1.0) > 1e-5:
            raise ValueError(f"dense_weight ({d_weight}) + bm25_weight ({b_weight}) must equal 1.0.")

        logger.info(f'Executing hybrid retrieval query: "{query}" (k={k}, weights: dense={d_weight}, bm25={b_weight})')

        # 1. Execute Dense Retrieval
        dense_results = self.dense_retriever.search(query, k=k)
        logger.info(f"Dense results count: {len(dense_results)}")

        # 2. Execute BM25 Retrieval
        bm25_results = self.bm25_retriever.search(query, k=k)
        logger.info(f"BM25 results count: {len(bm25_results)}")

        if not dense_results and not bm25_results:
            logger.warning("Both retrievers returned 0 results.")
            return []

        # 3. Normalize scores, merge duplicates, and calculate final weighted ranking
        fused_results = ScoreFusionEngine.fuse_results(
            dense_results=dense_results,
            bm25_results=bm25_results,
            dense_weight=d_weight,
            bm25_weight=b_weight,
            top_k=k
        )

        return fused_results
