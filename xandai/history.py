"""
XandAI - History Manager
Manages conversation history and tracks file edits to prevent duplicates
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class HistoryManager:
    """
    Manages conversation history and file edit tracking

    Features:
    - In-memory conversation history
    - File content tracking to prevent duplicates
    - Project context maintenance
    - Framework consistency tracking
    """

    def __init__(self, history_dir: str = ".xandai_history"):
        """Initialize history manager with robust Windows error handling"""
        self.history_dir = Path(history_dir)
        self.history_enabled = True

        # Robust directory creation with Windows-specific error handling
        try:
            # First, check if directory already exists
            if not self.history_dir.exists():
                self.history_dir.mkdir(parents=True, exist_ok=True)
            elif not self.history_dir.is_dir():
                # If it exists but is not a directory, try alternative location
                raise OSError("History path exists but is not a directory")

        except (OSError, FileExistsError, PermissionError) as e:
            # Windows-specific handling for WinError 183 and similar issues
            print(f"⚠️  Warning: Could not create history directory '{history_dir}': {e}")

            # Try alternative locations in order of preference
            alternative_paths = [
                Path.home() / ".xandai_history",  # User home directory
                Path.cwd() / "xandai_history",  # Current working directory
                Path(os.environ.get("TEMP", "/tmp")) / "xandai_history",  # Temp directory
            ]

            success = False
            for alt_path in alternative_paths:
                try:
                    alt_path.mkdir(parents=True, exist_ok=True)
                    self.history_dir = alt_path
                    print(f"✅ Using alternative history directory: {alt_path}")
                    success = True
                    break
                except (OSError, PermissionError):
                    continue

            if not success:
                # Last resort: disable history persistence
                print(
                    "⚠️  Warning: Could not create any history directory. History will not be persisted."
                )
                self.history_enabled = False
                self.history_dir = None

        # In-memory storage
        self.conversation_history: List[Dict[str, Any]] = []
        self.file_contents: Dict[str, str] = {}  # filename -> latest_content
        self.project_context: Dict[str, Any] = {
            "framework": None,  # Track consistent framework choice
            "language": None,  # Primary language
            "project_type": None,  # web, cli, api, etc.
            "dependencies": [],  # Track dependencies
            "structure": {},  # Track project structure
        }

        # Load existing history if available
        self._load_history()

    def add_conversation(
        self,
        role: str,
        content: str,
        context_usage: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ):
        """Add message to conversation history"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "role": role,  # 'user', 'assistant', 'system'
            "content": content,
            "context_usage": context_usage,
            "metadata": metadata or {},
        }

        self.conversation_history.append(entry)

        # Keep history manageable (last 100 messages)
        if len(self.conversation_history) > 100:
            self.conversation_history = self.conversation_history[-100:]

        # Auto-save periodically
        if len(self.conversation_history) % 10 == 0:
            self._save_history()

    def get_recent_conversation(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent conversation messages"""
        return self.conversation_history[-limit:] if limit > 0 else self.conversation_history

    def get_conversation_context(self, limit: int = 10) -> List[Dict[str, str]]:
        """Get conversation context for LLM (role/content format)"""
        recent = self.get_recent_conversation(limit)
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in recent
            if msg["role"] in ["user", "assistant", "system"]
        ]

    def track_file_edit(self, filename: str, content: str, operation: str = "edit"):
        """
        Track file edits to maintain consistency

        Args:
            filename: Path to file
            content: New file content
            operation: 'create', 'edit', 'delete'
        """
        # Normalize path
        filepath = os.path.normpath(filename)

        # Store content
        if operation == "delete":
            self.file_contents.pop(filepath, None)
        else:
            self.file_contents[filepath] = content

        # Add to conversation metadata
        self.add_conversation(
            role="system",
            content=f"File {operation}: {filepath}",
            metadata={
                "type": "file_operation",
                "operation": operation,
                "filepath": filepath,
                "content_length": len(content) if content else 0,
            },
        )

        # Update project context
        self._update_project_context(filepath, content, operation)

    def get_file_content(self, filename: str) -> Optional[str]:
        """Get current content of tracked file"""
        filepath = os.path.normpath(filename)
        return self.file_contents.get(filepath)

    def file_exists_in_history(self, filename: str) -> bool:
        """Check if file has been tracked"""
        filepath = os.path.normpath(filename)
        return filepath in self.file_contents

    def get_project_files(self) -> List[str]:
        """Get list of all tracked files"""
        return list(self.file_contents.keys())

    def set_project_context(
        self,
        framework: Optional[str] = None,
        language: Optional[str] = None,
        project_type: Optional[str] = None,
    ):
        """Manually set project context"""
        if framework:
            self.project_context["framework"] = framework
        if language:
            self.project_context["language"] = language
        if project_type:
            self.project_context["project_type"] = project_type

    def get_project_context(self) -> Dict[str, Any]:
        """Get current project context"""
        return self.project_context.copy()

    def get_context_summary(self) -> str:
        """Get formatted project context summary (simplified for terminal prompt)"""
        summary_parts = []

        file_count = len(self.file_contents)
        if file_count > 0:
            summary_parts.append(f"Files: {file_count}")

        return " | ".join(summary_parts) if summary_parts else "No project context"

    def clear_conversation(self):
        """Clear conversation history (keep file tracking)"""
        self.conversation_history.clear()

    def clear_all(self):
        """Clear all history and context"""
        self.conversation_history.clear()
        self.file_contents.clear()
        self.project_context = {
            "framework": None,
            "language": None,
            "project_type": None,
            "dependencies": [],
            "structure": {},
        }

    def export_conversation(self, filepath: str):
        """Export conversation history to file"""
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "conversation": self.conversation_history,
            "project_context": self.project_context,
            "file_count": len(self.file_contents),
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

    def _update_project_context(self, filepath: str, content: str, operation: str):
        """Update project context based on file operations"""
        if operation == "delete":
            return

        # Infer language from file extension
        ext = Path(filepath).suffix.lower()
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".html": "html",
            ".css": "css",
            ".json": "json",
            ".md": "markdown",
            ".yml": "yaml",
            ".yaml": "yaml",
        }

        if ext in language_map and not self.project_context["language"]:
            self.project_context["language"] = language_map[ext]

        # Infer framework from file content and names
        if not self.project_context["framework"]:
            content_lower = content.lower()
            filepath_lower = filepath.lower()

            # Framework detection patterns
            if "package.json" in filepath_lower:
                if "react" in content_lower:
                    self.project_context["framework"] = "react"
                elif "express" in content_lower:
                    self.project_context["framework"] = "express"
                elif "vue" in content_lower:
                    self.project_context["framework"] = "vue"
            elif "requirements.txt" in filepath_lower:
                if "flask" in content_lower:
                    self.project_context["framework"] = "flask"
                elif "django" in content_lower:
                    self.project_context["framework"] = "django"
                elif "fastapi" in content_lower:
                    self.project_context["framework"] = "fastapi"
            elif ext == ".py":
                if "from flask import" in content_lower or "import flask" in content_lower:
                    self.project_context["framework"] = "flask"
                elif "from django" in content_lower or "import django" in content_lower:
                    self.project_context["framework"] = "django"

        # Update project structure
        dir_name = os.path.dirname(filepath) or "."
        if dir_name not in self.project_context["structure"]:
            self.project_context["structure"][dir_name] = []

        filename = os.path.basename(filepath)
        if filename not in self.project_context["structure"][dir_name]:
            self.project_context["structure"][dir_name].append(filename)

    def _save_history(self):
        """Save history to disk (with error protection)"""
        if not self.history_enabled or not self.history_dir:
            return

        try:
            history_file = self.history_dir / "conversation.json"
            export_data = {
                "timestamp": datetime.now().isoformat(),
                "conversation": self.conversation_history[-50:],  # Save last 50 messages
                "project_context": self.project_context,
            }

            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2)
        except Exception:
            # Silent fail - don't interrupt user experience
            pass

    def _load_history(self):
        """Load history from disk (with error protection)"""
        if not self.history_enabled or not self.history_dir:
            return

        try:
            history_file = self.history_dir / "conversation.json"
            if history_file.exists():
                with open(history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                self.conversation_history = data.get("conversation", [])
                self.project_context.update(data.get("project_context", {}))
        except Exception:
            # Silent fail - start with empty history
            pass
