from ast import Not
from calendar import c
from typing import List, Optional, Annotated
from httpx import delete
from sqlalchemy.orm import Session
from libs.models.embeddings import EmbeddingsBatch
from libs.storage.tables.documents import Document as DocumentDB
from libs.models.documents import Document, EmbeddedChunk, TextChunk, ProcessedDocument
from libs.storage.db import get_db_session
from fastapi import Depends


class DocumentRepository:
    def __init__(self, session: Session):
        self.session = session

    def upsert_document(self, document: Document) -> Document:
        try:
            existing_doc = self.get_full_document(document.id)
            if not existing_doc:
                return self.create_document(document)

            doc_data = document.model_dump(exclude_unset=True, exclude={"chunks"})
            for key, value in doc_data.items():
                setattr(existing_doc, key, value)

            if document.embedded_chunks:
                self._sync_document_chunks(
                    document.embedded_chunks, existing_doc.embedded_chunks
                )

            self.session.commit()
            return existing_doc

        except Exception as e:
            self.session.rollback()
            raise e
        finally:
            self.session.close()

    def create_document(self, document: Document) -> Document:
        try:
            doc_data = document.model_dump(exclude_unset=True, exclude={"chunks"})
            doc = DocumentDB(**doc_data)
            self.session.add(doc)
            self.session.commit()
            self.session.refresh(doc)

            if document.embedded_chunks:
                for chunk_data in document.embedded_chunks:
                    self._create_chunk(chunk_data)
                self.session.commit()

            return self.get_full_document(doc.id)

        except Exception:
            self.session.rollback()
            raise
        finally:
            self.session.close()

    def get_full_document(self, doc_id: str) -> Document:
        raise NotImplementedError()

    def get_document_by_id(self, doc_id: str) -> Optional[ProcessedDocument]:
        doc = self.session.query(DocumentDB).filter(DocumentDB.id == doc_id).first()
        return ProcessedDocument.model_validate(doc.__dict__) if doc else None

    def get_document_by_title(self, title: str) -> Optional[ProcessedDocument]:
        doc = self.session.query(DocumentDB).filter(DocumentDB.title == title).first()
        return ProcessedDocument.model_validate(doc.__dict__) if doc else None

    def save_documents(self, document: Document) -> Document:
        raise NotImplementedError()

    def get_chunks_by_document_id(self, doc_id: str) -> List[EmbeddedChunk]:
        raise NotImplementedError

    def delete_document(self, doc_id: str) -> None:
        raise NotImplementedError

    def _sync_document_chunks(
        self, new_chunks: list[EmbeddedChunk], current_chunks: list[EmbeddedChunk]
    ) -> None:
        if new_chunks[0].id != current_chunks[0].id:
            raise ValueError("Chunk IDs do not match between new and current chunks.")
        try:
            existing_chunk_ids = {chunk.id for chunk in current_chunks}
            incoming_chunk_ids = {chunk.id for chunk in new_chunks}

            chunks_to_delete = existing_chunk_ids - incoming_chunk_ids
            for chunk_id in chunks_to_delete:
                self._delete_chunk(chunk_id)

            for chunk_data in new_chunks:
                if chunk_data.id in existing_chunk_ids:
                    self._update_chunk(chunk_data)
                else:
                    self._create_chunk(chunk_data)

            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def _delete_chunk(self, chunk_id: str) -> None:
        raise NotImplementedError

    def _update_chunk(self, chunk_data: EmbeddedChunk) -> None:
        raise NotImplementedError

    def _create_chunk(self, chunk_data: EmbeddedChunk) -> None:
        raise NotImplementedError
