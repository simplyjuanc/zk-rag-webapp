#!/usr/bin/env python3
import asyncio
import logging
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.models.pipeline import FileEventType
from libs.pipeline import DataPipeline
from libs.models.pipeline import PipelineConfig, PipelineResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def pipeline_callback(result: PipelineResult) -> None:
    """Callback function for pipeline results."""
    if result.event_type == FileEventType.DELETED:
        logger.info(f"File deleted: {result.file_path}")
    elif not result.document:
        logger.info(f"No document found for file: {result.file_path}")
    else:
        document = result.document
        chunks = result.chunks

        file_name = document.metadata.file_metadata.file_name if document.metadata.file_metadata else "unknown"
        num_chunks = len(chunks) if chunks is not None else 0
        logger.info(f"Document: {file_name}.{document.metadata.file_metadata.file_extension} was processed ({num_chunks} chunks)")


async def main() -> None:
    """Main function to run the pipeline."""
    watch_directory = "assets"  # Directory to watch for markdown files
    ollama_url = "http://localhost:11434"
    embedding_model = "nomic-embed-text"
    
    # Create pipeline configuration
    config = PipelineConfig(
        watch_directory=watch_directory,
        ollama_url=ollama_url,
        embedding_model=embedding_model,
        chunk_size=100,
        chunk_overlap=200,
    )
    
    # Create pipeline
    pipeline = DataPipeline(config=config)
    
    try:
        logger.info("Starting data pipeline...")
        logger.info(f"Watching directory: {watch_directory}")
        logger.info(f"Using Ollama at: {ollama_url}")
        logger.info(f"Using embedding model: {embedding_model}")
        
        # Start the pipeline
        await pipeline.start(callback=pipeline_callback)
        
        # Keep running until interrupted
        logger.info("Pipeline is running. Press Ctrl+C to stop.")
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, stopping pipeline...")
    except Exception as e:
        logger.error(f"Error running pipeline: {e}")
    finally:
        await pipeline.stop()
        logger.info("Pipeline stopped.")


if __name__ == "__main__":
    asyncio.run(main()) 
