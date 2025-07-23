from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid

from libs.storage.tables.base import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(
        primary_key=True, index=True, default=lambda: uuid.uuid4().hex
    )
    file_path: Mapped[str] = mapped_column(nullable=False, unique=True)
    file_name: Mapped[str] = mapped_column(nullable=False)
    raw_content: Mapped[str] = mapped_column(nullable=True)
    file_extension: Mapped[str] = mapped_column(nullable=False)
    file_size: Mapped[int] = mapped_column(nullable=False)
    content_hash: Mapped[str] = mapped_column(nullable=False, unique=True)
    processed_content: Mapped[str] = mapped_column(nullable=True)
    title: Mapped[str] = mapped_column(nullable=True)
    author: Mapped[str] = mapped_column(nullable=True)
    document_type: Mapped[str] = mapped_column(nullable=True)
    category: Mapped[str] = mapped_column(nullable=True)
    tags: Mapped[str] = mapped_column(nullable=True)
    source: Mapped[str] = mapped_column(nullable=True)
    created_on: Mapped[str] = mapped_column(nullable=True)
    last_updated: Mapped[str] = mapped_column(nullable=True)
    content_created_at: Mapped[str] = mapped_column(nullable=True)
    content_modified_at: Mapped[str] = mapped_column(nullable=True)
    processed_at: Mapped[str] = mapped_column(nullable=True)
    
    chunks = relationship('DocumentChunk', back_populates='document')


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(primary_key=True, index=True, default=lambda: uuid.uuid4().hex)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), nullable=False, index=True)
    content: Mapped[str] = mapped_column(nullable=False)
    content_hash: Mapped[str] = mapped_column(nullable=False)
    chunk_index: Mapped[int] = mapped_column(nullable=False)
    chunk_type: Mapped[str] = mapped_column(nullable=True, default="paragraph")
    start_char: Mapped[int] = mapped_column(nullable=True)
    end_char: Mapped[int] = mapped_column(nullable=True)
    parent_section: Mapped[str] = mapped_column(nullable=True)
    token_count: Mapped[int] = mapped_column(nullable=True)
    estimated_tokens: Mapped[int] = mapped_column(nullable=True)
    embedding: Mapped[str] = mapped_column(nullable=True)  # Store as JSON/text for now
    embedding_model: Mapped[str] = mapped_column(nullable=True, default="text-embedding-ada-002")
    embedding_created_at: Mapped[str] = mapped_column(nullable=True)
    semantic_similarity: Mapped[float] = mapped_column(nullable=True)
    created_at: Mapped[str] = mapped_column(nullable=True)
    updated_at: Mapped[str] = mapped_column(nullable=True)

    document = relationship("Document", backref="chunks")
    
