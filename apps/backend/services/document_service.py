import datetime
from typing import List
from pathlib import Path
import logging
import uuid
from dependency_injector.wiring import inject, Provide
from apps.backend.services.embedding_service import EmbeddingService
from libs.models.documents import AnalysedDocument, EmbeddedChunk, TextChunk, Document
from libs.storage.repositories.document import DocumentRepository
from libs.pipeline.pipeline import DataPipeline

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
        embedding_service: EmbeddingService = Provide["Container.embedding_service"],
    ) -> None:
        self.document_repo = document_repo
        self.embedding_service = embedding_service
        self.repo_base_path = Path.cwd()

    async def process_md_files(self, contents: List[str]) -> List[AnalysedDocument]:
        documents = [self._clean_md_files(f) for f in contents]
        document_titles = [
            f.metadata.frontmatter_metadata.title
            if f.metadata.frontmatter_metadata
            else None
            for f in documents
        ]
        existing_documents = [
            self.document_repo.get_document_by_title(title) if title else None
            for title in document_titles
        ]
        document_ids = [
            doc.id if doc else uuid.uuid4().hex for doc in existing_documents
        ]

        chunked_documents = [self._chunk_document(doc) for doc in documents]
        embedded_document_chunks = [
            await self._add_embeddings_to_chunks(doc) for doc in chunked_documents
        ]

        logging.info(f"---> {document_ids}, {embedded_document_chunks}, {documents}")
        completed_documents = [
            AnalysedDocument(
                id=doc_id if doc_id else uuid.uuid4().hex,
                metadata=doc.metadata,
                created_at=doc.created_at,
                updated_at=datetime.datetime.now(datetime.timezone.utc),
                content_hash=doc.content_hash,
                embedded_chunks=embedded_chunks,
                content=doc.content,
            )
            for doc, doc_id, embedded_chunks in zip(
                documents, document_ids, embedded_document_chunks
            )
        ]

        return [self.document_repo.create_document(doc) for doc in completed_documents]

    async def sync_documents_removed_from_gh(self, files: List[str]) -> None:
        """
        Remove documents that are no longer present in the GitHub repository.
        This method should be called when files are deleted from the repository.
        """
        raise NotImplementedError(
            "This method should be implemented to remove documents."
        )

    def _clean_md_files(self, file: str) -> Document:
        raise NotImplementedError(
            "This method should be implemented to process modified files."
        )

    async def _add_embeddings_to_chunks(
        self, chunks: List[TextChunk]
    ) -> List[EmbeddedChunk]:
        """Embed a list of document chunks."""
        if not chunks:
            return []

        texts = [chunk.content for chunk in chunks]
        analysed_batch = await self.embedding_service.generate_multiple_embeddings(
            texts
        )

        embedded_chunks: List[EmbeddedChunk] = []
        for chunk, embedding in zip(chunks, analysed_batch.embeddings):
            embedded_chunk = EmbeddedChunk.from_text_chunk(chunk, embedding)
            embedded_chunks.append(embedded_chunk)

        logger.info(f"Embedded {len(embedded_chunks)} chunks")
        return embedded_chunks

    def _chunk_document(self, doc: Document) -> List[TextChunk]:
        """
        Chunk a document into smaller parts for processing.
        This is a placeholder implementation and should be replaced with actual logic.
        """
        # Example logic: split the document into lines and return as chunks
        raise NotImplementedError(
            "This method should be implemented to process chunks."
        )
