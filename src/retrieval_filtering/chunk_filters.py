"""
Utility class for filtering, pruning, and deduplicating chunks before LLM generation.
"""

import logging
from typing import List
from app.reranking.models import RerankedChunk

logger = logging.getLogger(__name__)


class ChunkFilters:
    """Pre-generation context window optimizations."""

    @staticmethod
    def deduplicate(chunks: List[RerankedChunk]) -> List[RerankedChunk]:
        """
        Removes exact duplicate or near-duplicate texts to preserve context window.
        """
        seen_hashes = set()
        deduped = []
        original_count = len(chunks)

        for chunk in chunks:
            # Normalize whitespace and lowercase for hash
            normalized_text = " ".join(chunk.text.strip().lower().split())
            text_hash = hash(normalized_text)

            if text_hash not in seen_hashes:
                seen_hashes.add(text_hash)
                deduped.append(chunk)

        removed_count = original_count - len(deduped)
        if removed_count > 0:
            logger.info(f"Deduplicated {removed_count} identical chunks from context window.")
            
        return deduped
