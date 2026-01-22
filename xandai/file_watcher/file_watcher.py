"""
File Watcher

Monitors file system changes with callbacks.
"""

import os
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set


class EventType(Enum):
    """File system event types"""

    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"


@dataclass
class FileEvent:
    """File system event"""

    event_type: EventType
    path: str
    timestamp: str
    is_directory: bool = False
    old_path: Optional[str] = None  # For MOVED events


class FileWatcher:
    """
    File Watcher

    Monitors directories for file changes and triggers callbacks.
    """

    def __init__(self, polling_interval: float = 1.0):
        """
        Initialize file watcher

        Args:
            polling_interval: Seconds between polling checks
        """
        self.polling_interval = polling_interval
        self.watched_paths: Dict[str, Set[str]] = {}  # path -> set of file paths
        self.file_mtimes: Dict[str, float] = {}  # file path -> modification time
        self.callbacks: Dict[EventType, List[Callable]] = {
            EventType.CREATED: [],
            EventType.MODIFIED: [],
            EventType.DELETED: [],
            EventType.MOVED: [],
        }
        self.running = False
        self.thread: Optional[threading.Thread] = None

    def watch(self, path: str, recursive: bool = True):
        """
        Start watching a path

        Args:
            path: Path to watch
            recursive: Watch subdirectories
        """
        path = os.path.abspath(path)

        if path not in self.watched_paths:
            self.watched_paths[path] = set()
            self._scan_directory(path, recursive)

    def unwatch(self, path: str):
        """
        Stop watching a path

        Args:
            path: Path to unwatch
        """
        path = os.path.abspath(path)

        if path in self.watched_paths:
            # Remove file mtimes for this path
            for file_path in self.watched_paths[path]:
                if file_path in self.file_mtimes:
                    del self.file_mtimes[file_path]

            del self.watched_paths[path]

    def on(self, event_type: EventType, callback: Callable[[FileEvent], None]):
        """
        Register a callback for an event type

        Args:
            event_type: Event type to listen for
            callback: Callback function
        """
        self.callbacks[event_type].append(callback)

    def start(self):
        """Start watching in background thread"""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop watching"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
            self.thread = None

    def _watch_loop(self):
        """Main watch loop"""
        while self.running:
            self._check_changes()
            time.sleep(self.polling_interval)

    def _check_changes(self):
        """Check for file changes"""
        for watch_path in list(self.watched_paths.keys()):
            if not os.path.exists(watch_path):
                continue

            current_files = set()

            # Scan directory
            for root, dirs, files in os.walk(watch_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    current_files.add(file_path)

                    # Check if file is new
                    if file_path not in self.file_mtimes:
                        self._trigger_event(
                            FileEvent(
                                event_type=EventType.CREATED,
                                path=file_path,
                                timestamp=datetime.now().isoformat(),
                                is_directory=False,
                            )
                        )
                        self.file_mtimes[file_path] = os.path.getmtime(file_path)
                    else:
                        # Check if file was modified
                        current_mtime = os.path.getmtime(file_path)
                        if current_mtime > self.file_mtimes[file_path]:
                            self._trigger_event(
                                FileEvent(
                                    event_type=EventType.MODIFIED,
                                    path=file_path,
                                    timestamp=datetime.now().isoformat(),
                                    is_directory=False,
                                )
                            )
                            self.file_mtimes[file_path] = current_mtime

            # Check for deleted files
            watched_files = self.watched_paths[watch_path]
            deleted_files = watched_files - current_files

            for file_path in deleted_files:
                self._trigger_event(
                    FileEvent(
                        event_type=EventType.DELETED,
                        path=file_path,
                        timestamp=datetime.now().isoformat(),
                        is_directory=False,
                    )
                )
                if file_path in self.file_mtimes:
                    del self.file_mtimes[file_path]

            # Update watched files
            self.watched_paths[watch_path] = current_files

    def _scan_directory(self, path: str, recursive: bool):
        """Initial directory scan"""
        if not os.path.exists(path):
            return

        if os.path.isfile(path):
            self.watched_paths.setdefault(os.path.dirname(path), set()).add(path)
            self.file_mtimes[path] = os.path.getmtime(path)
            return

        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                self.watched_paths.setdefault(path, set()).add(file_path)
                self.file_mtimes[file_path] = os.path.getmtime(file_path)

            if not recursive:
                break

    def _trigger_event(self, event: FileEvent):
        """Trigger callbacks for an event"""
        for callback in self.callbacks[event.event_type]:
            try:
                callback(event)
            except Exception:
                pass  # Don't let callback errors break watching
