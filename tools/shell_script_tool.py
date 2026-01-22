#!/usr/bin/env python3
"""
Shell Script Tool for XandAI
Executes complex shell tasks like finding large files, searching strings, etc.
"""

import os
import platform
from pathlib import Path


class ShellScriptTool:
    """
    Tool for executing complex shell script tasks.

    Use cases:
    - Find largest files in directory
    - Search for strings in files/folders
    - Analyze disk usage
    - Find files by pattern
    - And other shell-based operations
    """

    def get_name(self) -> str:
        """Return tool name"""
        return "shell_script_tool"

    def get_description(self) -> str:
        """Return tool description"""
        return """Execute complex shell script tasks like:
- Find largest files (e.g., "list 50 biggest files")
- Search for strings in folders (e.g., "search for 'anthropic' in this folder")
- Analyze disk usage
- Find files by pattern or extension
- Count lines of code
- And other shell-based operations

This tool automatically adapts commands for Windows/Linux/macOS."""

    def get_parameters(self) -> dict:
        """Return parameter schema"""
        return {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "Description of the shell task to perform (e.g., 'list 50 biggest files', 'search for anthropic in this folder')",
                },
                "target_path": {
                    "type": "string",
                    "description": "Optional: Target path for the operation (defaults to current directory)",
                },
                "search_string": {
                    "type": "string",
                    "description": "Optional: String to search for (used in search tasks)",
                },
                "file_pattern": {
                    "type": "string",
                    "description": "Optional: File pattern to match (e.g., '*.py', '*.txt')",
                },
            },
            "required": ["task"],
        }

    def execute(
        self, task: str, target_path: str = ".", search_string: str = "", file_pattern: str = "*"
    ) -> dict:
        """
        Execute shell script task

        Args:
            task: Description of the task
            target_path: Path to operate on (default: current directory)
            search_string: String to search for
            file_pattern: File pattern to match

        Returns:
            dict with command wrapped in <commands> tags for LLM execution
        """
        try:
            # Get OS type
            os_type = platform.system().lower()
            is_windows = os_type == "windows"

            # Normalize path
            if target_path == ".":
                target_path = os.getcwd()
            else:
                target_path = os.path.abspath(target_path)

            # Check if path exists
            if not os.path.exists(target_path):
                return {
                    "success": False,
                    "error": f"Path not found: {target_path}",
                    "message": f"❌ The path '{target_path}' does not exist.",
                }

            # Task detection and command generation
            task_lower = task.lower()
            command = None
            description = ""

            # Task 1: Find largest files
            if any(
                keyword in task_lower
                for keyword in ["largest", "biggest", "large files", "big files", "file size"]
            ):
                limit = self._extract_number(task_lower, default=50)
                description = f"Finding the {limit} largest files in {target_path}"

                if is_windows:
                    # Windows PowerShell command
                    command = f'Get-ChildItem -Path "{target_path}" -Recurse -File -ErrorAction SilentlyContinue | Sort-Object Length -Descending | Select-Object -First {limit} FullName, @{{Name="Size(MB)";Expression={{[math]::Round($_.Length/1MB,2)}}}} | Format-Table -AutoSize'
                else:
                    # Linux/macOS command
                    command = f'find "{target_path}" -type f -exec du -h {{}} + 2>/dev/null | sort -rh | head -n {limit}'

            # Task 2: Search for string in files
            elif any(
                keyword in task_lower for keyword in ["search", "find string", "contains", "grep"]
            ):
                if not search_string:
                    # Try to extract from task description
                    search_string = self._extract_search_string(task)

                if not search_string:
                    return {
                        "success": False,
                        "error": "No search string provided",
                        "message": "❌ Please provide a search_string parameter or include it in the task description.",
                    }

                description = f"Searching for '{search_string}' in {target_path}"

                if is_windows:
                    # Windows command with findstr
                    if file_pattern != "*":
                        command = f'Get-ChildItem -Path "{target_path}" -Recurse -Include {file_pattern} -File -ErrorAction SilentlyContinue | Select-String -Pattern "{search_string}" -CaseSensitive:$false'
                    else:
                        command = f'Get-ChildItem -Path "{target_path}" -Recurse -File -ErrorAction SilentlyContinue | Select-String -Pattern "{search_string}" -CaseSensitive:$false'
                else:
                    # Linux/macOS command with grep
                    if file_pattern != "*":
                        command = f'find "{target_path}" -type f -name "{file_pattern}" -exec grep -l -i "{search_string}" {{}} \\; 2>/dev/null'
                    else:
                        command = f'grep -r -i -l "{search_string}" "{target_path}" 2>/dev/null'

            # Task 3: Disk usage analysis
            elif any(
                keyword in task_lower
                for keyword in ["disk usage", "folder size", "directory size", "space used"]
            ):
                description = f"Analyzing disk usage in {target_path}"

                if is_windows:
                    command = f'Get-ChildItem -Path "{target_path}" -Directory -ErrorAction SilentlyContinue | ForEach-Object {{ $size = (Get-ChildItem $_.FullName -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum; [PSCustomObject]@{{Folder=$_.Name; "Size(MB)"=[math]::Round($size/1MB,2)}} }} | Sort-Object "Size(MB)" -Descending | Format-Table -AutoSize'
                else:
                    command = f'du -h --max-depth=1 "{target_path}" 2>/dev/null | sort -rh'

            # Task 4: Count lines of code
            elif any(
                keyword in task_lower
                for keyword in ["count lines", "line count", "loc", "lines of code"]
            ):
                description = f"Counting lines of code in {target_path}"

                if file_pattern == "*":
                    # Default to common code files
                    file_pattern = "*.py,*.js,*.java,*.cpp,*.c,*.h,*.cs,*.ts,*.tsx,*.jsx"

                if is_windows:
                    patterns = file_pattern.split(",")
                    pattern_args = ",".join([f'"{p.strip()}"' for p in patterns])
                    command = f'$files = Get-ChildItem -Path "{target_path}" -Recurse -Include {pattern_args} -File -ErrorAction SilentlyContinue; $totalLines = 0; $files | ForEach-Object {{ $totalLines += (Get-Content $_.FullName -ErrorAction SilentlyContinue | Measure-Object -Line).Lines }}; Write-Output "Total files: $($files.Count)"; Write-Output "Total lines: $totalLines"'
                else:
                    patterns = file_pattern.replace(",", " -o -name ")
                    command = f'find "{target_path}" \\( -name {patterns} \\) -type f -exec wc -l {{}} + 2>/dev/null | tail -1'

            # Task 5: Find files by pattern/name
            elif any(
                keyword in task_lower
                for keyword in ["find files", "list files", "files matching", "files named"]
            ):
                description = f"Finding files matching pattern '{file_pattern}' in {target_path}"

                if is_windows:
                    command = f'Get-ChildItem -Path "{target_path}" -Recurse -Include {file_pattern} -File -ErrorAction SilentlyContinue | Select-Object FullName, @{{Name="Size(KB)";Expression={{[math]::Round($_.Length/1KB,2)}}}} | Format-Table -AutoSize'
                else:
                    command = f'find "{target_path}" -type f -name "{file_pattern}" -ls 2>/dev/null'

            # Generic fallback
            else:
                return {
                    "success": False,
                    "error": "Task type not recognized",
                    "message": f"❌ I couldn't understand the task: '{task}'\n\nSupported tasks:\n- Find largest/biggest files\n- Search for strings\n- Disk usage analysis\n- Count lines of code\n- Find files by pattern",
                    "suggestion": "Try rephrasing using keywords like: 'largest files', 'search for', 'disk usage', 'count lines', or 'find files'",
                }

            if not command:
                return {
                    "success": False,
                    "error": "Failed to generate command",
                    "message": "❌ Could not generate appropriate command for the task.",
                }

            # Build response with <commands> tag for LLM execution
            os_name = "Windows (PowerShell)" if is_windows else "Linux/macOS (Bash)"

            llm_context = f"""🔧 Shell Script Tool Execution

📋 Task: {task}
📂 Target: {target_path}
💻 OS: {os_name}

📝 Description:
{description}

⚡ Generated Command:
<commands>{command}</commands>

This command will be executed automatically. The results will appear below.
"""

            return {
                "success": True,
                "task": task,
                "target_path": target_path,
                "os_type": os_type,
                "command": command,
                "description": description,
                "llm_context": llm_context,
            }

        except Exception as e:
            return {"success": False, "error": str(e), "message": f"❌ Error: {e}"}

    def _extract_number(self, text: str, default: int = 50) -> int:
        """Extract number from text (e.g., '50' from 'list 50 biggest files')"""
        import re

        match = re.search(r"\b(\d+)\b", text)
        return int(match.group(1)) if match else default

    def _extract_search_string(self, text: str) -> str:
        """Extract search string from text (e.g., 'anthropic' from 'search for anthropic')"""
        import re

        # Try to find quoted string
        quoted = re.search(r'["\']([^"\']+)["\']', text)
        if quoted:
            return quoted.group(1)

        # Try common patterns
        patterns = [
            r"search for\s+(\w+)",
            r"find\s+(\w+)",
            r"contains\s+(\w+)",
            r'string\s+["\']?(\w+)["\']?',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return ""


# Export the tool class
__all__ = ["ShellScriptTool"]
