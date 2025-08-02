import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List
import logging

from libs.models.documents import TextChunk, Document
from libs.models.pipeline.metadata import DocumentMetadata
from .metadata_extractor import MetadataValidator
from .content_parser import MarkdownParser

logger = logging.getLogger(__name__)

OVERLAP_ESTIMATED_LINE_LENGTH = 50


class DocumentProcessor:
    """Processes Markdown documents and extracts all relevant information."""

    def __init__(self) -> None:
        self.metadata_extractor = MetadataValidator()
        self.content_parser = MarkdownParser()

    def process_document(self, file_path: Path) -> Document:
        """Process a Markdown document and extract all relevant information."""
        try:
            content = file_path.read_text(encoding="utf-8")
            file_metadata = self.metadata_extractor.extract_file_metadata(file_path)
            parsed_content = self.content_parser.parse_content(
                content, self.metadata_extractor
            )

            result = Document(
                id=uuid.uuid4().hex,
                metadata=DocumentMetadata(
                    file_metadata=file_metadata,
                    frontmatter_metadata=parsed_content.metadata,
                ),
                content=parsed_content.content,
                content_hash=self.__calculate_content_hash(parsed_content.content),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                deleted_at=None,
            )

            logger.info(f"Processed document: {file_path.name}")
            return result

        except Exception as e:
            logger.error(f"Error processing document {file_path}: {e}")
            raise

    def extract_chunks(
        self, content: str, chunk_size: int = 1000, overlap: int = 200
    ) -> List[TextChunk]:
        chunks: List[TextChunk] = []
        lines = content.split("\n")
        current_chunk: List[str] = []
        current_length = 0

        document_id = uuid.uuid4().hex

        for line in lines:
            line_length = len(line) + 1  # +1 for newline

            # If we can add the line to the current chunk, do it
            if not (current_length + line_length > chunk_size and current_chunk):
                current_chunk.append(line)
                current_length += line_length
            else:
                # Else finalise the current chunk and start a new one
                chunk_text = "\n".join(current_chunk)
                chunks.append(
                    TextChunk(
                        id=uuid.uuid4().hex,
                        document_id=document_id,
                        content=chunk_text,
                        content_hash=self.__calculate_content_hash(chunk_text),
                        chunk_index=len(chunks),
                        word_count_estimate=len(chunk_text.split()),
                    )
                )

                # Start new chunk with overlap
                if overlap > 0:
                    # Calculate how many lines to overlap (roughly overlap/50 characters per line)
                    overlap_lines_count = max(
                        1,
                        min(
                            len(current_chunk), overlap // OVERLAP_ESTIMATED_LINE_LENGTH
                        ),
                    )
                    overlap_lines = current_chunk[-overlap_lines_count:]
                    current_chunk = overlap_lines + [line]
                    current_length = sum(len(l) + 1 for l in current_chunk)
                else:
                    current_chunk = [line]
                    current_length = line_length

        # Add final chunk if there's remaining content
        if current_chunk:
            chunk_text = "\n".join(current_chunk)
            chunks.append(
                TextChunk(
                    id=uuid.uuid4().hex,
                    document_id=document_id,
                    content=chunk_text,
                    content_hash=self.__calculate_content_hash(chunk_text),
                    chunk_index=len(chunks),
                    word_count_estimate=len(chunk_text.split()),
                )
            )

        return chunks

    def __calculate_content_hash(self, content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
