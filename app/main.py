"""
Main entry point for the FastAPI RAG application.
Initializes logging, configuration, routers, and middleware.
"""

import logging
from fastapi import FastAPI
from app.core.config import settings
from app.core.logging import setup_logging
from app.api.routes import router as api_router
from app.api.ingestion_routes import router as ingestion_router
from app.api.retrieval_routes import router as retrieval_router
from app.api.routing_routes import router as routing_router
from app.api.generation_routes import router as generation_router
from app.api.orchestration_routes import router as orchestration_router
from app.api.auth_routes import router as auth_router

# Initialize structured logging
setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI application instance
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Research-Grade RAG API",
    description="A modular, production-quality Retrieval-Augmented Generation system.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins, adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include API routers
app.include_router(api_router, prefix="/api/v1")
app.include_router(ingestion_router, prefix="/api/v1")
app.include_router(retrieval_router, prefix="/api/v1")
app.include_router(routing_router, prefix="/api/v1")
app.include_router(generation_router, prefix="/api/v1")
app.include_router(orchestration_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])


@app.on_event("startup")
async def startup_event() -> None:
    """Startup event handler for initializing app-level connections."""
    logger.info(f"Starting RAG API in '{settings.app_env}' environment.")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Shutdown event handler for cleaning up resources."""
    logger.info("Shutting down RAG API.")
