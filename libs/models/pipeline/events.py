"""File system event models for the data pipeline."""

from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict


class FileEventType(Enum):
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    EXISTING = "existing"
    MANUAL = "manual"


class FileEvent(BaseModel):
    """Represents a file system event."""
    file_path: Path
    event_type: FileEventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    model_config = ConfigDict(arbitrary_types_allowed=True) 