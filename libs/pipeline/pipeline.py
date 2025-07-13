import asyncio
import logging
from pathlib import Path
from typing import Optional

from libs.models.pipeline import (
    PipelineConfig,
    FileEvent,
    FileEventType,
    DocumentMetadata,
    DocumentChunk,
    EmbeddedChunk,
    ProcessedDocument,
    PipelineResult,
    PipelineStatus,
    PipelineCallback,
    DocumentMetadata
)

from .file_watcher import FileWatcher
from .processor import DocumentProcessor
from .embedder import OllamaEmbedder, DocumentEmbedder, SimilarityCalculator

logger = logging.getLogger(__name__)


class DataPipeline:
    """Main data pipeline that orchestrates file watching, processing, and embedding."""
    
    def __init__(
        self,
        config: PipelineConfig,
    ):
        self.config = config
        
        self.file_watcher = FileWatcher(self.config.watch_directory)
        self.processor = DocumentProcessor()
        
        self.ollama_embedder = OllamaEmbedder(self.config.ollama_url, self.config.embedding_model)
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
        if hasattr(self, 'processing_task'):
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
        
        file_event = FileEvent(
            file_path=file_path,
            event_type=event_type
        )
        
        asyncio.create_task(self.processing_queue.put(file_event))
    
    async def _process_queue(self) -> None:
        """Process items from the queue."""
        while self.is_running:
            try:
                # Get item from queue with timeout
                file_event = await asyncio.wait_for(self.processing_queue.get(), timeout=1.0)
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
            logger.info(f"Processing file: {file_event.file_path} ({file_event.event_type})")
            
            if file_event.event_type == FileEventType.DELETED:
                await self._handle_file_deletion(file_event.file_path)
            else:
                await self._handle_file_processing(file_event.file_path, file_event.event_type)
                
        except Exception as e:
            logger.error(f"Error processing file {file_event.file_path}: {e}")
    
    async def _handle_file_processing(self, file_path: Path, event_type: FileEventType) -> PipelineResult:
        """Handle file processing (create/modify)."""
        processed_document = self.processor.process_document(file_path)
        
        chunk_data_list = self.processor.extract_chunks(
            processed_document.processed_content,
            self.config.chunk_size,
            self.config.chunk_overlap
        )
        
        document_chunks = [
            DocumentChunk(
                content=chunk.content,
                content_hash=chunk.content_hash,
                chunk_index=chunk.chunk_index,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                word_count_estimate=chunk.word_count_estimate
            )
            for chunk in chunk_data_list
        ]
        
        embedded_chunks = await self.document_embedder.embed_document_chunks(document_chunks)
        
        result = PipelineResult.from_processing(
            document=processed_document,
            chunks=embedded_chunks,
            event_type=event_type
        )
        
        if self.callback:
            try:
                await self.callback(result)
            except Exception as e:
                logger.error(f"Error in pipeline callback: {e}")
        
        logger.info(f"Successfully processed {file_path.name} with {len(embedded_chunks)} chunks")
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