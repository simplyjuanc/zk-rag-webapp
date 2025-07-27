import re
import logging
import frontmatter  # type: ignore

from libs.models.documents import ParsedContent
from .metadata_extractor import MetadataValidator

logger = logging.getLogger(__name__)


class MarkdownParser:
    """Parses and cleans markdown content."""

    @staticmethod
    def parse_content(
        content: str, metadata_validator: MetadataValidator
    ) -> ParsedContent:
        """Parse markdown content and extract frontmatter and content."""
        try:
            post = frontmatter.loads(content)
            metadata = dict(post.metadata) if post.metadata else {}
            clean_content = post.content

        except Exception as e:
            logger.warning(f"Could not parse frontmatter: {e}")
            metadata = {}
            clean_content = content

        processed_content = MarkdownParser.clean_content(clean_content)

        return ParsedContent(
            metadata=metadata_validator.validate_metadata(metadata, processed_content),
            content=processed_content,
        )

    @staticmethod
    def clean_content(content: str) -> str:
        # Remove excessive whitespace
        content = re.sub(r"\n\s*\n\s*\n", "\n\n", content)

        # Normalize line endings
        content = content.replace("\r\n", "\n").replace("\r", "\n")

        return content.strip()
