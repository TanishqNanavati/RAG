"""
Document ingestion service orchestrating file loading and text chunking.
"""

import os
import logging
from typing import List
from app.services.ingestion.loader import DocumentLoader
from app.services.ingestion.chunker import TextChunker
from app.services.ingestion.schemas import DocumentChunk

logger = logging.getLogger(__name__)


class DocumentIngestionService:
    """Service orchestrating the full ingestion and chunking pipeline."""

    def __init__(self, chunk_size: int = 1000, overlap: int = 200) -> None:
        """Initializes loader and chunker components."""
        self.loader = DocumentLoader()
        self.chunker = TextChunker(chunk_size=chunk_size, overlap=overlap)
        logger.info("Initialized DocumentIngestionService")

    def ingest_file(self, file_path: str) -> List[DocumentChunk]:
        """
        Legacy: Loads a single file into memory completely.
        """
        logger.info(f"Ingesting file: {file_path}")
        loaded_doc = self.loader.load_file(file_path)
        chunks = self.chunker.chunk_document(loaded_doc)
        return chunks

    def ingest_file_in_batches(self, file_path: str, batch_size: int = 100):
        """
        Streams a file and yields chunks in memory-safe batches.
        """
        logger.info(f"Streaming ingestion for file: {file_path}")
        chunk_generator = self.chunker.stream_chunks(self.loader.stream_file(file_path))
        batch = []
        for chunk in chunk_generator:
            batch.append(chunk)
            if len(batch) >= batch_size:
                yield batch
                batch = []
        if batch:
            yield batch

    def ingest_directory(self, directory_path: str) -> List[DocumentChunk]:
        """
        Scans a directory for supported files and ingests them all.

        Args:
            directory_path: Absolute path to the folder containing documents.

        Returns:
            Combined list of DocumentChunk objects from all files.
        """
        if not os.path.isdir(directory_path):
            raise NotADirectoryError(f"Directory not found: {directory_path}")

        logger.info(f"Ingesting directory: {directory_path}")
        all_chunks: List[DocumentChunk] = []

        for root, _, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    # Attempt to detect file type; skip unsupported files silently or log debug
                    self.loader.detect_file_type(file_path)
                    chunks = self.ingest_file(file_path)
                    all_chunks.extend(chunks)
                except ValueError:
                    logger.debug(f"Skipping unsupported file in directory scan: {file}")
                except Exception as e:
                    logger.error(f"Failed to ingest file {file_path} during directory scan: {e}")

        logger.info(f"Total chunks generated from directory {directory_path}: {len(all_chunks)}")
        return all_chunks
