"""
FastAPI router definitions for health checks and RAG endpoints.
"""

import logging
from fastapi import APIRouter
from app.core.config import settings
from app.models.schemas import HealthResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="Health Check")
async def health_check() -> HealthResponse:
    """Verifies that the API and configuration are functioning correctly."""
    logger.debug("Health check endpoint called.")
    return HealthResponse(status="ok", environment=settings.app_env)
