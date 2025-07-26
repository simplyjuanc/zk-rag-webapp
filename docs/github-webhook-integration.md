# GitHub Webhook Integration

This document describes how the GitHub webhook integration works with the embedding service and pipeline.

## Overview

When a GitHub push event is received via webhook, the system automatically processes any modified markdown files through the embedding pipeline and stores them in the database.

## Flow

1. **GitHub Webhook**: Receives push events from GitHub
2. **GitHub Handler**: Extracts file paths from the push event
3. **Embedding Service**: Processes markdown files through the pipeline
4. **Pipeline**: Processes documents, creates embeddings, and stores in database

## Configuration

### Environment Variables

Add these to your `.env` file:

```env
# Repository Configuration
REPO_BASE_PATH=/path/to/your/repository

# Ollama Configuration
OLLAMA_URL=http://localhost:11434
LLM_EMBEDDINGS_MODEL=nomic-embed-text

# GitHub Webhook Secret
ZK_REPO_SECRET=your_github_webhook_secret
```

### Repository Base Path

The `REPO_BASE_PATH` should point to the root of your repository. This is used to resolve relative file paths from GitHub webhooks to absolute paths on your system.

## Usage

### Setting up GitHub Webhook

1. Go to your GitHub repository settings
2. Navigate to Webhooks
3. Add a new webhook with:
   - **Payload URL**: `https://your-domain.com/webhooks/github`
   - **Content type**: `application/json`
   - **Secret**: Use the same value as `ZK_REPO_SECRET`
   - **Events**: Select "Just the push event"

### Testing the Integration

You can test the integration by:

1. Making a commit with markdown files to your repository
2. Checking the logs to see if files are processed
3. Verifying that documents appear in your database

### Manual Processing

You can also manually process files using the embedding service:

```python
from apps.backend.services.embedding import EmbeddingService

# Initialize the service
service = EmbeddingService(document_repo)

# Process a single file
success = await service.process_single_file("path/to/file.md")

# Process multiple files
processed_files = await service.process_files([
    "path/to/file1.md",
    "path/to/file2.md"
])
```

## File Processing

### Supported Files

- Only `.md` (markdown) files are processed
- Files are automatically filtered from GitHub push events
- Both relative and absolute paths are supported

### Processing Steps

1. **File Validation**: Check if file exists and is a markdown file
2. **Document Processing**: Extract metadata and content
3. **Chunking**: Split content into chunks for embedding
4. **Embedding**: Generate embeddings using Ollama
5. **Storage**: Store document and chunks in database

## Error Handling

- Files that don't exist are logged and skipped
- Non-markdown files are logged and skipped
- Processing errors are logged but don't stop other files
- Database errors are logged and handled gracefully

## Monitoring

Check the logs for:

- `Processing file: {file_path}` - File processing started
- `Successfully processed: {file_path}` - File processing completed
- `Error processing file {file_path}: {error}` - Processing errors

## Troubleshooting

### Files Not Being Processed

1. Check that `REPO_BASE_PATH` is set correctly
2. Verify that files exist at the expected paths
3. Ensure files have `.md` extension
4. Check logs for error messages

### Pipeline Issues

1. Verify Ollama is running and accessible
2. Check that `OLLAMA_URL` is correct
3. Ensure `LLM_EMBEDDINGS_MODEL` is available in Ollama
4. Check database connectivity

### Webhook Issues

1. Verify webhook URL is accessible
2. Check webhook secret matches `ZK_REPO_SECRET`
3. Ensure webhook is configured for push events
4. Check GitHub webhook delivery logs
