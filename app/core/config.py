"""
Environment configuration loader for the RAG system.
Uses Pydantic BaseSettings for validation and type safety.
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""
    
    # App config
    app_env: str = "dev"
    log_level: str = "INFO"

    # LLM config (OpenAI-compatible API)
    openai_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    openai_timeout_s: int = 60
    openai_max_retries: int = 2

    # Vector DB (Qdrant) config
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "rag_chunks"
    qdrant_api_key: Optional[str] = None

    # Embeddings & Reranking config
    embedding_model: str = "all-MiniLM-L6-v2"
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # Retrieval knobs
    top_k_dense: int = 20
    top_k_bm25: int = 20
    rerank_top_n: int = 30
    fusion_w_dense: float = 0.6
    fusion_w_bm25: float = 0.4
    min_rerank_score: float = -4.0
    min_avg_rerank_score: float = -6.0

    # Self-eval / retry loop config
    max_rag_rounds: int = 2
    faithfulness_threshold: float = 0.70
    citation_threshold: float = 0.70

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


# Global settings instance
settings = Settings()
