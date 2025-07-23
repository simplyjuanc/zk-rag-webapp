import re
import logging
import frontmatter  # type: ignore
from libs.models.pipeline import ParsedContent 
from .metadata_extractor import MetadataExtractor

logger = logging.getLogger(__name__)

class ContentParser:
    """Parses and cleans markdown content."""
    
    def parse_markdown_content(self, content: str, metadata_extractor: MetadataExtractor) -> ParsedContent:
        """Parse markdown content and extract frontmatter and content."""
        try:
            post = frontmatter.loads(content)
            metadata_dict = dict(post.metadata) if post.metadata else {}
            clean_content = post.content
            
        except Exception as e:
            logger.warning(f"Could not parse frontmatter: {e}")
            metadata_dict = {}
            clean_content = content
        
        processed_content = self._clean_content(clean_content)
        
        return ParsedContent(
            metadata=metadata_extractor.extract_normalised_metadata(metadata_dict, processed_content),
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