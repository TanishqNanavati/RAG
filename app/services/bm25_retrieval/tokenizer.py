"""
Reusable tokenizer utility for BM25 keyword retrieval.
Performs text normalization, punctuation removal, and simple tokenization.
"""

import re
import logging
from typing import List, Set, Optional

logger = logging.getLogger(__name__)


class SimpleTokenizer:
    """Lightweight text tokenizer removing punctuation and extracting normalized terms."""

    def __init__(self, stop_words: Optional[Set[str]] = None) -> None:
        """
        Initializes tokenizer with optional lightweight stopword filtering.

        Args:
            stop_words: Set of common stopwords to exclude from tokens.
        """
        # Default lightweight stopword set
        self.stop_words: Set[str] = stop_words or {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with", "by", "of", "is", "are", "was", "were"
        }
        logger.info("Initialized SimpleTokenizer")

    def tokenize(self, text: str) -> List[str]:
        """
        Processes input text into a list of clean, lowercase tokens.

        Args:
            text: Raw input text string.

        Returns:
            List of normalized string tokens.
        """
        if not text:
            return []

        # Convert to lowercase
        text = text.lower()

        # Remove punctuation using regex
        text = re.sub(r'[^\w\s]', '', text)

        # Split on whitespace
        raw_tokens = text.split()

        # Filter out empty tokens and basic stopwords
        clean_tokens = [t for t in raw_tokens if t and t not in self.stop_words]

        return clean_tokens
