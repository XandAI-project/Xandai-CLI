#!/usr/bin/env python3
"""
XandAI - Enhanced File Handler
Integration layer between AI file operations and existing chat REPL
"""

import re
from typing import Dict, List, Optional, Tuple

from rich.console import Console

from xandai.history import HistoryManager
from xandai.integrations.base_provider import LLMProvider
from xandai.utils.ai_file_prompts import AIFilePrompts
from xandai.utils.file_operations import FileOperationsManager


class EnhancedFileHandler:
    """
    Enhanced file handler that integrates AI-guided file operations

    This class serves as a bridge between:
    - AI prompts and responses
    - File operations manager
    - Chat REPL interface
    - History management

    Features:
    - Smart detection of file operations in AI responses
    - Batch file creation support
    - Enhanced prompts for better AI understanding
    - Automatic validation and backup
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        history_manager: HistoryManager,
        console: Optional[Console] = None,
        verbose: bool = False,
    ):
        """
        Initialize enhanced file handler

        Args:
            llm_provider: LLM provider for AI operations
            history_manager: History manager for tracking operations
            console: Rich console for output
            verbose: Enable verbose logging
        """
        self.llm_provider = llm_provider
        self.history_manager = history_manager
        self.console = console or Console()
        self.verbose = verbose

        self.file_ops = FileOperationsManager(console=self.console)
        self.prompts = AIFilePrompts()

    def detect_file_operations_in_response(self, response: str) -> List[Tuple[str, str, str]]:
        """
        Detect file operations in AI response

        Args:
            response: AI response text

        Returns:
            List of tuples (operation_type, filename, content)
            operation_type is 'create', 'edit', or 'update'
        """
        operations = []

        # Pattern to match <code edit filename="..."> and <code create filename="...">
        pattern = r'<code\s+(edit|create|update)\s+filename=["\']([^"\']+)["\']>(.*?)</code>'
        matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)

        for operation_type, filename, content in matches:
            # Clean up content
            content = content.strip()

            # Normalize operation type
            if operation_type.lower() in ["edit", "update"]:
                op_type = "update"
            else:
                op_type = "create"

            operations.append((op_type, filename, content))

        return operations

    def execute_detected_operations(
        self, operations: List[Tuple[str, str, str]], interactive: bool = True
    ) -> Dict[str, bool]:
        """
        Execute detected file operations

        Args:
            operations: List of (operation_type, filename, content) tuples
            interactive: If True, prompt user for confirmation

        Returns:
            Dictionary mapping filenames to success status
        """
        results = {}

        if not operations:
            return results

        # Check if it's a batch operation (multiple files)
        is_batch = len(operations) > 1

        if is_batch:
            self.console.print(
                f"\n[cyan]📦 Detected batch operation: {len(operations)} file(s)[/cyan]"
            )
            for op_type, filename, _ in operations:
                self.console.print(f"  • [{op_type}] {filename}")

            if interactive:
                self.console.print(
                    "\n[yellow]Execute all file operations? (y/N):[/yellow]", end=" "
                )
                response = input().strip().lower()
                if response not in ["y", "yes", "sim", "s"]:
                    self.console.print("[dim]Batch operation cancelled.[/dim]")
                    return {filename: False for _, filename, _ in operations}

        # Execute each operation
        for op_type, filename, content in operations:
            if op_type == "create":
                operation = self.file_ops.create_file(
                    filename, content, overwrite=False, interactive=(not is_batch and interactive)
                )
            else:  # update
                operation = self.file_ops.update_file(
                    filename,
                    content,
                    create_if_missing=True,
                    interactive=(not is_batch and interactive),
                )

            results[filename] = operation.success

            # Track in history
            if operation.success:
                self.history_manager.track_file_edit(filename, content, op_type)

        return results

    def create_multiple_files(
        self, files: Dict[str, str], interactive: bool = True
    ) -> Dict[str, bool]:
        """
        Create multiple files in one operation

        Args:
            files: Dictionary mapping filenames to content
            interactive: If True, prompt for confirmation

        Returns:
            Dictionary mapping filenames to success status
        """
        result = self.file_ops.batch_create_files(files, overwrite=False, interactive=interactive)

        # Track successful operations in history
        for operation in result.operations:
            if operation.success:
                self.history_manager.track_file_edit(
                    operation.file_path, operation.content or "", "create"
                )

        # Return status for each file
        return {op.file_path: op.success for op in result.operations}

    def update_multiple_files(
        self, files: Dict[str, str], interactive: bool = True
    ) -> Dict[str, bool]:
        """
        Update multiple files in one operation

        Args:
            files: Dictionary mapping filenames to new content
            interactive: If True, prompt for confirmation

        Returns:
            Dictionary mapping filenames to success status
        """
        result = self.file_ops.batch_update_files(
            files, create_if_missing=True, interactive=interactive
        )

        # Track successful operations in history
        for operation in result.operations:
            if operation.success:
                self.history_manager.track_file_edit(
                    operation.file_path, operation.content or "", "update"
                )

        # Return status for each file
        return {op.file_path: op.success for op in result.operations}

    def get_enhanced_system_prompt(self) -> str:
        """Get enhanced system prompt for chat mode"""
        return self.prompts.get_enhanced_system_prompt_for_chat()

    def get_file_update_prompt(self, file_path: str, file_content: str, issue: str) -> str:
        """
        Get context-aware prompt for fixing a file

        Args:
            file_path: Path to the file
            file_content: Current file content
            issue: Description of the issue to fix

        Returns:
            Complete prompt for AI
        """
        return self.prompts.get_code_fix_context_prompt(file_path, file_content, issue)

    def get_multi_file_creation_prompt(
        self, project_description: str, file_list: Optional[List[str]] = None
    ) -> str:
        """
        Get prompt for creating multiple files

        Args:
            project_description: Description of what to create
            file_list: Optional list of specific files

        Returns:
            Complete prompt for AI
        """
        return self.prompts.get_multi_file_creation_context_prompt(project_description, file_list)

    def enhance_user_query(self, user_query: str, file_path: Optional[str] = None) -> str:
        """
        Enhance user query for better AI understanding

        Args:
            user_query: Original user query
            file_path: Optional file path context

        Returns:
            Enhanced query
        """
        return self.prompts.enhance_user_query_for_fix(user_query, file_path)

    def process_ai_response_with_files(
        self, ai_response: str, interactive: bool = True
    ) -> Tuple[str, Dict[str, bool]]:
        """
        Process AI response and execute any file operations

        Args:
            ai_response: AI response text
            interactive: If True, prompt user for confirmation

        Returns:
            Tuple of (response_text, file_operations_results)
        """
        # Detect file operations
        operations = self.detect_file_operations_in_response(ai_response)

        if not operations:
            return ai_response, {}

        # Execute operations
        results = self.execute_detected_operations(operations, interactive=interactive)

        return ai_response, results

    def validate_and_fix_code(
        self, file_path: str, code_content: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate code content before writing

        Args:
            file_path: Path to the file (used for syntax checking)
            code_content: Code to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        return self.file_ops.validate_file_content(code_content, file_path)

    def get_operation_summary(self) -> str:
        """
        Get summary of recent file operations

        Returns:
            Formatted summary string
        """
        history = self.file_ops.get_operation_history()

        if not history:
            return "No file operations performed yet."

        summary_lines = ["📊 Recent File Operations:"]
        for i, op in enumerate(history[-10:], 1):  # Last 10 operations
            status = "✅" if op.success else "❌"
            summary_lines.append(f"  {i}. {status} [{op.operation_type}] {op.file_path}")
            if op.error:
                summary_lines.append(f"      Error: {op.error}")

        return "\n".join(summary_lines)

    def ask_ai_to_fix_file(
        self, file_path: str, issue_description: str, interactive: bool = True
    ) -> Tuple[bool, Optional[str]]:
        """
        Ask AI to fix a specific file

        Args:
            file_path: Path to the file to fix
            issue_description: Description of the issue
            interactive: If True, prompt user for confirmation

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Read current file content
            from pathlib import Path

            path = Path(file_path)
            if not path.exists():
                return False, f"File '{file_path}' does not exist"

            with open(path, "r", encoding="utf-8") as f:
                current_content = f.read()

            # Generate fix prompt
            fix_prompt = self.get_file_update_prompt(file_path, current_content, issue_description)

            # Get enhanced system prompt
            system_prompt = self.prompts.get_file_update_system_prompt()

            # Call AI
            self.console.print(f"[dim]🤖 Asking AI to fix '{file_path}'...[/dim]")

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": fix_prompt},
            ]

            response = self.llm_provider.chat(messages=messages, temperature=0.3)

            # Process response
            ai_response, results = self.process_ai_response_with_files(
                response.content, interactive=interactive
            )

            if file_path in results and results[file_path]:
                return True, None
            elif file_path in results:
                return False, "Failed to apply fix"
            else:
                return False, "AI did not provide a file update"

        except Exception as e:
            return False, str(e)

    def ask_ai_to_create_files(
        self,
        project_description: str,
        file_list: Optional[List[str]] = None,
        interactive: bool = True,
    ) -> Tuple[Dict[str, bool], Optional[str]]:
        """
        Ask AI to create multiple files

        Args:
            project_description: Description of what to create
            file_list: Optional list of specific files to create
            interactive: If True, prompt user for confirmation

        Returns:
            Tuple of (file_results_dict, error_message)
        """
        try:
            # Generate creation prompt
            creation_prompt = self.get_multi_file_creation_prompt(project_description, file_list)

            # Get enhanced system prompt
            system_prompt = self.prompts.get_multi_file_creation_system_prompt()

            # Call AI
            self.console.print(f"[dim]🤖 Asking AI to create files...[/dim]")

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": creation_prompt},
            ]

            response = self.llm_provider.chat(messages=messages, temperature=0.3)

            # Process response
            ai_response, results = self.process_ai_response_with_files(
                response.content, interactive=interactive
            )

            if results:
                return results, None
            else:
                return {}, "AI did not provide any file creations"

        except Exception as e:
            return {}, str(e)
