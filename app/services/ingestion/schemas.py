"""
Pydantic schemas for document ingestion and chunking pipeline.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ChunkMetadata(BaseModel):
    """Metadata attached to each document chunk."""
    source: str = Field(..., description="Original filename or source path.")
    page: Optional[int] = Field(default=None, description="Page number if source is a PDF.")
    chunk_index: int = Field(..., description="Sequential index of the chunk within the document.")
    document_type: str = Field(..., description="File format: pdf, txt, or md.")
    section_title: Optional[str] = Field(default=None, description="Detected markdown heading or PDF section title.")


class DocumentChunk(BaseModel):
    """Represents a single text chunk ready for vector storage later."""
    id: str = Field(..., description="Unique identifier for the chunk.")
    text: str = Field(..., description="The chunk text content.")
    metadata: ChunkMetadata = Field(..., description="Associated metadata.")


class LoadedPage(BaseModel):
    """Represents text extracted from a single page or section of a document."""
    text: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None


class LoadedDocument(BaseModel):
    """Represents a fully loaded document parsed into pages/sections."""
    source: str
    document_type: str
    pages: List[LoadedPage] = Field(default_factory=list)


class StreamedPage(BaseModel):
    """Represents a single yielded page in a streaming ingestion pipeline."""
    source: str
    document_type: str
    page: LoadedPage


class IngestResponse(BaseModel):
    """Response schema for the ingestion API endpoint."""
    status: str = Field(..., example="success")
    num_chunks: int = Field(..., example=15)
    sample_chunk: Optional[DocumentChunk] = Field(default=None, description="A sample chunk generated from the document.")
