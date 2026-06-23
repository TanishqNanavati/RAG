"""
Text chunking service supporting configurable size, overlap, and sentence boundary preservation.
"""

import logging
import re
import hashlib
from typing import List, Iterator
from app.services.ingestion.schemas import LoadedDocument, DocumentChunk, ChunkMetadata, StreamedPage

logger = logging.getLogger(__name__)


class TextChunker:
    """Service for splitting loaded document text into manageable chunks."""

    def __init__(self, chunk_size: int = 1000, overlap: int = 200) -> None:
        """
        Initializes the chunker with target size and overlap.
        """
        if overlap >= chunk_size:
            raise ValueError("Overlap must be less than chunk_size.")
        self.chunk_size = chunk_size
        self.overlap = overlap
        logger.info(f"Initialized TextChunker (chunk_size={chunk_size}, overlap={overlap})")

    def _generate_chunk_id(self, source: str, chunk_index: int, text: str) -> str:
        """Generates a stable unique hash ID for a chunk based on its content and source."""
        hash_input = f"{source}_{chunk_index}_{text[:50]}".encode("utf-8")
        return hashlib.md5(hash_input).hexdigest()

    def _split_sentences(self, text: str) -> List[str]:
        """Splits text into sentences using regex boundary detection."""
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        return [s.strip() for s in sentences if s.strip()]

    def chunk_document(self, document: LoadedDocument) -> List[DocumentChunk]:
        """Legacy compatibility wrapper. Returns a list of chunks."""
        logger.info(f"Chunking document (legacy mode): {document.source}")
        
        def page_stream():
            for page in document.pages:
                yield StreamedPage(source=document.source, document_type=document.document_type, page=page)
                
        chunks = list(self.stream_chunks(page_stream()))
        return chunks

    def stream_chunks(self, page_stream: Iterator[StreamedPage]) -> Iterator[DocumentChunk]:
        """Streams a generator of StreamedPage objects, yielding DocumentChunks efficiently."""
        chunk_index = 0
        current_chunk_sentences: List[str] = []
        current_length = 0
        last_page_context = None

        for streamed_page in page_stream:
            if current_chunk_sentences and last_page_context:
                chunk_text = " ".join(current_chunk_sentences)
                chunk_id = self._generate_chunk_id(last_page_context.source, chunk_index, chunk_text)
                metadata = ChunkMetadata(
                    source=last_page_context.source,
                    page=last_page_context.page.page_number,
                    chunk_index=chunk_index,
                    document_type=last_page_context.document_type,
                    section_title=last_page_context.page.section_title
                )
                yield DocumentChunk(id=chunk_id, text=chunk_text, metadata=metadata)
                chunk_index += 1
                current_chunk_sentences = []
                current_length = 0

            last_page_context = streamed_page
            page = streamed_page.page
            if not page.text.strip():
                continue

            sentences = self._split_sentences(page.text)

            for sentence in sentences:
                sentence_len = len(sentence)
                
                # If a single sentence exceeds chunk_size, split it by words
                if sentence_len > self.chunk_size:
                    if current_chunk_sentences:
                        chunk_text = " ".join(current_chunk_sentences)
                        chunk_id = self._generate_chunk_id(streamed_page.source, chunk_index, chunk_text)
                        metadata = ChunkMetadata(
                            source=streamed_page.source,
                            page=page.page_number,
                            chunk_index=chunk_index,
                            document_type=streamed_page.document_type,
                            section_title=page.section_title
                        )
                        yield DocumentChunk(id=chunk_id, text=chunk_text, metadata=metadata)
                        chunk_index += 1
                        current_chunk_sentences = []
                        current_length = 0

                    words = sentence.split()
                    sub_chunk: List[str] = []
                    sub_len = 0
                    for word in words:
                        if sub_len + len(word) + 1 > self.chunk_size:
                            sub_text = " ".join(sub_chunk)
                            chunk_id = self._generate_chunk_id(streamed_page.source, chunk_index, sub_text)
                            metadata = ChunkMetadata(
                                source=streamed_page.source,
                                page=page.page_number,
                                chunk_index=chunk_index,
                                document_type=streamed_page.document_type,
                                section_title=page.section_title
                            )
                            yield DocumentChunk(id=chunk_id, text=sub_text, metadata=metadata)
                            chunk_index += 1
                            sub_chunk = [word]
                            sub_len = len(word)
                        else:
                            sub_chunk.append(word)
                            sub_len += len(word) + 1
                    
                    if sub_chunk:
                        current_chunk_sentences = [" ".join(sub_chunk)]
                        current_length = sub_len
                    continue

                if current_length + sentence_len + 1 > self.chunk_size and current_chunk_sentences:
                    chunk_text = " ".join(current_chunk_sentences)
                    chunk_id = self._generate_chunk_id(streamed_page.source, chunk_index, chunk_text)
                    metadata = ChunkMetadata(
                        source=streamed_page.source,
                        page=page.page_number,
                        chunk_index=chunk_index,
                        document_type=streamed_page.document_type,
                        section_title=page.section_title
                    )
                    yield DocumentChunk(id=chunk_id, text=chunk_text, metadata=metadata)
                    chunk_index += 1

                    overlap_length = 0
                    overlap_sentences: List[str] = []
                    for s in reversed(current_chunk_sentences):
                        if overlap_length + len(s) + 1 <= self.overlap:
                            overlap_sentences.insert(0, s)
                            overlap_length += len(s) + 1
                        else:
                            break
                    current_chunk_sentences = overlap_sentences + [sentence]
                    current_length = overlap_length + sentence_len + 1
                else:
                    current_chunk_sentences.append(sentence)
                    current_length += sentence_len + 1

        # Flush remaining sentences
        if current_chunk_sentences and last_page_context:
            chunk_text = " ".join(current_chunk_sentences)
            chunk_id = self._generate_chunk_id(last_page_context.source, chunk_index, chunk_text)
            metadata = ChunkMetadata(
                source=last_page_context.source,
                page=last_page_context.page.page_number,
                chunk_index=chunk_index,
                document_type=last_page_context.document_type,
                section_title=last_page_context.page.section_title
            )
            yield DocumentChunk(id=chunk_id, text=chunk_text, metadata=metadata)
