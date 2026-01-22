"""
LSP Tool - Language Server Protocol Operations

Provides explicit access to LSP functionality for code intelligence.
"""

import os
from pathlib import Path
from typing import Any, Dict

from xandai.lsp import LSPManager


class LSPTool:
    """Interact with Language Server Protocol for code intelligence."""

    def __init__(self):
        """Initialize LSP Tool"""
        self._lsp_manager = None
        self._initialized = False

    @staticmethod
    def get_name():
        """Return the tool's name."""
        return "lsp_tool"

    @staticmethod
    def get_description():
        """Return description of what the tool does."""
        return "Get code intelligence using Language Server Protocol - analyze code, check syntax, get completions, and project context"

    @staticmethod
    def get_parameters():
        """Return the parameters this tool accepts."""
        return {
            "operation": "string (required) - Operation: 'status', 'analyze', 'project_info', 'completions', 'diagnostics'",
            "file_path": "string (optional) - Path to file for file-specific operations",
            "line": "number (optional) - Line number for position-specific operations (0-indexed)",
            "character": "number (optional) - Character position (0-indexed)",
        }

    def execute(
        self, operation: str, file_path: str = None, line: int = None, character: int = None
    ) -> Dict[str, Any]:
        """
        Execute LSP operation.

        Args:
            operation: Operation to perform
            file_path: Path to file (for file-specific operations)
            line: Line number (0-indexed)
            character: Character position (0-indexed)

        Returns:
            Dictionary with operation results
        """
        try:
            # Initialize LSP manager if needed
            if not self._initialized:
                self._initialize_lsp()

            operation = operation.lower()

            # LSP Status
            if operation == "status":
                return self._get_status()

            # Project Information
            elif operation == "project_info":
                return self._get_project_info()

            # Analyze File
            elif operation == "analyze":
                if not file_path:
                    return {
                        "success": False,
                        "error": "file_path is required for 'analyze' operation",
                    }
                return self._analyze_file(file_path)

            # Get Completions
            elif operation == "completions":
                if not file_path or line is None or character is None:
                    return {
                        "success": False,
                        "error": "file_path, line, and character are required for 'completions' operation",
                    }
                return self._get_completions(file_path, line, character)

            # Get Diagnostics
            elif operation == "diagnostics":
                if not file_path:
                    return {
                        "success": False,
                        "error": "file_path is required for 'diagnostics' operation",
                    }
                return self._get_diagnostics(file_path)

            else:
                return {
                    "success": False,
                    "error": f"Unknown operation: {operation}. Use: status, project_info, analyze, completions, diagnostics",
                }

        except Exception as e:
            return {"success": False, "error": f"LSP operation failed: {str(e)}"}

    def _initialize_lsp(self):
        """Initialize LSP manager"""
        if not self._lsp_manager:
            root_path = os.getcwd()
            self._lsp_manager = LSPManager(root_path, verbose=False)
            self._lsp_manager.initialize(auto_start=True)
            self._initialized = True

    def _get_status(self) -> Dict[str, Any]:
        """Get LSP status"""
        status = self._lsp_manager.get_lsp_status()

        result = {
            "success": True,
            "operation": "status",
            "lsp_initialized": status["initialized"],
            "root_path": status["root_path"],
            "active_servers": {},
            "available_servers": {},
            "project_stats": status["project_stats"],
        }

        # Format active servers
        for lang, info in status["active_servers"].items():
            result["active_servers"][lang] = {
                "server": info["server_name"],
                "running": info["is_running"],
                "files": info["file_count"],
            }

        # Format available servers
        for lang, info in status["available_servers"].items():
            result["available_servers"][lang] = {
                "server": info["server_name"],
                "installed": info["is_installed"],
                "install_command": info["install_command"] if not info["is_installed"] else None,
                "files": info["file_count"],
            }

        return result

    def _get_project_info(self) -> Dict[str, Any]:
        """Get project information"""
        stats = self._lsp_manager.get_project_statistics()

        return {
            "success": True,
            "operation": "project_info",
            "project_type": stats["project_type"],
            "primary_language": stats["primary_language"],
            "total_files": stats["total_files"],
            "language_count": stats["language_count"],
            "languages": stats["languages"],
        }

    def _analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a specific file"""
        # Resolve file path
        if not os.path.isabs(file_path):
            file_path = os.path.join(os.getcwd(), file_path)

        if not os.path.exists(file_path):
            return {"success": False, "error": f"File not found: {file_path}"}

        context = self._lsp_manager.get_file_context(file_path)

        return {
            "success": True,
            "operation": "analyze",
            "file_path": file_path,
            "language": context["language"],
            "lsp_available": context["lsp_available"],
            "server_info": context.get("server_info"),
            "diagnostics_count": len(context.get("diagnostics", [])),
            "diagnostics": context.get("diagnostics", [])[:10],  # Limit to 10
        }

    def _get_completions(self, file_path: str, line: int, character: int) -> Dict[str, Any]:
        """Get code completions"""
        # Resolve file path
        if not os.path.isabs(file_path):
            file_path = os.path.join(os.getcwd(), file_path)

        if not os.path.exists(file_path):
            return {"success": False, "error": f"File not found: {file_path}"}

        # Read file content
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        completions = self._lsp_manager.get_completions(file_path, line, character, content)

        return {
            "success": True,
            "operation": "completions",
            "file_path": file_path,
            "position": {"line": line, "character": character},
            "completion_count": len(completions),
            "completions": completions[:20],  # Limit to 20
        }

    def _get_diagnostics(self, file_path: str) -> Dict[str, Any]:
        """Get file diagnostics"""
        # Resolve file path
        if not os.path.isabs(file_path):
            file_path = os.path.join(os.getcwd(), file_path)

        if not os.path.exists(file_path):
            return {"success": False, "error": f"File not found: {file_path}"}

        # Read file content
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        diagnostics = self._lsp_manager.get_diagnostics(file_path, content)

        # Categorize diagnostics
        errors = [d for d in diagnostics if d.get("severity") == 1]
        warnings = [d for d in diagnostics if d.get("severity") == 2]
        info = [d for d in diagnostics if d.get("severity") == 3]

        return {
            "success": True,
            "operation": "diagnostics",
            "file_path": file_path,
            "total_issues": len(diagnostics),
            "errors": len(errors),
            "warnings": len(warnings),
            "info": len(info),
            "diagnostics": diagnostics[:20],  # Limit to 20
        }
