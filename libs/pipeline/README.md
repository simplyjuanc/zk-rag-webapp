# Data Pipeline

This module implements the data processing pipeline for the Personal Knowledge AI system. It monitors markdown files for changes, processes them, and generates embeddings using Ollama.

## Components

### FileWatcher

Monitors a directory for markdown file changes using the `watchdog` library.

**Features:**

- Watches for file creation, modification, and deletion
- Recursive directory monitoring
- Supports `.md` and `.markdown` files
- Provides callback mechanism for file events

### DocumentProcessor

Processes markdown documents and extracts metadata.

**Features:**

- Parses frontmatter metadata
- Extracts file system metadata
- Cleans and normalizes content
- Chunks content for embedding
- Calculates content hashes

### DocumentEmbedder

Generates embeddings using Ollama's local embedding models.

**Features:**

- Uses Ollama API for local embedding generation
- Supports batch processing
- Calculates cosine similarity between embeddings
- Configurable embedding model

### DataPipeline

Main orchestrator that coordinates all components.

**Features:**

- Asynchronous processing queue
- File change event handling
- Configurable chunk size and overlap
- Callback mechanism for results
- Graceful shutdown

## Usage

### Basic Usage

```python
import asyncio
from libs.pipeline import DataPipeline

async def callback(result):
    """Handle pipeline results."""
    print(f"Processed: {result}")

# Create pipeline
pipeline = DataPipeline(
    watch_directory="path/to/markdown/files",
    ollama_url="http://localhost:11434",
    embedding_model="nomic-embed-text"
)

# Start pipeline
await pipeline.start(callback=callback)

# Keep running
try:
    while True:
        await asyncio.sleep(1)
except KeyboardInterrupt:
    await pipeline.stop()
```

### Configuration

The pipeline accepts the following configuration:

- `watch_directory`: Directory to monitor for markdown files
- `ollama_url`: URL of the Ollama server (default: "http://localhost:11434")
- `embedding_model`: Ollama embedding model to use (default: "nomic-embed-text")
- `chunk_size`: Maximum size of content chunks (default: 1000 characters)
- `chunk_overlap`: Overlap between chunks (default: 200 characters)

### Running the Example

1. Make sure Ollama is running with the embedding model:

   ```bash
   ollama pull nomic-embed-text
   ollama serve
   ```

2. Run the example script:

   ```bash
   python scripts/run_pipeline.py
   ```

3. Add or modify markdown files in the `assets` directory to see the pipeline in action.

## Dependencies

The pipeline requires the following dependencies:

- `watchdog`: File system monitoring
- `python-frontmatter`: Frontmatter parsing
- `httpx`: HTTP client for Ollama API
- `numpy`: Numerical operations for similarity calculations

## Output Format

The pipeline callback receives results in the following format:

For file processing:

```python
{
    'document': {
        'file_path': 'path/to/file.md',
        'file_name': 'file.md',
        'raw_content': '...',
        'processed_content': '...',
        'content_hash': '...',
        # ... other metadata
    },
    'chunks': [
        {
            'content': 'chunk content',
            'embedding': [0.1, 0.2, ...],
            'chunk_index': 0,
            # ... other chunk metadata
        }
    ],
    'event_type': 'created|modified|existing',
    'processed_at': datetime
}
```

For file deletion:

```python
{
    'file_path': 'path/to/file.md',
    'event_type': 'deleted',
    'processed_at': datetime
}
```

## Error Handling

The pipeline includes comprehensive error handling:

- File processing errors are logged but don't stop the pipeline
- Network errors with Ollama are handled gracefully
- Invalid markdown files are processed with fallback behavior
- Queue processing continues even if individual items fail

## Performance Considerations

- The pipeline uses asynchronous processing for better performance
- Embeddings are generated in batches to optimize Ollama API usage
- File watching is non-blocking and efficient
- Content hashing prevents reprocessing unchanged files
