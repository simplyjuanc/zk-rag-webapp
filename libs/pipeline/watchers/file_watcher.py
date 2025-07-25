from libs.models.pipeline import FileEventType
from libs.pipeline.watchers.source_watcher import SourceWatcher
from libs.pipeline.markdown_file_handler import MarkdownFileHandler, logger


from watchdog.observers import Observer


from pathlib import Path
from typing import Callable


class FileWatcher(SourceWatcher):
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