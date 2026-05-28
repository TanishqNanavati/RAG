"""
FastAPI routes for Phase 8 Grounded Answer Generation with Citations API.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from src.generation.models import GeneratedAnswer, AnswerGenerationRequest
from src.generation.answer_generator import AnswerGenerator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/generation", tags=["Answer Generation"])

answer_generator = AnswerGenerator()


@router.post("/generate", response_model=GeneratedAnswer, summary="Generate Grounded Answer with Citations")
async def generate_grounded_answer(request: AnswerGenerationRequest) -> GeneratedAnswer:
    """
    Accepts a query and retrieved/re-ranked chunks, assigns citation IDs ([1], [2]),
    executes LLM prompt generation, validates inline citations, and returns the grounded answer.
    """
    logger.info(f"Received answer generation request for query: '{request.query}' (Chunks: {len(request.chunks)})")
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        result = answer_generator.generate_answer(request.query, request.chunks)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Answer generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Generation error: {str(e)}")
