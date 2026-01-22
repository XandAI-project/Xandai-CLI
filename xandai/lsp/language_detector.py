"""
Language Detector Module

Automatically detects programming languages used in a project.
Scans directories and analyzes files to determine active languages.
"""

import os
from collections import Counter
from pathlib import Path
from typing import Dict, List, Set, Tuple

from xandai.lsp.lsp_config import get_server_for_file


class LanguageDetector:
    """Detects programming languages in a project"""

    # File extensions mapped to languages
    EXTENSION_MAP = {
        ".py": "python",
        ".pyi": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".rs": "rust",
        ".go": "go",
        ".java": "java",
        ".cpp": "cpp",
        ".cc": "cpp",
        ".cxx": "cpp",
        ".hpp": "cpp",
        ".c": "c",
        ".h": "c",
        ".rb": "ruby",
        ".php": "php",
        ".html": "html",
        ".htm": "html",
        ".css": "css",
        ".scss": "css",
        ".sass": "css",
        ".less": "css",
        ".json": "json",
        ".cs": "csharp",
        ".swift": "swift",
        ".kt": "kotlin",
        ".scala": "scala",
        ".lua": "lua",
        ".sh": "shell",
        ".bash": "shell",
        ".zsh": "shell",
    }

    # Directories to ignore during scanning
    IGNORE_DIRS = {
        "__pycache__",
        "node_modules",
        ".git",
        ".svn",
        "venv",
        "env",
        "dist",
        "build",
        "target",
        ".pytest_cache",
        ".mypy_cache",
        "coverage",
        ".coverage",
        "htmlcov",
        ".tox",
        ".eggs",
        "bower_components",
        "vendor",
    }

    def __init__(self, root_path: str = None, max_depth: int = 5):
        """
        Initialize the language detector

        Args:
            root_path: Root directory to scan (defaults to current directory)
            max_depth: Maximum directory depth to scan
        """
        self.root_path = Path(root_path) if root_path else Path.cwd()
        self.max_depth = max_depth
        self._language_cache: Dict[str, int] = {}
        self._file_cache: Dict[str, List[str]] = {}

    def detect_languages(self, min_files: int = 1) -> Dict[str, int]:
        """
        Detect all programming languages in the project

        Args:
            min_files: Minimum number of files required to consider a language

        Returns:
            Dictionary mapping language names to file counts
        """
        if self._language_cache:
            return self._language_cache

        language_counts = Counter()

        for file_path in self._scan_directory(self.root_path):
            ext = file_path.suffix.lower()
            language = self.EXTENSION_MAP.get(ext)

            if language:
                language_counts[language] += 1

                # Cache files by language
                if language not in self._file_cache:
                    self._file_cache[language] = []
                self._file_cache[language].append(str(file_path))

        # Filter by minimum file count
        self._language_cache = {
            lang: count for lang, count in language_counts.items() if count >= min_files
        }

        return self._language_cache

    def get_primary_language(self) -> str:
        """Get the primary/dominant language in the project"""
        languages = self.detect_languages()

        if not languages:
            return "unknown"

        # Return language with most files
        return max(languages.items(), key=lambda x: x[1])[0]

    def get_language_files(self, language: str) -> List[str]:
        """Get all files for a specific language"""
        if not self._language_cache:
            self.detect_languages()

        return self._file_cache.get(language, [])

    def get_file_language(self, file_path: str) -> str:
        """Detect language for a specific file"""
        ext = Path(file_path).suffix.lower()
        return self.EXTENSION_MAP.get(ext, "unknown")

    def detect_project_type(self) -> str:
        """
        Detect project type based on configuration files

        Returns:
            Project type (e.g., 'python-package', 'nodejs', 'rust-crate')
        """
        indicators = {
            "python-package": ["setup.py", "pyproject.toml", "setup.cfg"],
            "nodejs": ["package.json", "package-lock.json"],
            "rust-crate": ["Cargo.toml"],
            "go-module": ["go.mod"],
            "java-maven": ["pom.xml"],
            "java-gradle": ["build.gradle", "build.gradle.kts"],
            "ruby-gem": ["Gemfile", ".gemspec"],
            "php-composer": ["composer.json"],
        }

        root_files = {f.name for f in self.root_path.iterdir() if f.is_file()}

        for project_type, files in indicators.items():
            if any(f in root_files for f in files):
                return project_type

        # Fallback to primary language
        primary = self.get_primary_language()
        return f"{primary}-project" if primary != "unknown" else "unknown"

    def get_lsp_requirements(self) -> List[Tuple[str, str]]:
        """
        Get list of LSP servers needed for detected languages

        Returns:
            List of tuples (language, server_name)
        """
        languages = self.detect_languages()
        requirements = []

        for language in languages.keys():
            server = get_server_for_file(f"dummy.{self._get_extension(language)}")
            if server:
                requirements.append((language, server.name))

        return requirements

    def get_statistics(self) -> Dict:
        """Get detailed statistics about project languages"""
        languages = self.detect_languages()
        total_files = sum(languages.values())

        stats = {
            "total_files": total_files,
            "language_count": len(languages),
            "primary_language": self.get_primary_language(),
            "project_type": self.detect_project_type(),
            "languages": {},
        }

        for lang, count in sorted(languages.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_files * 100) if total_files > 0 else 0
            stats["languages"][lang] = {
                "files": count,
                "percentage": round(percentage, 2),
            }

        return stats

    def _scan_directory(self, directory: Path, depth: int = 0) -> List[Path]:
        """
        Recursively scan directory for source files

        Args:
            directory: Directory to scan
            depth: Current recursion depth

        Returns:
            List of file paths
        """
        if depth > self.max_depth:
            return []

        files = []

        try:
            for item in directory.iterdir():
                # Skip hidden files and ignored directories
                if item.name.startswith(".") or item.name in self.IGNORE_DIRS:
                    continue

                if item.is_file():
                    # Check if it's a source code file
                    if item.suffix.lower() in self.EXTENSION_MAP:
                        files.append(item)

                elif item.is_dir():
                    # Recursively scan subdirectory
                    files.extend(self._scan_directory(item, depth + 1))

        except (PermissionError, OSError):
            # Skip directories we can't access
            pass

        return files

    def _get_extension(self, language: str) -> str:
        """Get typical file extension for a language"""
        ext_map = {
            "python": "py",
            "javascript": "js",
            "typescript": "ts",
            "rust": "rs",
            "go": "go",
            "java": "java",
            "cpp": "cpp",
            "c": "c",
            "ruby": "rb",
            "php": "php",
            "html": "html",
            "css": "css",
            "json": "json",
        }
        return ext_map.get(language, language)

    def clear_cache(self):
        """Clear internal caches"""
        self._language_cache.clear()
        self._file_cache.clear()
