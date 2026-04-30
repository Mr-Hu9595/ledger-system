"""File system watcher for automatic document processing"""
import time
from pathlib import Path
from typing import Callable, Optional

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from ledger_system.business.document.parser import DocumentParser


class DocumentHandler(FileSystemEventHandler):
    """Handle file system events for document processing"""

    def __init__(self, callback: Callable[[str], None], supported_extensions: list):
        self.callback = callback
        self.supported_extensions = supported_extensions
        self.cooldown_seconds = 5
        self.last_processed = {}

    def on_created(self, event: FileCreatedEvent):
        """Handle file creation event"""
        if event.is_directory:
            return

        path = Path(event.src_path)
        if path.suffix.lower() not in self.supported_extensions:
            return

        # Cooldown to avoid processing same file multiple times
        current_time = time.time()
        last_time = self.last_processed.get(str(path), 0)
        if current_time - last_time < self.cooldown_seconds:
            return

        self.last_processed[str(path)] = current_time
        self.callback(str(path))


class FileWatcher:
    """Watch folder for new documents"""

    def __init__(self, watch_path: str, callback: Callable[[str], None]):
        self.watch_path = Path(watch_path)
        self.callback = callback
        self.supported_extensions = [
            ".jpg", ".jpeg", ".png", ".bmp",  # Images
            ".pdf",  # PDF
            ".xlsx", ".xls",  # Excel
            ".docx", ".doc",  # Word
            ".txt"  # Text
        ]
        self.observer: Optional[Observer] = None
        self.parser = DocumentParser()

    def start(self):
        """Start watching"""
        self.watch_path.mkdir(parents=True, exist_ok=True)

        event_handler = DocumentHandler(
            callback=self._handle_new_file,
            supported_extensions=self.supported_extensions
        )

        self.observer = Observer()
        self.observer.schedule(event_handler, str(self.watch_path), recursive=False)
        self.observer.start()

        return self

    def stop(self):
        """Stop watching"""
        if self.observer:
            self.observer.stop()
            self.observer.join()

    def _handle_new_file(self, file_path: str):
        """Handle new file detected"""
        try:
            result = self.parser.parse_file(file_path)
            self.callback({
                "file_path": file_path,
                "result": result,
                "status": "success" if "error" not in result else "failed"
            })
        except Exception as e:
            self.callback({
                "file_path": file_path,
                "result": {"error": str(e)},
                "status": "failed"
            })

    def process_existing(self):
        """Process existing files in watch folder"""
        for path in self.watch_path.iterdir():
            if path.is_file() and path.suffix.lower() in self.supported_extensions:
                self._handle_new_file(str(path))