# Pipeline Models

This directory contains the Pydantic models for the data pipeline, organized into logical modules for better maintainability.

## Structure

### `config.py`

Contains configuration models for the pipeline:

- `PipelineConfig`: Main configuration for the data pipeline including watch directory, Ollama settings, and chunk parameters

### `file_events.py`

Contains file system event models:

- `FileEvent`: Represents file system events (created, modified, deleted)

### `documents.py`

Contains document-related models:

- `DocumentMetadata`: Metadata extracted from documents including file info and frontmatter
- `DocumentChunk`: A chunk of document content with positioning and token information
- `EmbeddedChunk`: A document chunk with its embedding vector
- `ProcessedDocument`: A fully processed document with metadata and content

### `results.py`

Contains pipeline result models:

- `PipelineResult`: Result from processing a file through the pipeline with factory methods

### `status.py`

Contains pipeline status and callback models:

- `PipelineStatus`: Current status of the pipeline
- `PipelineCallback`: Type alias for async callback functions

### `pipeline.py`

Main interface module that imports and re-exports all models for convenience.

### `__init__.py`

Package initialization that provides a clean import interface.

## Usage

### Import from the main package

```python
from libs.models.pipeline import (
    PipelineConfig,
    FileEvent,
    DocumentMetadata,
    DocumentChunk,
    EmbeddedChunk,
    ProcessedDocument,
    PipelineResult,
    PipelineStatus,
    PipelineCallback
)
```

### Import specific modules

```python
from libs.models.pipeline.config import PipelineConfig
from libs.models.pipeline.documents import DocumentMetadata, EmbeddedChunk
from libs.models.pipeline.results import PipelineResult
```

## Benefits of This Structure

1. **Separation of Concerns**: Each module focuses on a specific aspect of the pipeline
2. **Maintainability**: Easier to find and modify specific model types
3. **Reusability**: Individual modules can be imported independently
4. **Testability**: Each module can be tested in isolation
5. **Documentation**: Clear organization makes the codebase more understandable

## Migration Notes

The existing import structure remains compatible:

- `from libs.models.pipeline import *` still works
- All existing code using these models will continue to work without changes
- The main `pipeline.py` file now serves as a re-export interface
