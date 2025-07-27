from typing import List
from pathlib import Path
import logging
from dependency_injector.wiring import inject, Provide
from libs.storage.repositories.document import DocumentRepository
from libs.pipeline.pipeline import DataPipeline

logger = logging.getLogger(__name__)


class EmbeddingService:
    @inject
    def __init__(
        self,
        document_repo: DocumentRepository = Provide["Container.document_repo"],
        pipeline: DataPipeline = Provide["Container.pipeline"],
    ) -> None:
        self.document_repo = document_repo
        self.pipeline = pipeline
        self.repo_base_path = Path.cwd()

    async def process_modified_files(self, files: List[str]) -> None:
        pass

    async def remove_documents(self, files: List[str]) -> None:
        pass
