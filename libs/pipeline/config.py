"""Configuration for the data pipeline."""

from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class PipelineConfig(BaseModel):
    """Configuration for the data pipeline."""

    # File watching
    watch_directory: str = Field(
        default="assets", description="Directory to watch for markdown files"
    )

    # Ollama settings
    ollama_url: str = Field(
        default="http://localhost:11434", description="URL of the Ollama server"
    )
    embedding_model: str = Field(
        default="nomic-embed-text", description="Ollama embedding model to use"
    )

    # Processing settings
    chunk_size: int = Field(
        default=1000,
        ge=100,
        le=5000,
        description="Maximum size of content chunks in characters",
    )
    chunk_overlap: int = Field(
        default=200, ge=0, le=1000, description="Overlap between chunks in characters"
    )

    # Performance settings
    max_concurrent_embeddings: int = Field(
        default=5, ge=1, le=20, description="Maximum concurrent embedding requests"
    )
    embedding_batch_size: int = Field(
        default=10, ge=1, le=50, description="Batch size for embedding requests"
    )

    supported_extensions: list[str] = Field(
        default=[".md", ".markdown"], description="Supported markdown file extensions"
    )

    log_level: str = Field(default="INFO", description="Logging level")

    class Config:
        env_prefix = "PIPELINE_"
        case_sensitive = False


# Default configuration
default_config = PipelineConfig()


def load_config(config_path: Optional[Path] = None) -> PipelineConfig:
    """Load configuration from file or environment."""
    if config_path and config_path.exists():
        # Load from file (future enhancement)
        return PipelineConfig()
    else:
        return PipelineConfig()
