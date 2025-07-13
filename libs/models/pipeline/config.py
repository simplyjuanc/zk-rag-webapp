"""Configuration models for the data pipeline."""

from pydantic import BaseModel, Field, ConfigDict


class PipelineConfig(BaseModel):
    """Configuration for the data pipeline."""
    watch_directory: str
    ollama_url: str = "http://localhost:11434"
    embedding_model: str = "nomic-embed-text"
    chunk_size: int = Field(default=1000, ge=100, le=10000)
    chunk_overlap: int = Field(default=200, ge=0, le=2000)
    
    model_config = ConfigDict(frozen=True) 