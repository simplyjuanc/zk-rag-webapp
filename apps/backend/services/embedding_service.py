from datetime import datetime, timezone
import os
from typing import List
import logging

import httpx
from libs.models.embeddings import Embedding, EmbeddingsBatch
from config import settings

logger = logging.getLogger(__name__)

DEFAULT_EMBEDDING_SIZE = 1536
BASE_EMBEDDING = [0.0] * DEFAULT_EMBEDDING_SIZE


class EmbeddingService:
    def __init__(self) -> None:
        self.base_url = settings.ollama_url
        self.model = settings.llm_embeddings_model
        self.client = httpx.AsyncClient(timeout=30.0)

    async def generate_embedding(self, text: str) -> Embedding:
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
            return Embedding(
                embedding=embedding_floats,
                embedding_model=self.model,
                embedding_created_at=datetime.now(timezone.utc),
            )
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    async def generate_multiple_embeddings(self, texts: List[str]) -> EmbeddingsBatch:
        embeddings: List[Embedding] = []
        batch_created_at = datetime.now(timezone.utc)

        for i, text in enumerate(texts):
            try:
                embedding = await self.generate_embedding(text)
                embeddings.append(embedding)

                if (i + 1) % 10 == 0:
                    logger.info(f"Processed {i + 1}/{len(texts)} embeddings")

            except Exception as e:
                logger.error(f"Error embedding text {i}: {e}")
                embeddings.append(
                    Embedding(
                        embedding=BASE_EMBEDDING,
                        embedding_model=self.model,
                        embedding_created_at=datetime.now(timezone.utc),
                    )
                )

        return EmbeddingsBatch(
            embeddings=embeddings,
            created_at=batch_created_at,
        )

    async def close(self) -> None:
        await self.client.aclose()
