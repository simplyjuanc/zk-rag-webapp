import asyncio
import logging
from pathlib import Path
from typing import Optional, Callable, Awaitable
import uuid

from libs.models.pipeline import (
    PipelineConfig,
    FileEvent,
    FileEventType,
    DocumentChunk,
    PipelineResult,
    PipelineStatus,
    PipelineCallback,
)
from .watchers.file_watcher import FileWatcher
from libs.pipeline.document_processor import DocumentProcessor

from .watchers.source_watcher import SourceWatcher
from .embedder import EmbeddingService, DocumentEmbedder, SimilarityCalculator

# --- DB Storage Callback for Pipeline ---
from libs.storage.db import get_db_session
from libs.storage.repositories.document import DocumentRepository
from libs.models.Document import DocumentDB, DocumentChunkDB
from libs.models.pipeline.processor import PipelineResult

logger = logging.getLogger(__name__)


class DataPipeline:
    """Main data pipeline that orchestrates file watching, processing, and embedding."""

    def __init__(
        self,
        config: PipelineConfig,
    ):
        self.config = config

        self.file_watcher: SourceWatcher = FileWatcher(self.config.watch_directory)
        self.processor = DocumentProcessor()

        self.ollama_embedder = EmbeddingService(
            self.config.ollama_url, self.config.embedding_model
        )
        self.document_embedder = DocumentEmbedder(self.ollama_embedder)
        self.similarity_calculator = SimilarityCalculator()

        self.is_running = False
        self.processing_queue: asyncio.Queue[FileEvent] = asyncio.Queue()
        self.callback: Optional[PipelineCallback] = None

    async def start(self, callback: Optional[PipelineCallback] = None) -> None:
        """Start the data pipeline."""
        if self.is_running:
            logger.warning("Pipeline is already running")
            return

        self.callback = callback
        self.is_running = True

        self.processing_task = asyncio.create_task(self._process_queue())
        self.file_watcher.start(self._on_file_change)
        self.file_watcher.scan_existing_files(self._on_file_change)

        logger.info("Data pipeline started")

    async def stop(self) -> None:
        """Stop the data pipeline."""
        if not self.is_running:
            return

        self.is_running = False

        # Stop file watcher
        self.file_watcher.stop()

        # Cancel processing task
        if hasattr(self, "processing_task"):
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass

        # Close embedders
        await self.document_embedder.close()

        logger.info("Data pipeline stopped")

    def _on_file_change(self, file_path: Path, event_type: FileEventType) -> None:
        """Handle file change events."""
        if not self.is_running:
            return

        file_event = FileEvent(file_path=file_path, event_type=event_type)

        asyncio.create_task(self.processing_queue.put(file_event))

    async def _process_queue(self) -> None:
        """Process items from the queue."""
        while self.is_running:
            try:
                file_event = await asyncio.wait_for(
                    self.processing_queue.get(), timeout=1.0
                )
                await self._process_file(file_event)
                self.processing_queue.task_done()

            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in processing queue: {e}")

    async def _process_file(self, file_event: FileEvent) -> None:
        """Process a single file."""
        try:
            logger.info(
                f"Processing file: {file_event.file_path} ({file_event.event_type})"
            )

            if file_event.event_type == FileEventType.DELETED:
                await self._handle_file_deletion(file_event.file_path)
            else:
                await self._handle_file_processing(
                    file_event.file_path, file_event.event_type
                )

        except Exception as e:
            logger.error(f"Error processing file {file_event.file_path}: {e}")

    async def _handle_file_processing(
        self, file_path: Path, event_type: FileEventType
    ) -> PipelineResult:
        """Handle file processing (create/modify)."""
        logger.info(f"Processing file: {file_path} ({event_type})")
        processed_document = self.processor.process_document(file_path)
        document_chunks = self.processor.extract_chunks(
            processed_document.processed_content,
            self.config.chunk_size,
            self.config.chunk_overlap,
        )

        embedded_chunks = await self.document_embedder.embed_document_chunks(
            document_chunks
        )

        logger.info(f"Processed file successfully: {file_path} ({event_type})")
        result = PipelineResult.from_processing(
            document=processed_document, chunks=embedded_chunks, event_type=event_type
        )

        # Call callback if provided
        if self.callback:
            try:
                await self.callback(result)
            except Exception as e:
                logger.error(f"Error in pipeline callback: {e}")

        logger.info(
            f"Successfully processed {file_path.name} with {len(embedded_chunks)} chunks"
        )
        return result

    async def _handle_file_deletion(self, file_path: Path) -> None:
        """Handle file deletion."""
        # Create result using Pydantic model
        result = PipelineResult.from_deletion(str(file_path))

        # Call callback if provided
        if self.callback:
            try:
                await self.callback(result)
            except Exception as e:
                logger.error(f"Error in pipeline callback for deletion: {e}")

        logger.info(f"Handled deletion of {file_path.name}")

    async def process_single_file(self, file_path: Path) -> PipelineResult:
        """Process a single file manually."""
        return await self._handle_file_processing(file_path, FileEventType.MANUAL)

    def get_status(self) -> PipelineStatus:
        """Get pipeline status."""
        return PipelineStatus(
            is_running=self.is_running,
            watch_directory=self.config.watch_directory,
            queue_size=self.processing_queue.qsize(),
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
        )


