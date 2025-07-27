from pydantic import BaseModel


from datetime import datetime
from typing import List


class Embedding(BaseModel):
    embedding: List[float]
    embedding_model: str
    embedding_created_at: datetime


class BatchEmbedding(BaseModel):
    embeddings: List[Embedding]
    batch_created_at: datetime
