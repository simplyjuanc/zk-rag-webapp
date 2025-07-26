import logging
import os
from typing import List
from datetime import datetime, timezone
import httpx
import numpy as np
from pydantic import BaseModel

from libs.models.pipeline import DocumentChunk, EmbeddedChunk

logger = logging.getLogger(__name__)

DEFAULT_EMBEDDING_SIZE = 1536
BASE_EMBEDDING = [0.0] * DEFAULT_EMBEDDING_SIZE


class EmbeddingResult(BaseModel):
    embedding: List[float]
    embedding_model: str
    embedding_created_at: datetime


class EmbeddingBatch(BaseModel):
    embeddings: List[EmbeddingResult]
    batch_created_at: datetime


class OllamaEmbedder:
    def __init__(
        self, 
        base_url: str = os.getenv("OLLAMA_API_URL", "http://localhost:11434"),
        model: str = os.getenv("LLM_EMBEDDINGS_MODEL", "nomic-embed-text")
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.client = httpx.AsyncClient(timeout=30.0)

    async def embed_text(self, text: str) -> EmbeddingResult:
        try:
            response = await self.client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": text},
            )
            response.raise_for_status()

            data = response.json()
            embedding = data.get("embedding", [])

            if not embedding:
                raise ValueError("No embedding returned from Ollama")
            if not isinstance(embedding, list):
                raise ValueError("Embedding returned is not a list")
            try:
                embedding_floats = [float(x) for x in embedding]
            except Exception as conv_e:
                logger.error(f"Failed to convert embedding values to float: {conv_e}")
                raise ValueError("Embedding contains non-numeric values") from conv_e

            logger.debug(f"Generated embedding of length {len(embedding)}")
            return EmbeddingResult(
                embedding=embedding_floats,
                embedding_model=self.model,
                embedding_created_at=datetime.now(timezone.utc),
            )
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    async def embed_batch(self, texts: List[str]) -> EmbeddingBatch:
        embeddings: List[EmbeddingResult] = []
        batch_created_at = datetime.now(timezone.utc)

        for i, text in enumerate(texts):
            try:
                embedding = await self.embed_text(text)
                embeddings.append(embedding)

                if (i + 1) % 10 == 0:
                    logger.info(f"Processed {i + 1}/{len(texts)} embeddings")

            except Exception as e:
                logger.error(f"Error embedding text {i}: {e}")
                embeddings.append(
                    EmbeddingResult(
                        embedding=BASE_EMBEDDING,
                        embedding_model=self.model,
                        embedding_created_at=datetime.now(timezone.utc),
                    )
                )

        return EmbeddingBatch(
            embeddings=embeddings,
            batch_created_at=batch_created_at,
        )

    async def close(self) -> None:
        await self.client.aclose()


class DocumentEmbedder:
    """Handles embedding generation for documents and chunks."""

    def __init__(self, embedder: OllamaEmbedder):
        self.embedder = embedder

    async def embed_document_chunks(
        self, chunks: List[DocumentChunk]
    ) -> List[EmbeddedChunk]:
        """Embed a list of document chunks."""
        if not chunks:
            return []

        texts = [chunk.content for chunk in chunks]
        analysed_batch = await self.embedder.embed_batch(texts)

        embedded_chunks = []
        for chunk, embedding in zip(chunks, analysed_batch.embeddings):
            embedded_chunk = EmbeddedChunk(
                id=chunk.id,
                content=chunk.content,
                content_hash=chunk.content_hash,
                chunk_index=chunk.chunk_index,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                word_count_estimate=chunk.word_count_estimate,
                embedding=embedding.embedding,
                embedding_model=self.embedder.model,
                embedding_created_at=analysed_batch.batch_created_at,
            )
            embedded_chunks.append(embedded_chunk)

        logger.info(f"Embedded {len(embedded_chunks)} chunks")
        return embedded_chunks

    async def embed_query(self, query: str) -> EmbeddingResult:
        return await self.embedder.embed_text(query)

    async def close(self) -> None:
        """Close the embedder."""
        await self.embedder.close()


class SimilarityCalculator:
    async def calculate_similarity(
        self, embedding1: EmbeddingResult, embedding2: EmbeddingResult
    ) -> float:
        """Calculate cosine similarity between two embeddings."""
        try:
            vec1 = np.array(embedding1.embedding)
            vec2 = np.array(embedding2.embedding)

            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            similarity = np.dot(vec1, vec2) / (norm1 * norm2)
            return float(similarity)

        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0

    async def calculate_similarities(
        self, query_embedding: EmbeddingResult, embeddings: List[EmbeddingResult]
    ) -> List[float]:
        """Calculate similarities between a query embedding and a list of embeddings."""
        similarities = []
        for embedding in embeddings:
            similarity = await self.calculate_similarity(query_embedding, embedding)
            similarities.append(similarity)
        return similarities
