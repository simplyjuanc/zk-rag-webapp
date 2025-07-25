from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Set
from watchdog.observers import Observer
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


class FileWatcher:
    """Watches a directory for markdown file changes."""

    def __init__(self, watch_directory: str) -> None:
        self.watch_directory = Path(watch_directory)
        self.observer = Observer()
        self.handler: MarkdownFileHandler | None = None
        self.is_running = False

    def start(self, callback: Callable[[Path, FileEventType], None]) -> None:
        """Start watching the directory for changes."""
        if self.is_running:
            logger.warning("File watcher is already running")
            return

        if not self.watch_directory.exists():
            raise ValueError(f"Watch directory does not exist: {self.watch_directory}")

        self.handler = MarkdownFileHandler(
            lambda file_path, event_type: callback(
                Path(file_path), FileEventType(event_type)
            )
        )
        self.observer.schedule(self.handler, str(self.watch_directory), recursive=True)

        self.observer.start()
        self.is_running = True
        logger.info(f"Started watching directory: {self.watch_directory}")

    def stop(self) -> None:
        """Stop watching the directory."""
        if not self.is_running:
            return

        self.observer.stop()
        self.observer.join()
        self.is_running = False
        logger.info("Stopped file watcher")

    def scan_existing_files(
        self, callback: Callable[[Path, FileEventType], None]
    ) -> None:
        """Scan for existing Markdown files in the directory."""
        logger.info(f"Scanning for existing markdown files in: {self.watch_directory}")

        md_files = self.watch_directory.rglob("*.md")
        markdown_files = self.watch_directory.rglob("*.markdown")
        for file_path in list(md_files) + list(markdown_files):
            if file_path.is_file():
                logger.info(f"Found existing markdown file: {file_path}")
                callback(file_path, FileEventType.EXISTING)
