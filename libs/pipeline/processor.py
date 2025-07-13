"""Document processor for parsing markdown files and extracting metadata."""

import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any
import frontmatter  # type: ignore
import logging

from libs.models.pipeline import (
    FileMetadata,
    FrontmatterMetadata,
    ChunkData,
    ParsedContent,
    DocumentMetadata,
    ProcessedDocument
)

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """Extracts metadata from files and content."""
    date_format = r'\s*(\d{4}-\d{2}-\d{2})'

    def __init__(self) -> None:
        self.metadata_patterns = {
            'created_on': r'created_on: *({})'.format(self.date_format),
            'last_updated': r'last updated: *({})'.format(self.date_format),
            'author': r'author: *\[?([^\]]+)\]?',
            'category': r'category: *\[?([^\]]+)\]?',
            'type': r'type: *\[?([^\]]+)\]?',
            'source': r'source: *([^\n]+)',
        }
    
    def extract_file_metadata(self, file_path: Path) -> FileMetadata:
        """Extract metadata from the file system."""
        stat = file_path.stat()
        
        return FileMetadata(
            file_path=str(file_path),
            file_name=file_path.name,
            file_extension=file_path.suffix.lower(),
            file_size=stat.st_size,
            content_created_at=datetime.fromtimestamp(stat.st_ctime),
            content_modified_at=datetime.fromtimestamp(stat.st_mtime),
        )

    def extract_normalised_metadata(self, metadata_dict: Dict[str, Any], content: str) -> FrontmatterMetadata:
        """Extract metadata from content and normalise the dictionary."""
        extracted_metadata = self.extract_content_metadata(content)
        metadata_dict.update(extracted_metadata)
        normalised_metadata_dict = self.normalize_metadata_dict(metadata_dict)
        return FrontmatterMetadata.model_validate(normalised_metadata_dict)
    
    def extract_content_metadata(self, content: str) -> Dict[str, Any]:
        """Extract metadata using regex patterns."""
        metadata = {}
        
        for key, pattern in self.metadata_patterns.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if key in ['author', 'category', 'type']:
                    # Handle array-like values
                    if value.startswith('[') and value.endswith(']'):
                        value = [item.strip() for item in value[1:-1].split(',')]
                    else:
                        value = [value]
                metadata[key] = value
        
        return metadata
    
    def normalize_metadata_dict(self, metadata_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize the metadata dictionary."""
        list_keys = {'author', 'category', 'type', 'tags'}
        for key, value in metadata_dict.items():
            if value is None:
                continue
            if key in list_keys:
                if isinstance(value, str):
                    val = value.strip()
                    if val.startswith('[') and val.endswith(']'):
                        items = [item.strip() for item in val[1:-1].split(',') if item.strip()]
                        metadata_dict[key] = items
                    else:
                        metadata_dict[key] = [val] if val else []
                elif isinstance(value, list):
                    metadata_dict[key] = [str(item).strip() for item in value if str(item).strip()]
                else:
                    metadata_dict[key] = [str(value).strip()]
            else:
                metadata_dict[key] = str(value)
        return metadata_dict


class ContentParser:
    """Parses and cleans markdown content."""
    
    def parse_markdown_content(self, content: str, metadata_extractor: MetadataExtractor) -> ParsedContent:
        """Parse markdown content and extract frontmatter and content."""
        try:
            post = frontmatter.loads(content)  # type: ignore
            metadata_dict = dict(post.metadata) if post.metadata else {}
            clean_content = post.content
            
        except Exception as e:
            logger.warning(f"Could not parse frontmatter: {e}")
            metadata_dict = {}
            clean_content = content
        
        processed_content = self._clean_content(clean_content)
        
        return ParsedContent(
            metadata=metadata_extractor.extract_normalised_metadata(metadata_dict, content),
            content=processed_content,
        )
    
    def _clean_content(self, content: str) -> str:
        """Clean and normalize the markdown content."""
        # Remove excessive whitespace
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        # Remove HTML comments
        content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
        
        # Normalize line endings
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        
        return content.strip()


class ContentChunker:
    """Handles content chunking and hashing."""
    
    def extract_chunks(self, content: str, chunk_size: int = 1000, overlap: int = 200) -> List[ChunkData]:
        """Extract chunks from the processed content."""
        chunks: List[ChunkData] = []
        lines = content.split('\n')
        current_chunk: List[str] = []
        current_length = 0
        chunk_start_line = 0
        
        for i, line in enumerate(lines):
            line_length = len(line) + 1  # +1 for newline
            
            # If adding this line would exceed chunk size and we have content
            if current_length + line_length > chunk_size and current_chunk:
                # Create chunk from current content
                chunk_text = '\n'.join(current_chunk)
                chunks.append(ChunkData(
                    content=chunk_text,
                    content_hash=self.calculate_content_hash(chunk_text),
                    chunk_index=len(chunks),
                    start_line=chunk_start_line,
                    end_line=i - 1,
                    word_count_estimate=len(chunk_text.split()),
                ))
                
                # Start new chunk with overlap
                if overlap > 0:
                    # Calculate how many lines to overlap (roughly overlap/50 characters per line)
                    overlap_lines_count = max(1, min(len(current_chunk), overlap // 50))
                    overlap_lines = current_chunk[-overlap_lines_count:]
                    current_chunk = overlap_lines + [line]
                    current_length = sum(len(l) + 1 for l in current_chunk)
                    chunk_start_line = i - len(overlap_lines)
                else:
                    current_chunk = [line]
                    current_length = line_length
                    chunk_start_line = i
            else:
                current_chunk.append(line)
                current_length += line_length
        
        # Add final chunk if there's remaining content
        if current_chunk:
            chunk_text = '\n'.join(current_chunk)
            chunks.append(ChunkData(
                content=chunk_text,
                content_hash=self.calculate_content_hash(chunk_text),
                chunk_index=len(chunks),
                start_line=chunk_start_line,
                end_line=len(lines) - 1,
                word_count_estimate=len(chunk_text.split()),
            ))
        
        return chunks
    
    def calculate_content_hash(self, content: str) -> str:
        """Calculate SHA-256 hash of the content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()


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
