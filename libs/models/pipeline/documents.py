"""Document and content models for the data pipeline."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from .metadata import DocumentMetadata, FrontmatterMetadata
from libs.models.Document import DocumentDB, DocumentChunkDB

# --- Content and Chunk Models ---

class ProcessedContent(BaseModel):
    raw_content: str
    processed_content: str
    content_hash: str
    processed_at: datetime

class DocumentChunk(BaseModel):
    id: str
    content: str
    content_hash: str
    chunk_index: int
    start_line: int
    end_line: int
    word_count_estimate: int

class EmbeddedChunk(DocumentChunk):
    embedding: List[float]
    embedding_model: str
    embedding_created_at: Optional[datetime] = None

# --- Document Models ---


class ChunkData(BaseModel):
        content: str
        content_hash: str
        chunk_index: int
        start_line: int
        end_line: int
        word_count_estimate: int


class ParsedContent(BaseModel):
    metadata: FrontmatterMetadata
    content: str

class ProcessedDocument(BaseModel):
    metadata: DocumentMetadata
    raw_content: str
    processed_content: str
    content_hash: str
    processed_at: datetime
