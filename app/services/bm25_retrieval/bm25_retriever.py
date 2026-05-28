"""
BM25 retriever service coordinating tokenization, Okapi indexing, and keyword search.
"""

import logging
from typing import List
from app.services.ingestion.schemas import DocumentChunk
from app.services.bm25_retrieval.tokenizer import SimpleTokenizer
from app.services.bm25_retrieval.bm25_index import BM25Index
from app.services.bm25_retrieval.schemas import RetrievedChunk

logger = logging.getLogger(__name__)


class BM25Retriever:
    """Service coordinating BM25 tokenization, Okapi indexing, and keyword retrieval."""

    def __init__(self) -> None:
        """Initializes retriever with tokenizer and creates BM25 index wrapper."""
        self.tokenizer = SimpleTokenizer()
        self.bm25_index = BM25Index()
        logger.info("Initialized BM25Retriever")

    def add_documents(self, chunks: List[DocumentChunk]) -> int:
        """
        Validates chunks and passes them to BM25Index for tokenization and Okapi indexing.

        Args:
            chunks: List of DocumentChunk schemas from Phase 2 ingestion.

        Returns:
            Total number of chunks indexed.
        """
        if not chunks:
            logger.warning("add_documents called with empty chunk list.")
            return 0

        logger.info(f"Indexing {len(chunks)} chunks into BM25 index.")
        total_indexed = self.bm25_index.add_documents(chunks, self.tokenizer)
        return total_indexed

    def search(self, query: str, k: int = 5) -> List[RetrievedChunk]:
        """
        Tokenizes query string, searches BM25 index, and returns top-k matching chunks.

        Args:
            query: User keyword search query.
            k: Number of top chunks to retrieve.

        Returns:
            List of RetrievedChunk schemas matching DenseRetriever format exactly.
        """
        if not query.strip():
            raise ValueError("Search query cannot be empty.")

        logger.info(f'Executing BM25 query: "{query}" (k={k})')
        query_tokens = self.tokenizer.tokenize(query)
        
        results = self.bm25_index.search(query_tokens, k=k)
        
        logger.info(f"Retrieved {len(results)} matching chunks.")
        return results
