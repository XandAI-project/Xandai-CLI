"""
Code Counter Tool - Count lines of code in files and directories
"""

from collections import defaultdict
from pathlib import Path


class CodeCounterTool:
    """Count lines of code, comments, and blank lines in source files."""

    # File extensions for different languages
    LANGUAGE_EXTENSIONS = {
        "Python": [".py", ".pyw"],
        "JavaScript": [".js", ".jsx", ".mjs"],
        "TypeScript": [".ts", ".tsx"],
        "Java": [".java"],
        "C": [".c", ".h"],
        "C++": [".cpp", ".hpp", ".cc", ".hh", ".cxx"],
        "C#": [".cs"],
        "Go": [".go"],
        "Rust": [".rs"],
        "Ruby": [".rb"],
        "PHP": [".php"],
        "Swift": [".swift"],
        "Kotlin": [".kt", ".kts"],
        "HTML": [".html", ".htm"],
        "CSS": [".css", ".scss", ".sass", ".less"],
        "Shell": [".sh", ".bash"],
        "SQL": [".sql"],
        "Markdown": [".md", ".markdown"],
        "JSON": [".json"],
        "YAML": [".yaml", ".yml"],
        "XML": [".xml"],
    }

    @staticmethod
    def get_name():
        """Return the tool's name."""
        return "code_counter_tool"

    @staticmethod
    def get_description():
        """Return description of what the tool does."""
        return "Count lines of code, comments, and blank lines in source files"

    @staticmethod
    def get_parameters():
        """Return the parameters this tool accepts."""
        return {
            "path": "string (required) - File or directory path to analyze",
            "recursive": "boolean (optional) - Search subdirectories recursively (default: true)",
        }

    def execute(self, path: str, recursive: bool = True):
        """
        Execute the code counting.

        Args:
            path: File or directory path to analyze
            recursive: Whether to search recursively

        Returns:
            Dictionary with code counting results
        """
        try:
            target_path = Path(path).resolve()

            if not target_path.exists():
                return {
                    "success": False,
                    "error": f"Path does not exist: {path}",
                }

            # Collect files
            if target_path.is_file():
                files = [target_path]
            else:
                # Find all source files
                if recursive:
                    files = [f for f in target_path.rglob("*") if f.is_file()]
                else:
                    files = [f for f in target_path.glob("*") if f.is_file()]

            # Filter to known source files
            source_files = []
            for file_path in files:
                ext = file_path.suffix.lower()
                for lang, exts in self.LANGUAGE_EXTENSIONS.items():
                    if ext in exts:
                        source_files.append((file_path, lang))
                        break

            if not source_files:
                return {
                    "success": False,
                    "error": "No source code files found in the specified path",
                }

            # Count lines
            stats_by_language = defaultdict(
                lambda: {
                    "files": 0,
                    "code_lines": 0,
                    "comment_lines": 0,
                    "blank_lines": 0,
                    "total_lines": 0,
                }
            )

            all_files_stats = []

            for file_path, language in source_files:
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()

                    code = 0
                    comments = 0
                    blank = 0

                    for line in lines:
                        stripped = line.strip()
                        if not stripped:
                            blank += 1
                        elif self._is_comment_line(stripped, language):
                            comments += 1
                        else:
                            code += 1

                    total = len(lines)

                    # Update language stats
                    stats_by_language[language]["files"] += 1
                    stats_by_language[language]["code_lines"] += code
                    stats_by_language[language]["comment_lines"] += comments
                    stats_by_language[language]["blank_lines"] += blank
                    stats_by_language[language]["total_lines"] += total

                    # Store file stats
                    all_files_stats.append(
                        {
                            "file": (
                                str(file_path.relative_to(target_path))
                                if target_path.is_dir()
                                else file_path.name
                            ),
                            "language": language,
                            "code_lines": code,
                            "comment_lines": comments,
                            "blank_lines": blank,
                            "total_lines": total,
                        }
                    )

                except Exception:
                    # Skip files we can't read
                    continue

            # Calculate totals
            totals = {
                "files": sum(s["files"] for s in stats_by_language.values()),
                "code_lines": sum(s["code_lines"] for s in stats_by_language.values()),
                "comment_lines": sum(s["comment_lines"] for s in stats_by_language.values()),
                "blank_lines": sum(s["blank_lines"] for s in stats_by_language.values()),
                "total_lines": sum(s["total_lines"] for s in stats_by_language.values()),
            }

            # Sort files by code lines
            all_files_stats.sort(key=lambda x: x["code_lines"], reverse=True)

            return {
                "success": True,
                "path": str(target_path),
                "recursive": recursive,
                "totals": totals,
                "by_language": dict(stats_by_language),
                "top_files": all_files_stats[:10],  # Top 10 largest files
                "total_files_analyzed": len(all_files_stats),
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Code counting error: {str(e)}",
            }

    @staticmethod
    def _is_comment_line(line: str, language: str) -> bool:
        """Check if a line is a comment."""
        # Single line comments
        single_line_markers = {
            "Python": "#",
            "JavaScript": "//",
            "TypeScript": "//",
            "Java": "//",
            "C": "//",
            "C++": "//",
            "C#": "//",
            "Go": "//",
            "Rust": "//",
            "PHP": "//",
            "Swift": "//",
            "Kotlin": "//",
            "Shell": "#",
            "Ruby": "#",
            "SQL": "--",
            "HTML": "<!--",
            "CSS": "/*",
        }

        marker = single_line_markers.get(language)
        if marker and line.startswith(marker):
            return True

        # Multi-line comment markers (simplified check)
        if line.startswith("/*") or line.startswith("*/") or line.startswith("*"):
            return True
        if line.startswith('"""') or line.startswith("'''"):  # Python docstrings
            return True

        return False
