"""
XandAI Utils - Git Utilities
Git integration for code review functionality
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .subprocess_utils import execute_command_safe


class GitUtils:
    """
    Git utilities for XandAI

    Provides functionality to detect changed files, repository root,
    and extract file content for code review.
    """

    @staticmethod
    def is_git_repository(path: str = ".") -> bool:
        """
        Check if current directory is a Git repository

        Args:
            path: Directory path to check (default: current directory)

        Returns:
            bool: True if it's a Git repository
        """
        try:
            result = execute_command_safe("git rev-parse --git-dir", cwd=path, timeout=5)
            return result.returncode == 0
        except Exception:
            return False

    @staticmethod
    def get_repository_root(path: str = ".") -> Optional[str]:
        """
        Get the root directory of the Git repository

        Args:
            path: Directory path to start from (default: current directory)

        Returns:
            str or None: Absolute path to repository root, None if not a Git repo
        """
        try:
            result = execute_command_safe("git rev-parse --show-toplevel", cwd=path, timeout=5)
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except Exception:
            return None

    @staticmethod
    def get_changed_files(
        comparison: str = "HEAD",
        include_untracked: bool = True,
        include_staged: bool = True,
        include_unstaged: bool = True,
        path: str = ".",
    ) -> List[str]:
        """
        Get list of changed files in the repository

        Args:
            comparison: What to compare against (default: "HEAD" for last commit)
            include_untracked: Include untracked files
            include_staged: Include staged changes
            include_unstaged: Include unstaged changes
            path: Repository path

        Returns:
            List[str]: List of changed file paths relative to repo root
        """
        changed_files = []

        if not GitUtils.is_git_repository(path):
            return changed_files

        try:
            # Get staged changes
            if include_staged:
                result = execute_command_safe("git diff --cached --name-only", cwd=path, timeout=10)
                if result.returncode == 0 and result.stdout.strip():
                    changed_files.extend(result.stdout.strip().split("\n"))

            # Get unstaged changes
            if include_unstaged:
                result = execute_command_safe("git diff --name-only", cwd=path, timeout=10)
                if result.returncode == 0 and result.stdout.strip():
                    changed_files.extend(result.stdout.strip().split("\n"))

            # Get untracked files
            if include_untracked:
                result = execute_command_safe(
                    "git ls-files --others --exclude-standard", cwd=path, timeout=10
                )
                if result.returncode == 0 and result.stdout.strip():
                    changed_files.extend(result.stdout.strip().split("\n"))

            # If no changes detected, compare with HEAD
            if not changed_files and comparison:
                result = execute_command_safe(
                    f"git diff --name-only {comparison}", cwd=path, timeout=10
                )
                if result.returncode == 0 and result.stdout.strip():
                    changed_files.extend(result.stdout.strip().split("\n"))

        except Exception:
            pass

        # Remove duplicates and empty strings, filter existing files
        repo_root = GitUtils.get_repository_root(path)
        if repo_root:
            unique_files = []
            for file_path in set(changed_files):
                if file_path and file_path.strip():
                    full_path = os.path.join(repo_root, file_path.strip())
                    if os.path.isfile(full_path):
                        unique_files.append(file_path.strip())
            return unique_files

        return list(set(f for f in changed_files if f and f.strip()))

    @staticmethod
    def get_file_diff(file_path: str, comparison: str = "HEAD", repo_path: str = ".") -> str:
        """
        Get diff for a specific file

        Args:
            file_path: Path to file relative to repo root
            comparison: What to compare against (default: "HEAD")
            repo_path: Repository path

        Returns:
            str: Diff content for the file
        """
        try:
            result = execute_command_safe(
                f"git diff {comparison} -- {file_path}", cwd=repo_path, timeout=15
            )
            if result.returncode == 0:
                return result.stdout
            return ""
        except Exception:
            return ""

    @staticmethod
    def read_file_content(file_path: str, repo_path: str = ".") -> str:
        """
        Read content of a file

        Args:
            file_path: Path to file relative to repo root
            repo_path: Repository path

        Returns:
            str: File content
        """
        try:
            repo_root = GitUtils.get_repository_root(repo_path)
            if repo_root:
                full_path = os.path.join(repo_root, file_path)
                if os.path.isfile(full_path):
                    with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                        return f.read()
            return ""
        except Exception:
            return ""

    @staticmethod
    def get_commit_info(repo_path: str = ".") -> Dict[str, str]:
        """
        Get information about the current commit

        Args:
            repo_path: Repository path

        Returns:
            Dict with commit information
        """
        info = {}

        try:
            # Get current branch
            result = execute_command_safe("git branch --show-current", cwd=repo_path, timeout=5)
            if result.returncode == 0:
                info["branch"] = result.stdout.strip()

            # Get last commit hash
            result = execute_command_safe("git rev-parse HEAD", cwd=repo_path, timeout=5)
            if result.returncode == 0:
                info["commit_hash"] = result.stdout.strip()[:7]  # Short hash

            # Get last commit message
            result = execute_command_safe("git log -1 --pretty=format:%s", cwd=repo_path, timeout=5)
            if result.returncode == 0:
                info["commit_message"] = result.stdout.strip()

            # Get author
            result = execute_command_safe(
                "git log -1 --pretty=format:%an", cwd=repo_path, timeout=5
            )
            if result.returncode == 0:
                info["author"] = result.stdout.strip()

        except Exception:
            pass

        return info

    @staticmethod
    def get_repository_stats(repo_path: str = ".") -> Dict[str, int]:
        """
        Get repository statistics

        Args:
            repo_path: Repository path

        Returns:
            Dict with repository stats
        """
        stats = {}

        try:
            # Count total files tracked
            result = execute_command_safe("git ls-files | wc -l", cwd=repo_path, timeout=10)
            if result.returncode == 0:
                stats["total_files"] = int(result.stdout.strip())

            # Count commits
            result = execute_command_safe("git rev-list --all --count", cwd=repo_path, timeout=10)
            if result.returncode == 0:
                stats["total_commits"] = int(result.stdout.strip())

        except Exception:
            pass

        return stats

    @staticmethod
    def filter_code_files(file_paths: List[str]) -> List[str]:
        """
        Filter list to include only code files

        Args:
            file_paths: List of file paths

        Returns:
            List[str]: Filtered list of code files
        """
        code_extensions = {
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".java",
            ".cpp",
            ".c",
            ".h",
            ".hpp",
            ".cs",
            ".php",
            ".rb",
            ".go",
            ".rs",
            ".swift",
            ".kt",
            ".scala",
            ".r",
            ".sql",
            ".html",
            ".css",
            ".scss",
            ".sass",
            ".less",
            ".vue",
            ".svelte",
            ".json",
            ".yaml",
            ".yml",
            ".xml",
            ".toml",
            ".ini",
            ".cfg",
            ".conf",
            ".sh",
            ".bash",
            ".zsh",
            ".fish",
            ".ps1",
            ".bat",
            ".cmd",
            ".dockerfile",
            ".md",
            ".rst",
            ".txt",
            ".gradle",
            ".maven",
            ".cmake",
            ".makefile",
        }

        code_files = []
        for file_path in file_paths:
            file_ext = Path(file_path).suffix.lower()
            file_name = Path(file_path).name.lower()

            # Check extension
            if file_ext in code_extensions:
                code_files.append(file_path)
            # Check specific filenames
            elif file_name in {
                "makefile",
                "dockerfile",
                "requirements.txt",
                "package.json",
                "composer.json",
                "go.mod",
                "cargo.toml",
            }:
                code_files.append(file_path)

        return code_files

    @staticmethod
    def prepare_review_context(repo_path: str = ".") -> Dict:
        """
        Prepare complete context for code review

        Args:
            repo_path: Repository path

        Returns:
            Dict with complete review context
        """
        context = {
            "is_git_repo": False,
            "repo_root": None,
            "changed_files": [],
            "code_files": [],
            "file_contents": {},
            "file_diffs": {},
            "commit_info": {},
            "repo_stats": {},
            "error": None,
        }

        try:
            # Check if it's a Git repository
            if not GitUtils.is_git_repository(repo_path):
                context["error"] = "Not a Git repository"
                return context

            context["is_git_repo"] = True
            context["repo_root"] = GitUtils.get_repository_root(repo_path)

            # Get changed files
            changed_files = GitUtils.get_changed_files(path=repo_path)
            context["changed_files"] = changed_files

            # Filter code files
            code_files = GitUtils.filter_code_files(changed_files)
            context["code_files"] = code_files

            # Read file contents (limit to reasonable size)
            for file_path in code_files[:20]:  # Limit to 20 files to avoid overwhelming
                content = GitUtils.read_file_content(file_path, repo_path)
                if content and len(content) < 50000:  # Limit to 50KB per file
                    context["file_contents"][file_path] = content

                    # Get diff for the file
                    diff = GitUtils.get_file_diff(file_path, repo_path=repo_path)
                    if diff:
                        context["file_diffs"][file_path] = diff

            # Get commit and repository info
            context["commit_info"] = GitUtils.get_commit_info(repo_path)
            context["repo_stats"] = GitUtils.get_repository_stats(repo_path)

        except Exception as e:
            context["error"] = f"Error preparing context: {str(e)}"

        return context
