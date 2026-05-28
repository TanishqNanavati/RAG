"""
FastAPI routes for Phase 3 Dense, Phase 4 BM25, and Phase 5 Hybrid retrieval APIs.
"""

import os
import shutil
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.services.ingestion.ingestion_service import DocumentIngestionService
from app.services.dense_retrieval.embedding_service import EmbeddingService
from app.services.dense_retrieval.dense_retriever import DenseRetriever
from app.services.dense_retrieval.schemas import IndexResponse, SearchRequest, SearchResponse
from app.services.bm25_retrieval.bm25_retriever import BM25Retriever
from app.services.bm25_retrieval.schemas import BM25IndexResponse, BM25SearchRequest, BM25SearchResponse
from app.services.hybrid_retrieval.hybrid_retriever import HybridRetriever
from app.services.hybrid_retrieval.schemas import HybridIndexResponse, HybridSearchRequest, HybridSearchResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# Dependency injection / Singleton initialization
from app.core.shared_state import dense_retriever, bm25_retriever, hybrid_retriever
ingestion_service = DocumentIngestionService()



# ---- Phase 3: Dense Retrieval Routes ----

@router.post("/index", response_model=IndexResponse, summary="Ingest and Index Document in FAISS")
async def index_document(file: UploadFile = File(...)) -> IndexResponse:
    logger.info(f"Received dense indexing request for file: {file.filename}")
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in [".pdf", ".txt", ".md", ".markdown"]:
        raise HTTPException(status_code=400, detail=f"Unsupported file type '{ext}'.")

    temp_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../temp_uploads"))
    os.makedirs(temp_dir, exist_ok=True)
    temp_file_path = os.path.join(temp_dir, file.filename or "uploaded_doc")

    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        chunks = ingestion_service.ingest_file(temp_file_path)
        if not chunks:
            raise HTTPException(status_code=400, detail="Document produced 0 chunks.")

        total_indexed = dense_retriever.add_documents(chunks)
        return IndexResponse(status="success", chunks_indexed=total_indexed)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dense indexing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Dense indexing error: {str(e)}")

    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@router.post("/search", response_model=SearchResponse, summary="Semantic Dense Search")
async def semantic_search(request: SearchRequest) -> SearchResponse:
    logger.info(f"Received semantic search request for query: '{request.query}'")
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty.")

    try:
        results = dense_retriever.search(request.query, k=request.k)
        return SearchResponse(query=request.query, results=results)
    except Exception as e:
        logger.error(f"Dense search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Dense search error: {str(e)}")


# ---- Phase 4: BM25 Keyword Retrieval Routes ----

@router.post("/bm25/index", response_model=BM25IndexResponse, summary="Ingest and Index Document in BM25")
async def bm25_index_document(file: UploadFile = File(...)) -> BM25IndexResponse:
    logger.info(f"Received BM25 indexing request for file: {file.filename}")
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in [".pdf", ".txt", ".md", ".markdown"]:
        raise HTTPException(status_code=400, detail=f"Unsupported file type '{ext}'.")

    temp_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../temp_uploads"))
    os.makedirs(temp_dir, exist_ok=True)
    temp_file_path = os.path.join(temp_dir, file.filename or "uploaded_doc")

    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        chunks = ingestion_service.ingest_file(temp_file_path)
        if not chunks:
            raise HTTPException(status_code=400, detail="Document produced 0 chunks.")

        total_indexed = bm25_retriever.add_documents(chunks)
        return BM25IndexResponse(
            status="success",
            chunks_indexed=total_indexed,
            document_name=file.filename or "uploaded_doc"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"BM25 indexing failed: {e}")
        raise HTTPException(status_code=500, detail=f"BM25 indexing error: {str(e)}")

    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@router.post("/bm25/search", response_model=BM25SearchResponse, summary="BM25 Keyword Search")
async def bm25_search(request: BM25SearchRequest) -> BM25SearchResponse:
    logger.info(f"Received BM25 search request for query: '{request.query}'")
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty.")

    try:
        results = bm25_retriever.search(request.query, k=request.k)
        return BM25SearchResponse(query=request.query, results=results)
    except Exception as e:
        logger.error(f"BM25 search failed: {e}")
        raise HTTPException(status_code=500, detail=f"BM25 search error: {str(e)}")


# ---- Phase 5: Hybrid Retrieval Routes ----

@router.post("/hybrid/index", response_model=HybridIndexResponse, summary="Ingest and Index Document in Hybrid System")
async def hybrid_index_document(file: UploadFile = File(...)) -> HybridIndexResponse:
    """
    Uploads a document (PDF, TXT, MD), executes Phase 2 ingestion to generate chunks,
    and indexes them into BOTH Dense (FAISS) and BM25 (Okapi) stores simultaneously.
    """
    logger.info(f"Received hybrid indexing request for file: {file.filename}")
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in [".pdf", ".txt", ".md", ".markdown"]:
        raise HTTPException(status_code=400, detail=f"Unsupported file type '{ext}'.")

    temp_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../temp_uploads"))
    os.makedirs(temp_dir, exist_ok=True)
    temp_file_path = os.path.join(temp_dir, file.filename or "uploaded_doc")

    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        chunks = ingestion_service.ingest_file(temp_file_path)
        if not chunks:
            raise HTTPException(status_code=400, detail="Document produced 0 chunks.")

        total_indexed = hybrid_retriever.add_documents(chunks)
        return HybridIndexResponse(status="success", chunks_indexed=total_indexed)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Hybrid indexing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Hybrid indexing error: {str(e)}")

    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@router.post("/hybrid/search", response_model=HybridSearchResponse, summary="Hybrid Semantic + Keyword Search")
async def hybrid_search(request: HybridSearchRequest) -> HybridSearchResponse:
    """
    Executes hybrid search across Dense and BM25 stores, normalizes scores, merges duplicates,
    computes weighted final rankings, and returns top-k chunks.
    """
    logger.info(f"Received hybrid search request for query: '{request.query}' (weights: dense={request.dense_weight}, bm25={request.bm25_weight})")
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty.")

    try:
        results = hybrid_retriever.search(
            query=request.query,
            k=request.k,
            dense_weight=request.dense_weight,
            bm25_weight=request.bm25_weight
        )
        return HybridSearchResponse(query=request.query, results=results)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Hybrid search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Hybrid search error: {str(e)}")
