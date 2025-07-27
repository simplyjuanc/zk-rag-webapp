from pydantic import BaseModel


from datetime import datetime
from typing import List


class Embedding(BaseModel):
    embedding: List[float]
    embedding_model: str
    embedding_created_at: datetime


class EmbeddingsBatch(BaseModel):
    embeddings: List[Embedding]
    created_at: datetime
