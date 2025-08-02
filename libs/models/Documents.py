from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from libs.models.embeddings import Embedding

from .pipeline.metadata import DocumentMetadata, FrontmatterMetadata


class ParsedContent(BaseModel):
    metadata: FrontmatterMetadata
    content: str


class TextChunk(BaseModel):
    id: str
    document_id: str
    content: str
    content_hash: str
    chunk_index: int
    word_count_estimate: int


class EmbeddedChunk(TextChunk):
    embedding: Optional[Embedding]

    def __str__(self) -> str:
        return f"EmbeddedChunk(id={self.id}, document_id={self.document_id}, chunk_index={self.chunk_index})"

    @classmethod
    def from_text_chunk(
        cls, text_chunk: TextChunk, embedding: Embedding
    ) -> "EmbeddedChunk":
        return cls(
            id=text_chunk.id,
            document_id=text_chunk.document_id,
            content=text_chunk.content,
            content_hash=text_chunk.content_hash,
            chunk_index=text_chunk.chunk_index,
            word_count_estimate=text_chunk.word_count_estimate,
            embedding=embedding,
        )


class Document(BaseModel):
    id: str
    metadata: DocumentMetadata
    content: str
    content_hash: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


class AnalysedDocument(Document):
    embedded_chunks: List[EmbeddedChunk] = []

    def __str__(self) -> str:
        return f"Document(id={self.id}, name={self.metadata.frontmatter_metadata.title if self.metadata.frontmatter_metadata else 'N/A'}, created_at={self.created_at})"

    @classmethod
    def from_document_and_embeddings(
        cls, document: Document, embedded_chunks: List[EmbeddedChunk]
    ) -> "AnalysedDocument":
        return cls(
            id=document.id,
            metadata=document.metadata,
            content=document.content,
            content_hash=document.content_hash,
            created_at=document.created_at,
            updated_at=document.updated_at,
            deleted_at=document.deleted_at,
            embedded_chunks=embedded_chunks,
        )
