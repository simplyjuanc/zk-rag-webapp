"""Metadata models for the data pipeline."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class FileMetadata(BaseModel):
    """File system metadata."""

    file_path: str
    file_name: str
    file_extension: str
    file_size: int
    content_created_at: datetime
    content_modified_at: datetime


class FrontmatterMetadata(BaseModel):
    """Metadata extracted from frontmatter."""

    created_on: Optional[str] = Field(default=None)
    last_updated: Optional[str] = Field(default=None)
    author: Optional[List[str]] = Field(default=None)
    category: Optional[List[str]] = Field(default=None)
    type: Optional[List[str]] = Field(default=None)
    source: Optional[str] = Field(default=None)
    title: Optional[str] = Field(default=None)
    tags: Optional[List[str]] = Field(default=None)
    description: Optional[str] = Field(default=None)


class DocumentMetadata(BaseModel):
    """Metadata for a document."""

    file_metadata: Optional[FileMetadata] = Field(default=None)
    frontmatter_metadata: Optional[FrontmatterMetadata] = Field(default=None)
