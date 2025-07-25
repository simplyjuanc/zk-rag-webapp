from libs.models.pipeline import FileEventType


from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable


class SourceWatcher(ABC):
    @abstractmethod
    def start(self, callback: Callable[[Path, FileEventType], None]) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass

    @abstractmethod
    def scan_existing_files(
        self, callback: Callable[[Path, FileEventType], None]
    ) -> None:
        pass