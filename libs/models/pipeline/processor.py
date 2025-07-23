"""Document processing models for the data pipeline."""

from datetime import datetime, timezone
from typing import Awaitable, Callable, List, Optional
from pydantic import BaseModel

from .documents import ProcessedDocument, EmbeddedChunk
from .events import FileEventType


class PipelineResult(BaseModel):
    """Result from processing a file through the pipeline."""
    document: Optional[ProcessedDocument] = None
    chunks: Optional[List[EmbeddedChunk]] = None
    file_path: Optional[str] = None
    event_type: FileEventType
    processed_at: datetime
    
    @classmethod
    def from_processing(
        cls,
        document: ProcessedDocument,
        chunks: List[EmbeddedChunk],
        event_type: FileEventType
    ) -> "PipelineResult":
        """Create a result from document processing."""
        return cls(
            document=document,
            chunks=chunks,
            event_type=event_type,
            processed_at=datetime.now(timezone.utc)
        )
    
    @classmethod
    def from_deletion(cls, file_path: str) -> "PipelineResult":
        """Create a result from file deletion."""
        return cls(
            file_path=file_path,
            event_type=FileEventType.DELETED,
            processed_at=datetime.now(timezone.utc)
        )


class PipelineStatus(BaseModel):
    """Current status of the pipeline."""
    is_running: bool
    watch_directory: str
    queue_size: int
    chunk_size: int
    chunk_overlap: int


PipelineCallback = Callable[[PipelineResult], Awaitable[None]]  