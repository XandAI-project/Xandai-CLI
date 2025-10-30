"""
Delete Tool - Delete files or folders safely
"""

import os
import platform
import subprocess
from pathlib import Path


class DeleteTool:
    """Delete files or folders with confirmation."""

    @staticmethod
    def get_name():
        """Return the tool's name."""
        return "delete_tool"

    @staticmethod
    def get_description():
        """Return description of what the tool does."""
        return "Delete files or folders (provides commands for safe deletion)"

    @staticmethod
    def get_parameters():
        """Return the parameters this tool accepts."""
        return {
            "target": "string (required) - File or folder name to delete",
            "force": "boolean (optional) - Force deletion without confirmation (default: false)",
        }

    def execute(self, target: str, force: bool = False):
        """
        Execute the delete operation.

        Args:
            target: File or folder to delete
            force: Whether to force deletion without confirmation

        Returns:
            Dictionary with directory listing and delete command
        """
        try:
            # Get current directory
            current_dir = Path.cwd()
            target_path = current_dir / target

            # Check if target exists
            if not target_path.exists():
                return {
                    "success": False,
                    "error": f"File or folder '{target}' not found in current directory",
                    "current_directory": str(current_dir),
                    "suggestion": "Run 'dir' or 'ls' to see available files",
                }

            # Get directory listing
            dir_output = self._get_directory_listing()

            # Get file/folder info
            is_file = target_path.is_file()
            is_dir = target_path.is_dir()

            item_type = "file" if is_file else "folder"

            # Get size info
            size_info = ""
            if is_file:
                size = target_path.stat().st_size
                size_info = self._format_size(size)
            elif is_dir:
                # Count items in directory
                try:
                    items = list(target_path.iterdir())
                    size_info = f"{len(items)} item(s)"
                except:
                    size_info = "unknown items"

            # Determine OS and appropriate delete command
            is_windows = platform.system().lower() == "windows"

            # Only use quotes if filename has spaces
            needs_quotes = " " in target
            quoted_target = f'"{target}"' if needs_quotes else target

            if is_windows:
                if is_file:
                    delete_cmd = f"del {quoted_target}"
                    delete_cmd_force = f"del /f /q {quoted_target}"
                else:
                    delete_cmd = f"rmdir {quoted_target}"
                    delete_cmd_force = f"rmdir /s /q {quoted_target}"
            else:
                if is_file:
                    delete_cmd = f"rm {quoted_target}"
                    delete_cmd_force = f"rm -f {quoted_target}"
                else:
                    delete_cmd = f"rm -r {quoted_target}"
                    delete_cmd_force = f"rm -rf {quoted_target}"

            # Build LLM-friendly context
            llm_context = f""" Current Directory: {current_dir}

 Directory Listing:
{dir_output}

 Target: {target}
   Type: {item_type.upper()}
   Size: {size_info}
   Exists:  Yes

  CRITICAL: The user wants to DELETE this {item_type}.

 EXECUTE THIS COMMAND TO DELETE:

<commands>{delete_cmd_force if force else delete_cmd}</commands>

 Command will:
   - Delete: {target} ({item_type})
   - Location: {current_dir}
   {'- Force mode: YES (no confirmation)' if force else '- May ask for confirmation (S/N or Y/N)'}

 After execution, run <commands>dir</commands> to verify deletion."""

            return {
                "success": True,
                "target": target,
                "type": item_type,
                "exists": True,
                "size": size_info,
                "force": force,
                "delete_command": delete_cmd_force if force else delete_cmd,
                "current_directory": str(current_dir),
                "directory_listing": dir_output,
                "llm_context": llm_context,
            }

        except Exception as e:
            return {
                "success": False,
                "target": target,
                "error": f"Error preparing delete operation: {str(e)}",
            }

    @staticmethod
    def _get_directory_listing():
        """Get current directory listing."""
        try:
            is_windows = platform.system().lower() == "windows"
            cmd = "dir" if is_windows else "ls -lah"

            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            return result.stdout.strip() if result.stdout else "Unable to list directory"
        except:
            return "Unable to list directory"

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
