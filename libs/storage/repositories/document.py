from typing import List, Optional, Annotated
from sqlalchemy.orm import Session
from libs.storage.tables.documents import Document, DocumentChunk
from libs.models.Document import DocumentDB, DocumentChunkDB
from libs.storage.db import get_db_session
from fastapi import Depends


class DocumentRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_document(self, document: DocumentDB) -> DocumentDB:
        # Exclude chunks field when creating SQLAlchemy model since it's a relationship
        doc_data = document.model_dump(exclude_unset=True, exclude={'chunks'})
        doc = Document(**doc_data)
        self.session.add(doc)
        self.session.commit()
        self.session.refresh(doc)
        return DocumentDB.model_validate(doc.__dict__)

    def get_document_by_id(self, doc_id: str) -> Optional[DocumentDB]:
        doc = self.session.query(Document).filter(Document.id == doc_id).first()
        return DocumentDB.model_validate(doc.__dict__) if doc else None

    def create_chunk(self, chunk_data: DocumentChunkDB) -> DocumentChunkDB:
        chunk = DocumentChunk(**chunk_data.model_dump(exclude_unset=True))
        self.session.add(chunk)
        self.session.commit()
        self.session.refresh(chunk)
        return DocumentChunkDB.model_validate(chunk.__dict__)

    def get_chunks_by_document_id(self, doc_id: str) -> List[DocumentChunkDB]:
        chunks = self.session.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).all()
        return [DocumentChunkDB.model_validate(chunk.__dict__) for chunk in chunks]


def get_document_repository(session: Session = Depends(get_db_session)) -> DocumentRepository:
    return DocumentRepository(session)


document_repo_injection = Annotated[DocumentRepository, Depends(get_document_repository)]
