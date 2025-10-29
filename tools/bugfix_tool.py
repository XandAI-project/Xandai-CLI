"""
Bug Fix Tool - AI-powered stack trace analysis and bug fixing

This tool parses stack traces, reads relevant files, and uses AI to analyze
and suggest fixes for the errors found.
"""

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


class BugFixTool:
    """Analyze stack traces and suggest bug fixes using AI."""

    def __init__(self, llm_provider=None):
        """
        Initialize the bug fix tool.

        Args:
            llm_provider: LLM provider for intelligent analysis
        """
        self.llm_provider = llm_provider

    @staticmethod
    def get_name():
        """Return the tool's name."""
        return "bugfix_tool"

    @staticmethod
    def get_description():
        """Return description of what the tool does."""
        return "Analyze stack traces, read involved files, and suggest bug fixes using AI"

    @staticmethod
    def get_parameters():
        """Return the parameters this tool accepts."""
        return {
            "stack_trace": "string (required) - The complete stack trace/error message to analyze",
            "context_lines": "integer (optional) - Number of context lines to read around error location (default: 15)",
            "project_root": "string (optional) - Root directory of the project (default: current directory)",
        }

    def execute(
        self,
        stack_trace: str,
        context_lines: int = 15,
        project_root: str = ".",
    ):
        """
        Execute the bug fix analysis.

        Args:
            stack_trace: The complete stack trace or error message
            context_lines: Number of lines to read around the error location
            project_root: Root directory of the project

        Returns:
            Dictionary with analysis results and suggested fixes
        """
        try:
            # Parse the stack trace
            parsed_info = self._parse_stack_trace(stack_trace)

            if not parsed_info["files"]:
                # No files found, but we can still analyze with LLM
                if self.llm_provider:
                    return self._analyze_without_files(stack_trace)
                else:
                    return {
                        "success": False,
                        "error": "Could not parse file information and no LLM available",
                        "raw_trace": stack_trace,
                    }

            # Read relevant files
            file_contents = self._read_files(parsed_info["files"], project_root, context_lines)

            # Use LLM for intelligent analysis
            if self.llm_provider:
                llm_analysis = self._analyze_with_llm(parsed_info, file_contents, stack_trace)

                return {
                    "success": True,
                    "error_summary": {
                        "type": parsed_info["error_type"],
                        "message": parsed_info["error_message"],
                        "files_involved": len(parsed_info["files"]),
                    },
                    "analysis": llm_analysis,
                }
            else:
                # Fallback without LLM
                return {
                    "success": True,
                    "error_summary": {
                        "type": parsed_info["error_type"],
                        "message": parsed_info["error_message"],
                        "files_involved": len(parsed_info["files"]),
                    },
                    "file_contents": file_contents,
                    "note": "LLM not available - showing file contents only",
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Bug fix analysis error: {str(e)}",
                "raw_trace": stack_trace,
            }

    def _parse_stack_trace(self, stack_trace: str) -> Dict[str, Any]:
        """
        Parse stack trace to extract error information.

        Supports multiple formats:
        - Python: File "path", line X, in function
        - JavaScript/Node: at function (path:line:col)
        - Java: at class.method(File.java:line)
        - C#: at namespace.class.method() in File.cs:line X
        - Go: path/file.go:line +0xaddr
        - Ruby: from path:line:in `method'
        """
        parsed = {
            "error_type": "Unknown",
            "error_message": "",
            "files": [],
            "full_trace": stack_trace,
        }

        lines = stack_trace.split("\n")

        # Try to extract error type and message
        for line in lines:
            # Python style with module prefix: module.ErrorType: message
            module_error_match = re.match(
                r"^([\w.]+\.)?(\w+(?:Error|Exception|Warning)):\s*(.+)", line
            )
            if module_error_match:
                parsed["error_type"] = module_error_match.group(2)
                parsed["error_message"] = module_error_match.group(3).strip()
                break

            # Standard ErrorType: message
            error_match = re.match(r"^(\w+(?:Error|Exception|Warning)):\s*(.+)", line)
            if error_match:
                parsed["error_type"] = error_match.group(1)
                parsed["error_message"] = error_match.group(2).strip()
                break

        if not parsed["error_message"]:
            # Try last non-empty line
            for line in reversed(lines):
                if line.strip():
                    parsed["error_message"] = line.strip()
                    last_error_match = re.search(r"(\w+(?:Error|Exception|Warning)):", line)
                    if last_error_match:
                        parsed["error_type"] = last_error_match.group(1)
                    break

        # Parse file locations
        file_info_list = []

        for line in lines:
            # Python format: File "path", line X, in function
            python_match = re.search(r'File "([^"]+)", line (\d+)(?:, in (.+))?', line)
            if python_match:
                file_info_list.append(
                    {
                        "file": python_match.group(1),
                        "line": int(python_match.group(2)),
                        "function": python_match.group(3) if python_match.group(3) else "unknown",
                        "context": line.strip(),
                    }
                )
                continue

            # JavaScript/Node format: at function (path:line:col)
            js_match = re.search(r"at\s+(?:(.+?)\s+\()?([^)]+):(\d+):(\d+)\)?", line)
            if js_match:
                file_info_list.append(
                    {
                        "file": js_match.group(2),
                        "line": int(js_match.group(3)),
                        "column": int(js_match.group(4)),
                        "function": js_match.group(1) if js_match.group(1) else "anonymous",
                        "context": line.strip(),
                    }
                )
                continue

            # Java format: at package.Class.method(File.java:line)
            java_match = re.search(r"at\s+([a-zA-Z0-9_.]+)\(([^:]+):(\d+)\)", line)
            if java_match:
                file_info_list.append(
                    {
                        "file": java_match.group(2),
                        "line": int(java_match.group(3)),
                        "function": java_match.group(1),
                        "context": line.strip(),
                    }
                )
                continue

            # Generic path:line format (Go, Ruby, etc.)
            generic_match = re.search(r"([a-zA-Z0-9_./\\-]+\.\w+):(\d+)", line)
            if generic_match:
                file_info_list.append(
                    {
                        "file": generic_match.group(1),
                        "line": int(generic_match.group(2)),
                        "function": "unknown",
                        "context": line.strip(),
                    }
                )
                continue

        parsed["files"] = file_info_list
        return parsed

    def _read_files(
        self, file_list: List[Dict[str, Any]], project_root: str, context_lines: int
    ) -> List[Dict[str, Any]]:
        """
        Read the relevant sections of files mentioned in stack trace.

        Args:
            file_list: List of file information from parsed stack trace
            project_root: Root directory of the project
            context_lines: Number of lines to read around error location

        Returns:
            List of file contents with context
        """
        file_contents = []
        root_path = Path(project_root).resolve()

        for file_info in file_list:
            file_path_str = file_info["file"]
            error_line = file_info["line"]

            # Try to find the file
            possible_paths = [
                Path(file_path_str),
                root_path / file_path_str,
                root_path / Path(file_path_str).name,
            ]

            actual_path = None
            for path in possible_paths:
                if path.exists() and path.is_file():
                    actual_path = path
                    break

            if not actual_path:
                file_contents.append(
                    {
                        "file": file_path_str,
                        "line": error_line,
                        "error": "File not found",
                        "searched_paths": [str(p) for p in possible_paths],
                    }
                )
                continue

            try:
                with open(actual_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                # Calculate range
                start_line = max(0, error_line - context_lines - 1)
                end_line = min(len(lines), error_line + context_lines)

                # Extract context
                context = []
                for i in range(start_line, end_line):
                    is_error_line = (i + 1) == error_line
                    context.append(
                        {
                            "line_number": i + 1,
                            "content": lines[i].rstrip(),
                            "is_error_line": is_error_line,
                        }
                    )

                file_contents.append(
                    {
                        "file": str(actual_path),
                        "relative_path": file_path_str,
                        "error_line": error_line,
                        "function": file_info.get("function", "unknown"),
                        "context": context,
                        "total_lines": len(lines),
                        "full_content": "".join(lines),  # Keep full file for LLM
                    }
                )

            except Exception as e:
                file_contents.append(
                    {
                        "file": str(actual_path),
                        "line": error_line,
                        "error": f"Could not read file: {str(e)}",
                    }
                )

        return file_contents

    def _analyze_without_files(self, stack_trace: str) -> Dict[str, Any]:
        """Analyze stack trace when no files are found."""
        prompt = f"""You are an expert software engineer analyzing a bug.

STACK TRACE:
{stack_trace}

Please analyze this error and provide:
1. What type of error this is
2. What likely caused it
3. How to fix it
4. Prevention tips

Be specific and practical."""

        try:
            response = self.llm_provider.generate(prompt, max_tokens=1500)
            response_text = response.content if hasattr(response, "content") else str(response)

            return {
                "success": True,
                "analysis": response_text,
                "note": "No files were found to read, analysis based on stack trace only",
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"LLM analysis failed: {str(e)}",
            }

    def _analyze_with_llm(
        self, parsed_info: Dict[str, Any], file_contents: List[Dict[str, Any]], stack_trace: str
    ) -> str:
        """
        Use LLM to analyze the error and suggest fixes.

        Args:
            parsed_info: Parsed stack trace information
            file_contents: Contents of relevant files
            stack_trace: Original stack trace

        Returns:
            LLM analysis as formatted text
        """
        # Build context for LLM
        files_context = ""
        for file_data in file_contents:
            if "error" in file_data:
                files_context += f"\n## File: {file_data['file']}\n"
                files_context += f"ERROR: {file_data['error']}\n"
                continue

            files_context += f"\n## File: {file_data['relative_path']}\n"
            files_context += (
                f"Error at line {file_data['error_line']} in function '{file_data['function']}'\n"
            )
            files_context += f"Total lines in file: {file_data['total_lines']}\n\n"
            files_context += "### Code Context:\n```\n"

            for line_info in file_data["context"]:
                marker = ">>> " if line_info["is_error_line"] else "    "
                files_context += f"{marker}{line_info['line_number']:4d} | {line_info['content']}\n"

            files_context += "```\n"

        # Create comprehensive prompt
        prompt = f"""You are an expert software engineer and debugging specialist. Analyze this bug and provide a comprehensive fix.

## STACK TRACE:
```
{stack_trace}
```

## ERROR INFORMATION:
- Type: {parsed_info['error_type']}
- Message: {parsed_info['error_message']}
- Files involved: {len(parsed_info['files'])}

## FILE CONTENTS:
{files_context}

## YOUR TASK:

Analyze this bug thoroughly and provide:

1. **Root Cause Analysis**: What exactly is causing this error? Be specific about the line of code and why it fails.

2. **Explanation**: Explain in simple terms what went wrong and why the code behaves this way.

3. **The Fix**: Provide the COMPLETE fixed file content. Use this EXACT format for EACH file that needs changes:

<code edit filename="path/to/file.py">
[COMPLETE file content with the fix applied - from first line to last line]
</code>

CRITICAL FORMAT RULES:
- Use <code edit filename="..."> for fixing existing files
- Include the ENTIRE file content, not just changed sections
- Do NOT use markdown code blocks (```python, etc.) inside <code> tags
- Do NOT use any other format (no SEARCH/REPLACE, no line numbers, no diffs)
- ONE <code> tag = ONE complete file
- MUST end with </code> tag
- If multiple files need changes, provide separate <code edit> blocks for each
- Do NOT add explanatory text between <code> tags

4. **Prevention Tips**: How to avoid similar bugs in the future.

## IMPORTANT RULES:
- Provide COMPLETE working files in <code> tags
- Include proper indentation and syntax
- Include ALL imports, ALL functions, ALL code
- Test your logic mentally before suggesting
- Do NOT use markdown (```) inside <code> tags
- Be concise but thorough in explanations

## EXAMPLE FORMAT:

**File: app.py needs fixing**

<code edit filename="app.py">
import json
import os

def calculate_total(items):
    total = 0
    for item in items:
        if item and hasattr(item, 'price'):
            total = total + item.price
    return total

def main():
    items = load_items()
    total = calculate_total(items)
    print(f"Total: {{total}}")

if __name__ == "__main__":
    main()
</code>

Begin your analysis:"""

        try:
            response = self.llm_provider.generate(prompt, max_tokens=3000)
            response_text = response.content if hasattr(response, "content") else str(response)
            return response_text

        except Exception as e:
            return f"Error during LLM analysis: {str(e)}\n\nPlease review the stack trace and file contents manually."
