from typing import List
from pathlib import Path
import asyncio
import logging
from dependency_injector.wiring import inject, Provide
from libs.storage.repositories.document import DocumentRepository
from libs.pipeline.pipeline import DataPipeline, pipeline_db_storage_callback_factory

logger = logging.getLogger(__name__)


class DocumentService:
    @inject
    def __init__(
        self,
        document_repo: DocumentRepository = Provide["Container.document_repo"],
        pipeline: DataPipeline = Provide["Container.pipeline"],
    ) -> None:
        self.document_repo = document_repo
        self.pipeline = pipeline
        self._pipeline_initialized = False
        self.repo_base_path = Path.cwd()

    async def process_modified_files(self, files: List[str]) -> List[str]:
        await asyncio.sleep(10)
        return files

    async def _ensure_pipeline_initialized(self) -> None:
        if not self._pipeline_initialized:
            callback = pipeline_db_storage_callback_factory()
            await self.pipeline.start(callback=callback)
            self._pipeline_initialized = True
            logger.info("Pipeline initialized for embedding service")

    def _resolve_file_path(self, file_path: str) -> Path:
        path = Path(file_path)
        if path.is_absolute():
            return path
        else:
            return self.repo_base_path / path

    async def process_files(self, file_paths: List[str]) -> List[str]:
        await self._ensure_pipeline_initialized()
        processed_files = []
        for file_path in file_paths:
            try:
                resolved_path = self._resolve_file_path(file_path)
                if not resolved_path.exists():
                    logger.warning(f"File does not exist: {resolved_path}")
                    continue
                if not resolved_path.suffix.lower() == ".md":
                    logger.info(f"Skipping non-markdown file: {resolved_path}")
                    continue
                logger.info(f"Processing file: {resolved_path}")
                result = await self.pipeline.process_single_file(resolved_path)
                processed_files.append(file_path)
                logger.info(f"Successfully processed: {file_path}")
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
        return processed_files

    async def process_single_file(self, file_path: str) -> bool:
        await self._ensure_pipeline_initialized()
        try:
            resolved_path = self._resolve_file_path(file_path)
            if not resolved_path.exists():
                logger.warning(f"File does not exist: {resolved_path}")
                return False
            if not resolved_path.suffix.lower() == ".md":
                logger.info(f"Skipping non-markdown file: {resolved_path}")
                return False
            logger.info(f"Processing file: {resolved_path}")
            result = await self.pipeline.process_single_file(resolved_path)
            logger.info(f"Successfully processed: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return False

    async def cleanup(self) -> None:
        if self._pipeline_initialized:
            await self.pipeline.stop()
            self._pipeline_initialized = False
            logger.info("Pipeline stopped for embedding service")
