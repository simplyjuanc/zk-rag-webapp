import json
import uuid
from typing import List
from datetime import datetime

from libs.models.pipeline import ProcessedDocument, EmbeddedChunk
from libs.models.Documents import DocumentDB, DocumentChunkDB


def map_processed_document_to_db(processed_doc: ProcessedDocument) -> DocumentDB:
    file_metadata = processed_doc.metadata.file_metadata
    frontmatter = processed_doc.metadata.frontmatter_metadata

    # Generate unique ID
    doc_id = uuid.uuid4().hex

    # Convert list fields to JSON strings for database storage
    tags_str = None
    if frontmatter and frontmatter.tags:
        tags_str = json.dumps(frontmatter.tags)

    author_str = None
    if frontmatter and frontmatter.author:
        author_str = (
            json.dumps(frontmatter.author)
            if isinstance(frontmatter.author, list)
            else str(frontmatter.author)
        )

    category_str = None
    if frontmatter and frontmatter.category:
        category_str = (
            json.dumps(frontmatter.category)
            if isinstance(frontmatter.category, list)
            else str(frontmatter.category)
        )

    document_type_str = None
    if frontmatter and frontmatter.type:
        document_type_str = (
            json.dumps(frontmatter.type)
            if isinstance(frontmatter.type, list)
            else str(frontmatter.type)
        )

    return DocumentDB(
        id=doc_id,
        file_path=file_metadata.file_path if file_metadata else "",
        file_name=file_metadata.file_name if file_metadata else "unknown",
        file_extension=file_metadata.file_extension if file_metadata else "",
        file_size=file_metadata.file_size if file_metadata else 0,
        content_hash=processed_doc.content_hash,
        raw_content=processed_doc.raw_content,
        processed_content=processed_doc.processed_content,
        title=frontmatter.title if frontmatter else None,
        author=author_str,
        document_type=document_type_str,
        category=category_str,
        tags=tags_str,
        source=frontmatter.source if frontmatter else None,
        created_on=frontmatter.created_on if frontmatter else None,
        last_updated=frontmatter.last_updated if frontmatter else None,
        content_created_at=file_metadata.content_created_at.isoformat()
        if file_metadata
        else None,
        content_modified_at=file_metadata.content_modified_at.isoformat()
        if file_metadata
        else None,
        processed_at=processed_doc.processed_at.isoformat(),
        chunks=None,  # Will be set separately
    )


def map_embedded_chunk_to_db(chunk: EmbeddedChunk, document_id: str) -> DocumentChunkDB:
    """Map an EmbeddedChunk to DocumentChunkDB for database storage."""
    # Generate unique ID
    chunk_id = uuid.uuid4().hex

    # Convert embedding list to JSON string for database storage
    embedding_str = json.dumps(chunk.embedding) if chunk.embedding else None

    return DocumentChunkDB(
        id=chunk_id,
        document_id=document_id,
        content=chunk.content,
        content_hash=chunk.content_hash,
        chunk_index=chunk.chunk_index,
        chunk_type="line",
        start_char=None,
        end_char=None,
        parent_section=None,
        token_count=None,
        estimated_tokens=chunk.word_count_estimate,
        embedding=embedding_str,
        embedding_model=chunk.embedding_model,
        embedding_created_at=chunk.embedding_created_at.isoformat()
        if chunk.embedding_created_at
        else None,
        semantic_similarity=None,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
    )


def map_pipeline_chunks_to_db(
    chunks: List[EmbeddedChunk], document_id: str
) -> List[DocumentChunkDB]:
    """Map a list of EmbeddedChunks to DocumentChunkDB for database storage."""
    return [map_embedded_chunk_to_db(chunk, document_id) for chunk in chunks]
