from pathlib import Path
from typing import Callable, Set
from watchdog.events import FileSystemEventHandler, FileSystemEvent
import logging

from libs.models.pipeline import FileEventType

logger = logging.getLogger(__name__)


class MarkdownFileHandler(FileSystemEventHandler):
    """Handles file system events for markdown files."""

    def __init__(self, callback: Callable[[Path, str], None]):
        self.callback = callback
        self.processed_files: Set[str] = set()

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory and self.__is_markdown_file(event.src_path):
            logger.info(f"New markdown file detected: {event.src_path}")
            self.__process_file(event.src_path, FileEventType.CREATED)

    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory and self.__is_markdown_file(event.src_path):
            logger.info(f"Markdown file modified: {event.src_path}")
            self.__process_file(event.src_path, FileEventType.MODIFIED)

    def on_deleted(self, event: FileSystemEvent) -> None:
        if not event.is_directory and self.__is_markdown_file(event.src_path):
            logger.info(f"Markdown file deleted: {event.src_path}")
            self.__process_file(event.src_path, FileEventType.DELETED)

    def __is_markdown_file(self, file_path: str) -> bool:
        """Check if the file is a markdown file."""
        return file_path.lower().endswith((".md", ".markdown"))

    def __process_file(self, file_path: str, event_type: FileEventType) -> None:
        """Process the file change event."""
        try:
            path = Path(file_path)
            self.callback(path, event_type.value)
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")




