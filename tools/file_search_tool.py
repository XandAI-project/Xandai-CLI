"""
File Search Tool - Search for files in the file system
"""

import os
from pathlib import Path
from typing import List


class FileSearchTool:
    """Search for files in the file system."""

    @staticmethod
    def get_name():
        """Return the tool's name."""
        return "file_search_tool"

    @staticmethod
    def get_description():
        """Return description of what the tool does."""
        return "Search for files by name pattern in a directory (supports wildcards)"

    @staticmethod
    def get_parameters():
        """Return the parameters this tool accepts."""
        return {
            "pattern": "string (required) - File name pattern to search for (e.g., '*.py', 'test*.txt')",
            "directory": "string (optional) - Directory to search in (default: current directory)",
            "recursive": "boolean (optional) - Search subdirectories recursively (default: true)",
        }

    def execute(self, pattern: str, directory: str = ".", recursive: bool = True):
        """
        Execute the file search.

        Args:
            pattern: File name pattern to search for
            directory: Directory to search in
            recursive: Whether to search recursively

        Returns:
            Dictionary with search results
        """
        try:
            search_path = Path(directory).resolve()

            if not search_path.exists():
                return {
                    "success": False,
                    "error": f"Directory does not exist: {directory}",
                }

            if not search_path.is_dir():
                return {
                    "success": False,
                    "error": f"Path is not a directory: {directory}",
                }

            # Search for files
            matches = []
            if recursive:
                matches = list(search_path.rglob(pattern))
            else:
                matches = list(search_path.glob(pattern))

            # Filter to only files
            file_matches = [f for f in matches if f.is_file()]

            # Prepare results
            results = []
            for file_path in file_matches[:100]:  # Limit to 100 results
                try:
                    stat = file_path.stat()
                    results.append(
                        {
                            "name": file_path.name,
                            "path": str(file_path.relative_to(search_path)),
                            "full_path": str(file_path),
                            "size_bytes": stat.st_size,
                            "size_readable": self._format_size(stat.st_size),
                        }
                    )
                except Exception:
                    # Skip files we can't access
                    continue

            return {
                "success": True,
                "pattern": pattern,
                "directory": str(search_path),
                "recursive": recursive,
                "total_matches": len(file_matches),
                "results_shown": len(results),
                "files": results,
            }

        except Exception as e:
            return {
                "success": False,
                "pattern": pattern,
                "directory": directory,
                "error": f"Search error: {str(e)}",
            }

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
