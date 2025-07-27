from typing import List
from pathlib import Path
import asyncio
import logging
from dependency_injector.wiring import inject, Provide
from libs.storage.repositories.document import DocumentRepository
from libs.pipeline.pipeline import DataPipeline, pipeline_db_storage_callback_factory

logger = logging.getLogger(__name__)


# TODO: Add logic to process files that have changed,
# including fetching file content from the repo, and then processing them
# again through the pipeline or removing them accordingly

# TODO: Change the logic of the pipeline to rely on the utils and services here
# i.e. making the modules more reusbale and not tied to the backend service
# Change the logic so that the entry point is either a file or a payload of osme sort

# TODO: Find how to schedule jobs and set up queues in python
# to process files in the background, and then use the pipeline to process them
# and store them in the database (a whole job could live on top of this service)


class DocumentService:
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

    async def remove_documents_from_gh_path(self, files: List[str]) -> None:
        pass
