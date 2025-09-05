"""
XandAI Utils - Operating System Utilities
Cross-platform OS detection and command mapping for file operations
"""

import os
import platform
from typing import Dict, List


class OSUtils:
    """
    Cross-platform operating system utilities

    Handles OS detection and provides appropriate commands for different platforms.
    """

    @staticmethod
    def get_platform() -> str:
        """
        Get current platform

        Returns:
            str: 'windows', 'linux', 'darwin' (macOS), or 'unknown'
        """
        system = platform.system().lower()
        if system == "windows":
            return "windows"
        elif system == "linux":
            return "linux"
        elif system == "darwin":
            return "darwin"  # macOS
        else:
            return "unknown"

    @staticmethod
    def is_windows() -> bool:
        """Check if running on Windows"""
        return OSUtils.get_platform() == "windows"

    @staticmethod
    def is_unix_like() -> bool:
        """Check if running on Unix-like system (Linux/macOS)"""
        return OSUtils.get_platform() in ["linux", "darwin"]

    @staticmethod
    def get_file_read_command(filepath: str) -> str:
        """
        Get platform-appropriate command to read a file

        Args:
            filepath: Path to file to read

        Returns:
            str: Complete command to read the file
        """
        if OSUtils.is_windows():
            return f'type "{filepath}"'
        else:
            return f'cat "{filepath}"'

    @staticmethod
    def get_file_head_command(filepath: str, lines: int = 10) -> str:
        """
        Get platform-appropriate command to read first N lines of a file

        Args:
            filepath: Path to file to read
            lines: Number of lines to read (default: 10)

        Returns:
            str: Complete command to read first N lines
        """
        if OSUtils.is_windows():
            # Windows doesn't have head, but we can simulate it with PowerShell
            return f"powershell \"Get-Content '{filepath}' -Head {lines}\""
        else:
            return f'head -{lines} "{filepath}"'

    @staticmethod
    def get_file_tail_command(filepath: str, lines: int = 10) -> str:
        """
        Get platform-appropriate command to read last N lines of a file

        Args:
            filepath: Path to file to read
            lines: Number of lines to read (default: 10)

        Returns:
            str: Complete command to read last N lines
        """
        if OSUtils.is_windows():
            # Windows doesn't have tail, but we can simulate it with PowerShell
            return f"powershell \"Get-Content '{filepath}' -Tail {lines}\""
        else:
            return f'tail -{lines} "{filepath}"'

    @staticmethod
    def get_directory_list_command(dirpath: str = ".") -> str:
        """
        Get platform-appropriate command to list directory contents

        Args:
            dirpath: Directory path (default: current directory)

        Returns:
            str: Complete command to list directory
        """
        if OSUtils.is_windows():
            return f'dir "{dirpath}"'
        else:
            return f'ls -la "{dirpath}"'

    @staticmethod
    def get_file_search_command(pattern: str, filepath: str = ".") -> str:
        """
        Get platform-appropriate command to search within files

        Args:
            pattern: Search pattern
            filepath: File or directory to search in

        Returns:
            str: Complete command to search for pattern
        """
        if OSUtils.is_windows():
            return f'findstr /n "{pattern}" "{filepath}"'
        else:
            return f'grep -n "{pattern}" "{filepath}"'

    @staticmethod
    def get_available_commands() -> Dict[str, str]:
        """
        Get all available file operation commands for current platform

        Returns:
            Dict mapping command type to actual command template
        """
        return {
            "read_file": OSUtils.get_file_read_command("{filepath}"),
            "head_file": OSUtils.get_file_head_command("{filepath}", 10),
            "tail_file": OSUtils.get_file_tail_command("{filepath}", 10),
            "list_dir": OSUtils.get_directory_list_command("{dirpath}"),
            "search_file": OSUtils.get_file_search_command("{pattern}", "{filepath}"),
        }

    @staticmethod
    def debug_print(message: str, enabled: bool = True):
        """
        Platform-aware debug printing

        Args:
            message: Debug message to print
            enabled: Whether debug is enabled
        """
        if enabled:
            # Use print to ensure visibility across all platforms
            print(f"[DEBUG] {message}")
            # Also try to flush output for immediate visibility
            import sys

            sys.stdout.flush()
