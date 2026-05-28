"""
Embedding service for generating dense vector representations using sentence-transformers.
"""

import logging
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for loading SentenceTransformer model and generating normalized embeddings."""

    def __init__(self) -> None:
        """Initializes the sentence-transformers model once upon startup."""
        self.model_name = settings.embedding_model
        logger.info(f"Loading SentenceTransformer model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        self.dimension = self.model.get_embedding_dimension()
        logger.info(f"Embedding model loaded successfully. Vector dimension: {self.dimension}")

    def embed_text(self, text: str) -> np.ndarray:
        """
        Generates a normalized embedding vector for a single text string.

        Args:
            text: Input text string.

        Returns:
            1D numpy array representing the normalized embedding vector.
        """
        logger.debug(f"Generating embedding for single text (len: {len(text)})")
        # encode with normalize_embeddings=True for cosine similarity via inner product
        vector = self.model.encode(text, normalize_embeddings=True)
        return np.array(vector, dtype=np.float32)

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Generates normalized embedding vectors for a list of text strings in batch.

        Args:
            texts: List of input text strings.

        Returns:
            2D numpy array of shape (len(texts), dimension).
        """
        logger.debug(f"Generating batch embeddings for {len(texts)} texts.")
        if not texts:
            return np.empty((0, self.dimension), dtype=np.float32)

        vectors = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return np.array(vectors, dtype=np.float32)
