#!/usr/bin/env python3
import sys
import asyncio
import logging
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from libs.models.documents import Document
from libs.models.pipeline import FileEventType
from libs.pipeline import DataPipeline
from libs.models.pipeline import PipelineConfig, PipelineResult
from libs.storage.repositories.document import DocumentRepository
from libs.storage.db import get_db_session
from libs.di.container import container


logging.basicConfig(
    level=logging.WARNING, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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
        mapped_document = Document.from_document_and_embeddings(
            result.document, result.chunks
        )
        stored_document = doc_repo.create_document(mapped_document)
        title = (
            stored_document.metadata.frontmatter_metadata.title
            if stored_document.metadata.frontmatter_metadata
            else "Unknown"
        )

        logger.info(
            f'Stored {len(stored_document.embedded_chunks)} chunks for document "{title}"'
        )

    except Exception as e:
        logger.error(f"Error storing pipeline results to database: {e}")
        if session is not None:
            session.rollback()
        raise
    finally:
        if session is not None:
            session.close()


EMBEDDING_MODEL = "nomic-embed-text"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
WATCH_DIRECTORY = "assets"


async def main() -> None:
    container.wire(
        modules=[
            "libs.pipeline.pipeline",
            "libs.pipeline.embedder",
            "apps.backend.services.embedding_service",
        ]
    )

    # Get the pipeline from the DI container (dependencies auto-injected)
    pipeline = container.pipeline()

    try:
        logger.info("Starting data pipeline...")
        logger.info(f"Watching directory: {WATCH_DIRECTORY}")
        logger.info(f"Using Ollama at: {OLLAMA_URL}")
        logger.info(f"Using embedding model: {EMBEDDING_MODEL}")

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
