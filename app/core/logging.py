"""
Logging configuration for the RAG system.
Ensures standardized, structured logging across all modules.
"""

import logging
import sys
from app.core.config import settings


def setup_logging() -> None:
    """Configures root logger and handler formats based on application settings."""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Define log format
    log_format = (
        "%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s"
    )
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True  # Override any existing logging config
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized at level: {settings.log_level}")
