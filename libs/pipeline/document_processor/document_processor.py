from datetime import datetime, timezone
from pathlib import Path
from typing import List
import logging
from libs.models.pipeline import DocumentMetadata, ProcessedDocument, ChunkData
from .metadata_extractor import MetadataExtractor
from .content_parser import ContentParser
from .content_chunker import ContentChunker

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Processes markdown documents and extracts all relevant information."""
    
    def __init__(self) -> None:
        self.metadata_extractor = MetadataExtractor()
        self.content_parser = ContentParser()
        self.content_chunker = ContentChunker()
    
    def process_document(self, file_path: Path) -> ProcessedDocument:
        """Process a markdown document and extract all relevant information."""
        try:
            content = file_path.read_text(encoding='utf-8')
            file_metadata = self.metadata_extractor.extract_file_metadata(file_path)
            parsed_content = self.content_parser.parse_markdown_content(content, self.metadata_extractor)
            
            result = ProcessedDocument(
              metadata=DocumentMetadata(
                file_metadata=file_metadata,
                frontmatter_metadata=parsed_content.metadata
              ),
              raw_content=content,
              processed_content=parsed_content.content,
              content_hash=self.content_chunker.calculate_content_hash(parsed_content.content),
              processed_at=datetime.now(timezone.utc)
           )
            
            logger.info(f"Processed document: {file_path.name}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {e}")
            raise
    
    def extract_chunks(self, content: str, chunk_size: int = 1000, overlap: int = 50) -> List[ChunkData]:
        """Extract chunks from the processed content."""
        return self.content_chunker.extract_chunks(content, chunk_size, overlap) 