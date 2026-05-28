"""
FastAPI routes for document ingestion and chunking API.
"""

import os
import shutil
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Header
from app.services.ingestion.schemas import IngestResponse
from app.services.ingestion.ingestion_service import DocumentIngestionService
from app.core.security import get_current_user
from app.models.user import User, GuestUsage
from app.core.db import get_db
from sqlalchemy.orm import Session
from app.core.shared_state import hybrid_retriever

logger = logging.getLogger(__name__)
router = APIRouter()
ingestion_service = DocumentIngestionService()


@router.post("/ingest", response_model=IngestResponse, summary="Ingest and Chunk Document")
async def ingest_document(
    file: UploadFile = File(...),
    x_session_id: str = Header(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> IngestResponse:
    """
    Uploads a document (PDF, TXT, MD), extracts its text, splits it into chunks with overlap,
    and attaches rich metadata (source, page number, section titles).
    """
    if not current_user:
        if not x_session_id:
            raise HTTPException(status_code=400, detail="X-Session-ID header required for guests.")
        guest = db.query(GuestUsage).filter(GuestUsage.session_id == x_session_id).first()
        if not guest:
            guest = GuestUsage(session_id=x_session_id)
            db.add(guest)
            db.commit()
            db.refresh(guest)
        if guest.upload_count >= 1:
            raise HTTPException(status_code=403, detail="Guest upload limit reached. Please log in.")
        guest.upload_count += 1
        db.commit()

    logger.info(f"Received ingestion upload request for file: {file.filename}")
    
    # Validate extension
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in [".pdf", ".txt", ".md", ".markdown"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Supported formats: PDF, TXT, MD."
        )

    # Create temporary staging directory inside workspace
    temp_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../temp_uploads"))
    os.makedirs(temp_dir, exist_ok=True)
    temp_file_path = os.path.join(temp_dir, file.filename or "uploaded_doc")

    try:
        # Save uploaded file to disk
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Process file through ingestion service
        chunks = ingestion_service.ingest_file(temp_file_path)
        
        # Index chunks into FAISS and BM25 simultaneously
        if chunks:
            hybrid_retriever.add_documents(chunks)

        sample = chunks[0] if chunks else None
        return IngestResponse(
            status="success",
            num_chunks=len(chunks),
            sample_chunk=sample
        )

    except Exception as e:
        logger.error(f"Ingestion failed for {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion error: {str(e)}")

    finally:
        # Clean up temporary staging file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
