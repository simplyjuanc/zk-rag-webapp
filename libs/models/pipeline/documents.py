"""Document and content models for the data pipeline."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from .metadata import DocumentMetadata, FileMetadata, FrontmatterMetadata


class ProcessedContent(BaseModel):
    """Processed markdown content."""
    raw_content: str
    processed_content: str
    content_hash: str
    processed_at: datetime


class ChunkData(BaseModel):
    """Data for a single content chunk."""
    content: str
    content_hash: str
    chunk_index: int
    start_line: int
    end_line: int
    word_count_estimate: int


class ParsedContent(BaseModel):
    """Parsed markdown content with metadata."""
    metadata: FrontmatterMetadata
    content: str


class DocumentChunk(BaseModel):
    """A chunk of document content."""
    content: str
    content_hash: str
    chunk_index: int
    start_line: int
    end_line: int
    word_count_estimate: int


class EmbeddedChunk(DocumentChunk):
    """A document chunk with its embedding."""
    embedding: List[float]
    embedding_model: str
    embedding_created_at: Optional[datetime] = None


class ProcessedDocument(BaseModel):
    """A fully processed document."""
    metadata: DocumentMetadata
    raw_content: str
    processed_content: str
    content_hash: str
    processed_at: datetime 