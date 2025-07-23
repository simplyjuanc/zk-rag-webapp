
from pydantic import BaseModel
from typing import List, Optional

class DocumentChunkDB(BaseModel):
    id: str
    document_id: str
    content: str
    content_hash: str
    chunk_index: int
    chunk_type: Optional[str] = None
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    parent_section: Optional[str] = None
    token_count: Optional[int] = None
    estimated_tokens: Optional[int] = None
    embedding: Optional[str] = None
    embedding_model: Optional[str] = None
    embedding_created_at: Optional[str] = None
    semantic_similarity: Optional[float] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class DocumentDB(BaseModel):
    id: str
    file_path: str
    file_name: str
    file_extension: str
    file_size: int
    content_hash: str
    raw_content: Optional[str] = None
    processed_content: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    document_type: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[str] = None
    source: Optional[str] = None
    created_on: Optional[str] = None
    last_updated: Optional[str] = None
    content_created_at: Optional[str] = None
    content_modified_at: Optional[str] = None
    processed_at: Optional[str] = None
    chunks: Optional[List[DocumentChunkDB]] = None 
