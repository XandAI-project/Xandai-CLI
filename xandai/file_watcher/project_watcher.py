"""
Project Watcher

Watches project directories with smart filtering.
"""

import os
from pathlib import Path
from typing import List, Optional, Set

from xandai.file_watcher.file_watcher import EventType, FileEvent, FileWatcher


class ProjectWatcher:
    """
    Project Watcher

    Watches project directories with gitignore-style filtering.
    """

    # Common patterns to ignore
    DEFAULT_IGNORE_PATTERNS = [
        "__pycache__",
        "*.pyc",
        ".git",
        ".gitignore",
        "node_modules",
        ".venv",
        "venv",
        ".env",
        "*.log",
        ".DS_Store",
        "Thumbs.db",
        "*.swp",
        "*.swo",
        ".pytest_cache",
        ".coverage",
        "htmlcov",
        "dist",
        "build",
        "*.egg-info",
    ]

    def __init__(self, project_path: str, ignore_patterns: Optional[List[str]] = None):
        """
        Initialize project watcher

        Args:
            project_path: Project root directory
            ignore_patterns: Additional patterns to ignore
        """
        self.project_path = os.path.abspath(project_path)
        self.ignore_patterns = set(self.DEFAULT_IGNORE_PATTERNS)

        if ignore_patterns:
            self.ignore_patterns.update(ignore_patterns)

        self.watcher = FileWatcher()
        self._load_gitignore()

    def watch(self):
        """Start watching project"""
        self.watcher.watch(self.project_path, recursive=True)

    def start(self):
        """Start watching in background"""
        self.watch()
        self.watcher.start()

    def stop(self):
        """Stop watching"""
        self.watcher.stop()

    def on_change(self, callback):
        """Register callback for file changes"""

        def filtered_callback(event: FileEvent):
            if not self._should_ignore(event.path):
                callback(event)

        self.watcher.on(EventType.CREATED, filtered_callback)
        self.watcher.on(EventType.MODIFIED, filtered_callback)
        self.watcher.on(EventType.DELETED, filtered_callback)

    def on_created(self, callback):
        """Register callback for file creation"""

        def filtered_callback(event: FileEvent):
            if not self._should_ignore(event.path):
                callback(event)

        self.watcher.on(EventType.CREATED, filtered_callback)

    def on_modified(self, callback):
        """Register callback for file modification"""

        def filtered_callback(event: FileEvent):
            if not self._should_ignore(event.path):
                callback(event)

        self.watcher.on(EventType.MODIFIED, filtered_callback)

    def on_deleted(self, callback):
        """Register callback for file deletion"""

        def filtered_callback(event: FileEvent):
            if not self._should_ignore(event.path):
                callback(event)

        self.watcher.on(EventType.DELETED, filtered_callback)

    def _should_ignore(self, file_path: str) -> bool:
        """Check if file should be ignored"""
        rel_path = os.path.relpath(file_path, self.project_path)

        # Check each pattern
        for pattern in self.ignore_patterns:
            if pattern.startswith("*"):
                # Wildcard pattern
                if rel_path.endswith(pattern[1:]):
                    return True
            elif pattern in rel_path:
                # Contains pattern
                return True

        return False

    def _load_gitignore(self):
        """Load patterns from .gitignore if present"""
        gitignore_path = os.path.join(self.project_path, ".gitignore")

        if os.path.exists(gitignore_path):
            try:
                with open(gitignore_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            self.ignore_patterns.add(line)
            except:
                pass

    def get_watched_files(self) -> List[str]:
        """Get list of currently watched files"""
        all_files = []

        for root, dirs, files in os.walk(self.project_path):
            for file in files:
                file_path = os.path.join(root, file)
                if not self._should_ignore(file_path):
                    all_files.append(file_path)

        return all_files
