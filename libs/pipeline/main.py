#!/usr/bin/env python3
import sys
import asyncio
import logging
import os
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from libs.models.pipeline import FileEventType
from libs.pipeline import DataPipeline
from libs.models.pipeline import PipelineConfig, PipelineResult
from libs.storage.repositories.document import DocumentRepository
from libs.storage.mappers.pipeline_mappers import (
    map_processed_document_to_db,
    map_pipeline_chunks_to_db,
)
from libs.storage.db import get_db_session

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


async def store_pipeline_results_to_db(result: PipelineResult) -> None:
    if result.event_type == FileEventType.DELETED:
        logger.info(f"File deleted: {result.file_path}")
        # TODO: Implement document deletion from database
        return

    if not result.document or not result.chunks:
        logger.warning(f"No document or chunks found for file: {result.file_path}")
        return

    session = next(get_db_session())
    doc_repo = DocumentRepository(session)
    try:
        mapped_document = map_processed_document_to_db(result.document)
        stored_document = doc_repo.create_document(mapped_document)

        mapped_chunks = map_pipeline_chunks_to_db(result.chunks, stored_document.id)
        stored_chunks = []
        for chunk_db in mapped_chunks:
            stored_chunk = doc_repo.create_chunk(chunk_db)
            stored_chunks.append(stored_chunk)

        logger.info(
            f"Stored {len(stored_chunks)} chunks for document {stored_document.file_name}"
        )

    except Exception as e:
        logger.error(f"Error storing pipeline results to database: {e}")
        if "session" in locals():
            session.rollback()
        raise
    finally:
        if "session" in locals():
            session.close()


async def main() -> None:
    watch_directory = "assets"
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

        # Start the pipeline with database storage callback
        await pipeline.start(callback=store_pipeline_results_to_db)

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
