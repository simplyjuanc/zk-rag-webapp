"""Pydantic models for the data pipeline.

This module provides a unified interface to all pipeline-related models.
"""

# Import all models from their respective modules
from ..documents import (
    TextChunk,
    EmbeddedChunk,
    Document,
    ParsedContent,
    TextChunk,
)
from .metadata import FileMetadata, FrontmatterMetadata, DocumentMetadata
from .processor import PipelineResult, PipelineStatus, PipelineCallback
from .config import PipelineConfig
from .events import FileEvent, FileEventType

# Re-export all models for convenience
__all__ = [
    "PipelineConfig",
    "FileEvent",
    "FileEventType",
    "TextChunk",
    "EmbeddedChunk",
    "Document",
    "PipelineResult",
    "PipelineStatus",
    "PipelineCallback",
    "FileMetadata",
    "FrontmatterMetadata",
    "DocumentMetadata",
    "ProcessedContent",
    "ParsedContent",
    "TextChunk",
]
