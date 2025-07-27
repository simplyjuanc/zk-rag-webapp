from typing import List, Optional, Annotated
from httpx import delete
from sqlalchemy.orm import Session
from libs.models.Embeddings import EmbeddingsBatch
from libs.storage.tables.documents import Document as DocumentDB
from libs.models.documents import Document, EmbeddedChunk, TextChunk, ProcessedDocument
from libs.storage.db import get_db_session
from fastapi import Depends


class DocumentRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_document(self, document: Document) -> Document:
        try:
            doc_data = document.model_dump(exclude_unset=True, exclude={"chunks"})
            doc = DocumentDB(**doc_data)
            self.session.add(doc)
            self.session.commit()
            self.session.refresh(doc)

            if document.embedded_chunks:
                for chunk_data in document.embedded_chunks:
                    self.create_chunk(chunk_data)
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
        """Save a complete document to the database."""
        raise NotImplementedError()

    def create_chunk(self, chunk_data: EmbeddingsBatch) -> EmbeddingsBatch:
        chunk = TextChunk(**chunk_data.model_dump(exclude_unset=True))
        self.session.add(chunk)
        self.session.commit()
        self.session.refresh(chunk)
        return EmbeddingsBatch.model_validate(chunk.__dict__)

    def get_chunks_by_document_id(self, doc_id: str) -> List[EmbeddedChunk]:
        chunks = (
            self.session.query(TextChunk).filter(TextChunk.document_id == doc_id).all()
        )
        return [EmbeddedChunk.model_validate(chunk.__dict__) for chunk in chunks]

    def delete_document(self, doc_id: str) -> DocumentDB:
        doc = self.session.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            raise ValueError(f"Document with id {doc_id} not found")
        self.session.delete(doc)
        self.session.commit()
        return DocumentDB.model_validate(doc.__dict__)
