import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from libs.models.pipeline import FileMetadata, FrontmatterMetadata

LIST_KEYS = {'author', 'category', 'type', 'tags'}


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
        logger.info(f"Metadata: {metadata_dict}")
        normalised_metadata_dict = self.normalize_metadata_dict(metadata_dict)
        return FrontmatterMetadata.model_validate(normalised_metadata_dict)
    

    def normalize_metadata_dict(self, metadata_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize the metadata dictionary."""
        for key, value in metadata_dict.items():
            if value is None:
                continue
            if key in LIST_KEYS:
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

