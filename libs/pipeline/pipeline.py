import asyncio
import logging
from pathlib import Path
from typing import Optional, Callable, Awaitable

from dependency_injector.wiring import inject, Provide
from apps.backend.services.embedding_service import EmbeddingService
from libs.models.pipeline import (
    PipelineConfig,
    FileEvent,
    FileEventType,
    PipelineResult,
    PipelineStatus,
    PipelineCallback,
)
from libs.utils.document_processor.document_processor import DocumentProcessor
from .watchers.file_watcher import FileWatcher

from .watchers.source_watcher import SourceWatcher
from .embedder import DocumentEmbedder, SimilarityCalculator

from libs.storage.db import get_db_session
from libs.storage.repositories.document import DocumentRepository
from libs.models.documents import AnalysedDocument
from libs.models.pipeline.processor import PipelineResult

logger = logging.getLogger(__name__)


class DataPipeline:
    """Main data pipeline that orchestrates file watching, processing, and embedding."""

    @inject
    def __init__(
        self,
        config: PipelineConfig,
        document_embedder: DocumentEmbedder = Provide["Container.document_embedder"],
        similarity_calculator: SimilarityCalculator = Provide[
            "Container.similarity_calculator"
        ],
    ):
        self.config = config

        self.file_watcher: SourceWatcher = FileWatcher(self.config.watch_directory)
        self.processor = DocumentProcessor()

        # Use injected services
        self.document_embedder = document_embedder
        self.similarity_calculator = similarity_calculator

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
            processed_document.content,
            self.config.chunk_size,
            self.config.chunk_overlap,
        )

        embedded_chunks = await self.document_embedder.embed_document_chunks(
            document_chunks
        )

        logger.info(f"Pipelined successfully processed: {file_path} ({event_type})")
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
    async def save_embedded_document_callback(result: PipelineResult) -> None:
        if not result.document or not result.chunks:
            return

        # Compose a dict with all possible fields, letting Pydantic handle missing/optional ones.
        # Create Document object using proper Pydantic validation
        embedded_document = AnalysedDocument.from_document_and_embeddings(
            document=result.document, embedded_chunks=result.chunks or []
        )

        def sync_db_ops() -> None:
            session = next(get_db_session())
            repo = DocumentRepository(session)
            repo.create_document(embedded_document)
            session.close()

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, sync_db_ops)

    return save_embedded_document_callback
