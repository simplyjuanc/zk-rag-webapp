#!/usr/bin/env python3
"""Simple test script for the data pipeline components."""

import asyncio
import tempfile
import os
from pathlib import Path

from libs.models.pipeline import EmbeddedChunk, TextChunk
from libs.models.documents import ProcessedDocument
from libs.models.embeddings import EmbeddingsBatch
from libs.pipeline.embedder import SimilarityCalculator
from libs.utils.document_processor.document_processor import DocumentProcessor


async def test_processor() -> tuple[ProcessedDocument, list[TextChunk]]:
    """Test the document processor."""
    print("Testing DocumentProcessor...")
    test_content = """---
        author: [Test Author]
        category: [test, example]
        created_on: 2024-01-01
        last updated: 2024-01-02
        ---

        # Test Document

        This is a test document with some content.

        ## Section 1

        Some content in section 1.

        ## Section 2

        More content in section 2.
    """.strip()

    # Create a temporary Markdown file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(test_content)
        temp_file = f.name

    try:
        processor = DocumentProcessor()
        result = processor.process_document(Path(temp_file))

        if (
            not result.metadata.file_metadata
            or not result.metadata.frontmatter_metadata
        ):
            raise ValueError("Processed document has no metadata")

        print(f"✓ Processed document: {result.metadata.file_metadata.file_name}")
        print(f"  - Content hash: {result.content_hash[:16]}...")
        print(
            f"  - Author: {result.metadata.frontmatter_metadata.author if result.metadata.frontmatter_metadata.author else 'N/A'}"
        )
        print(
            f"  - Category: {result.metadata.frontmatter_metadata.category if result.metadata.frontmatter_metadata.category else 'N/A'}"
        )
        print(
            f"  - Created: {result.metadata.frontmatter_metadata.created_on if result.metadata.frontmatter_metadata.created_on else 'N/A'}"
        )

        if not result.content:
            raise ValueError("Processed document has no content")

        chunks = processor.extract_chunks(result.content, chunk_size=100, overlap=20)
        print(f"  - Generated {len(chunks)} chunks")

        return result, [TextChunk.model_validate(chunk) for chunk in chunks]

    finally:
        os.unlink(temp_file)


async def test_embedder() -> EmbeddingsBatch | None:
    """Test the document embedder."""
    print("\nTesting DocumentEmbedder...")

    try:
        # Test connection to Ollama
        embedder = EmbeddingService()

        # Test single embedding
        test_text = "This is a test sentence for embedding."
        embedding = await embedder.generate_embedding(test_text)

        print(f"✓ Generated embedding of length: {len(embedding.embedding)}")
        print(f"  - First few values: {embedding.embedding[:5]}")

        # Test batch embedding
        test_texts = [
            "First test sentence.",
            "Second test sentence.",
            "Third test sentence.",
        ]

        batch_embedding_result = await embedder.generate_multiple_embeddings(test_texts)
        embeddings = batch_embedding_result.embeddings
        print(f"✓ Generated {len(embeddings)} batch embeddings")

        similarity_calculator = SimilarityCalculator()

        similarity = await similarity_calculator.calculate_similarity(
            embeddings[0], embeddings[1]
        )
        print(f"✓ Calculated similarity: {similarity:.4f}")

        await embedder.close()
        return batch_embedding_result

    except Exception as e:
        print(f"✗ Embedder test failed: {e}")
        print("  Make sure Ollama is running with the nomic-embed-text model")
        return None


async def test_pipeline_integration() -> bool:
    """Test basic pipeline integration."""
    print("\nTesting Pipeline Integration...")

    document, chunks = await test_processor()
    embeddings = await test_embedder()

    if embeddings and chunks:
        print("✓ Pipeline components work together")

        # Simulate embedding chunks
        test_chunks = chunks[:2]  # Use first 2 chunks
        embedded_chunks = []

        for i, chunk in enumerate(test_chunks):
            embedded_chunk = EmbeddedChunk(
                id=chunk.id,
                content=chunk.content,
                content_hash=chunk.content_hash,
                chunk_index=chunk.chunk_index,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                word_count_estimate=chunk.word_count_estimate,
                embedding=embeddings.embeddings[
                    i % len(embeddings.embeddings)
                ].embedding,
                embedding_model="nomic-embed-text",
                embedding_created_at=embeddings.created_at,
            )
            embedded_chunks.append(embedded_chunk)

        print(f"✓ Successfully embedded {len(embedded_chunks)} chunks")

        return True
    else:
        print("✗ Pipeline integration test failed")
        return False


async def main() -> None:
    """Run all tests."""
    print("Running Data Pipeline Tests")
    print("=" * 40)

    success = await test_pipeline_integration()

    print("\n" + "=" * 40)
    if success:
        print("✓ All tests passed!")
        print("\nThe pipeline is ready to use.")
        print("Run 'python scripts/main.py' to start the pipeline.")
    else:
        print("✗ Some tests failed.")
        print("Please check the error messages above.")


if __name__ == "__main__":
    asyncio.run(main())