def pipeline_db_storage_callback_factory() -> Callable[
    [PipelineResult], Awaitable[None]
]:
    async def pipeline_db_storage_callback(result: PipelineResult) -> None:
        # Only store if document and chunks are present
        if not result.document or not result.chunks:
            return
        # Map ProcessedDocument to DocumentDB fields
        # Use the Pydantic DocumentDB model for mapping, leveraging its validation and defaults.
        from libs.models.Document import DocumentDB

        # Compose a dict with all possible fields, letting Pydantic handle missing/optional ones.
        file_meta = (
            getattr(result.document.metadata, "file_metadata", None)
            if result.document.metadata
            else None
        )
        front_meta = (
            getattr(result.document.metadata, "frontmatter_metadata", None)
            if result.document.metadata
            else None
        )

        doc_db_model = DocumentDB(
            id=getattr(result.document, "id", None) or uuid.uuid4().hex,
            file_path=getattr(file_meta, "file_path", None) or "",
            file_name=getattr(file_meta, "file_name", None) or "",
            file_extension=getattr(file_meta, "file_extension", None) or "",
            file_size=getattr(file_meta, "file_size", None) or 0,
            content_hash=result.document.content_hash,
            raw_content=result.document.raw_content,
            processed_content=result.document.processed_content,
            title=getattr(front_meta, "title", None),
            author=getattr(front_meta, "author", None),
            document_type=getattr(front_meta, "type", None),
            category=getattr(front_meta, "category", None),
            tags=getattr(front_meta, "tags", None),
            source=getattr(front_meta, "source", None),
            created_on=getattr(front_meta, "created_on", None),
            last_updated=getattr(front_meta, "last_updated", None),
            content_created_at=getattr(file_meta, "content_created_at", None),
            content_modified_at=getattr(file_meta, "content_modified_at", None),
            processed_at=str(result.document.processed_at)
            if result.document.processed_at
            else None,
        )
        # Use sync DB session in thread executor
        loop = asyncio.get_event_loop()

        def sync_db_ops() -> None:
            session = next(get_db_session())
            repo = DocumentRepository(session)
            doc_db = repo.create_document(doc_db_model)
            if result.chunks:
                for chunk in result.chunks:
                    chunk_data = DocumentChunkDB(
                        id=chunk.id,
                        document_id=doc_db.id,
                        content=chunk.content,
                        content_hash=chunk.content_hash,
                        chunk_index=chunk.chunk_index,
                        embedding=str(getattr(chunk, "embedding", None)),
                        embedding_model=getattr(chunk, "embedding_model", None),
                        embedding_created_at=str(
                            getattr(chunk, "embedding_created_at", None)
                        ),
                    )
                    repo.create_chunk(chunk_data)
            session.close()

        await loop.run_in_executor(None, sync_db_ops)

    return pipeline_db_storage_callback
