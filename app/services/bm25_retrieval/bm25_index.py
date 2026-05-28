"""
BM25 index wrapper class maintaining tokenized corpus and original chunk references.
Uses rank_bm25 for Okapi BM25 scoring.
"""

import logging
from typing import List, Dict, Any, Optional
import numpy as np
from rank_bm25 import BM25Okapi
from app.services.ingestion.schemas import DocumentChunk
from app.services.bm25_retrieval.schemas import RetrievedChunk
from app.services.bm25_retrieval.tokenizer import SimpleTokenizer

logger = logging.getLogger(__name__)


class BM25Index:
    """Wrapper class managing Okapi BM25 index and chunk metadata mapping."""

    def __init__(self) -> None:
        """Initializes empty corpus storage and mapping structures."""
        self.tokenized_corpus: List[List[str]] = []
        self.original_chunks: List[DocumentChunk] = []
        self.chunk_id_mapping: Dict[int, str] = {}
        self.bm25: Optional[BM25Okapi] = None
        logger.info("Initialized empty BM25Index")

    def add_documents(self, chunks: List[DocumentChunk], tokenizer: SimpleTokenizer) -> int:
        """
        Tokenizes chunks, appends to internal corpus, and initializes/updates BM25Okapi index.

        Args:
            chunks: List of DocumentChunk schemas.
            tokenizer: Instance of SimpleTokenizer.

        Returns:
            Total number of chunks currently indexed.
        """
        if not chunks:
            logger.warning("add_documents called with empty chunk list.")
            return len(self.original_chunks)

        start_idx = len(self.original_chunks)
        logger.info(f"Adding {len(chunks)} chunks to BM25 index (starting at index {start_idx}).")

        for i, chunk in enumerate(chunks):
            current_idx = start_idx + i
            tokens = tokenizer.tokenize(chunk.text)
            
            # Append to storage
            self.tokenized_corpus.append(tokens)
            self.original_chunks.append(chunk)
            self.chunk_id_mapping[current_idx] = chunk.id

        # Rebuild BM25Okapi index with updated corpus
        self.bm25 = BM25Okapi(self.tokenized_corpus)
        logger.info(f"BM25Okapi index rebuilt. Total documents in corpus: {len(self.tokenized_corpus)}")
        return len(self.original_chunks)

    def search(self, query_tokens: List[str], k: int = 5) -> List[RetrievedChunk]:
        """
        Computes Okapi BM25 scores for query tokens and returns top-k matching chunks.

        Args:
            query_tokens: List of tokenized query strings.
            k: Number of top results to retrieve.

        Returns:
            List of RetrievedChunk schemas containing text, score, and metadata.
        """
        if self.bm25 is None or not self.original_chunks:
            logger.warning("Search attempted on empty BM25 index.")
            return []

        if not query_tokens:
            logger.warning("Search attempted with empty query tokens.")
            return []

        # Get BM25 scores for all documents in corpus
        scores = self.bm25.get_scores(query_tokens)

        # Get top-k indices sorted descending by score
        # np.argsort sorts ascending, so [::-1] reverses it
        top_indices = np.argsort(scores)[::-1][:k]

        results: List[RetrievedChunk] = []
        for idx in top_indices:
            score = float(scores[idx])
            # Filter out zero score matches
            if score <= 0.0:
                continue

            chunk = self.original_chunks[idx]
            results.append(RetrievedChunk(
                id=chunk.id,
                text=chunk.text,
                score=score,
                metadata=chunk.metadata
            ))

        return results
