import logging
from typing import List
import numpy as np

from dependency_injector.wiring import inject, Provide
from apps.backend.services.embedding_service import EmbeddingService
from libs.models.documents import EmbeddedChunk, TextChunk
from libs.models.embeddings import Embedding

logger = logging.getLogger(__name__)


class DocumentEmbedder:
    """Handles embedding generation for documents and chunks."""

    @inject
    def __init__(
        self, embedder: EmbeddingService = Provide["Container.embedding_service"]
    ) -> None:
        self.embedder = embedder

    async def embed_document_chunks(
        self, chunks: List[TextChunk]
    ) -> List[EmbeddedChunk]:
        """Embed a list of document chunks."""
        if not chunks:
            return []

        texts = [chunk.content for chunk in chunks]
        analysed_batch = await self.embedder.generate_multiple_embeddings(texts)

        embedded_chunks: List[EmbeddedChunk] = []
        for chunk, embedding in zip(chunks, analysed_batch.embeddings):
            embedded_chunk = EmbeddedChunk.from_text_chunk(chunk, embedding)
            embedded_chunks.append(embedded_chunk)

        logger.info(f"Embedded {len(embedded_chunks)} chunks")
        return embedded_chunks

    async def close(self) -> None:
        """Close the embedder."""
        await self.embedder.close()


class SimilarityCalculator:
    async def calculate_similarity(
        self, embedding1: Embedding, embedding2: Embedding
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
        self, query_embedding: Embedding, embeddings: List[Embedding]
    ) -> List[float]:
        """Calculate similarities between a query embedding and a list of embeddings."""
        similarities = []
        for embedding in embeddings:
            similarity = await self.calculate_similarity(query_embedding, embedding)
            similarities.append(similarity)
        return similarities
