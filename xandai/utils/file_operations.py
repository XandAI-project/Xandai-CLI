#!/usr/bin/env python3
"""
XandAI - Enhanced File Operations Module
Handles file creation, updates, and batch operations with AI assistance
"""

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from rich.console import Console


@dataclass
class FileOperation:
    """Represents a file operation to be performed"""

    operation_type: str  # 'create', 'update', 'delete'
    file_path: str
    content: Optional[str] = None
    backup_path: Optional[str] = None
    success: bool = False
    error: Optional[str] = None


@dataclass
class BatchOperationResult:
    """Result of batch file operations"""

    total_operations: int
    successful_operations: int
    failed_operations: int
    operations: List[FileOperation]

    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_operations == 0:
            return 0.0
        return (self.successful_operations / self.total_operations) * 100


class FileOperationsManager:
    """
    Enhanced file operations manager with AI-friendly features

    Features:
    - Smart file update with content validation
    - Batch file creation without task mode
    - Automatic backup creation
    - Rollback support for failed operations
    - Detailed operation logging
    """

    def __init__(self, console: Optional[Console] = None, create_backups: bool = False):
        """
        Initialize file operations manager

        Args:
            console: Rich console for output (optional)
            create_backups: Whether to create backups before updates
        """
        self.console = console or Console()
        self.create_backups = create_backups
        self.operations_history: List[FileOperation] = []

    def create_file(
        self, file_path: str, content: str, overwrite: bool = False, interactive: bool = True
    ) -> FileOperation:
        """
        Create a new file with the given content

        Args:
            file_path: Path to the file to create
            content: Content to write to the file
            overwrite: If True, overwrite existing file without prompting
            interactive: If True, prompt user for confirmation

        Returns:
            FileOperation object with operation result
        """
        operation = FileOperation(operation_type="create", file_path=file_path, content=content)

        try:
            path = Path(file_path)

            # Check if file already exists
            if path.exists():
                if not overwrite and interactive:
                    self.console.print(
                        f"[yellow]⚠️  File '{file_path}' already exists. Overwrite? (y/N):[/yellow]",
                        end=" ",
                    )
                    response = input().strip().lower()
                    if response not in ["y", "yes", "sim", "s"]:
                        operation.error = "User cancelled overwrite"
                        self.console.print("[dim]File creation cancelled.[/dim]")
                        return operation
                elif not overwrite:
                    operation.error = "File already exists and overwrite=False"
                    self.console.print(f"[yellow]⚠️  File '{file_path}' already exists[/yellow]")
                    return operation

            # Create parent directories if they don't exist
            path.parent.mkdir(parents=True, exist_ok=True)

            # Write file content
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            operation.success = True
            self.console.print(f"[green]✅ File '{file_path}' created successfully![/green]")

        except Exception as e:
            operation.error = str(e)
            self.console.print(f"[red]❌ Error creating file '{file_path}': {e}[/red]")

        finally:
            self.operations_history.append(operation)

        return operation

    def update_file(
        self, file_path: str, content: str, create_if_missing: bool = True, interactive: bool = True
    ) -> FileOperation:
        """
        Update an existing file with new content

        Args:
            file_path: Path to the file to update
            content: New content to write to the file
            create_if_missing: If True, create file if it doesn't exist
            interactive: If True, prompt user for confirmation

        Returns:
            FileOperation object with operation result
        """
        operation = FileOperation(operation_type="update", file_path=file_path, content=content)

        try:
            path = Path(file_path)

            # Check if file exists
            if not path.exists():
                if create_if_missing:
                    if interactive:
                        self.console.print(
                            f"[yellow]⚠️  File '{file_path}' doesn't exist. Create it? (y/N):[/yellow]",
                            end=" ",
                        )
                        response = input().strip().lower()
                        if response in ["y", "yes", "sim", "s"]:
                            return self.create_file(file_path, content, interactive=False)
                        else:
                            operation.error = "User cancelled file creation"
                            self.console.print("[dim]File update cancelled.[/dim]")
                            return operation
                    else:
                        return self.create_file(file_path, content, interactive=False)
                else:
                    operation.error = "File doesn't exist and create_if_missing=False"
                    self.console.print(f"[yellow]⚠️  File '{file_path}' doesn't exist[/yellow]")
                    return operation

            # Create backup if enabled
            if self.create_backups:
                backup_path = self._create_backup(path)
                operation.backup_path = str(backup_path)

            # Write new content
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            operation.success = True
            self.console.print(f"[green]✅ File '{file_path}' updated successfully![/green]")

        except Exception as e:
            operation.error = str(e)
            self.console.print(f"[red]❌ Error updating file '{file_path}': {e}[/red]")

            # Attempt to restore from backup if update failed
            if operation.backup_path and Path(operation.backup_path).exists():
                self._restore_from_backup(operation.backup_path, file_path)

        finally:
            self.operations_history.append(operation)

        return operation

    def batch_create_files(
        self, files: Dict[str, str], overwrite: bool = False, interactive: bool = True
    ) -> BatchOperationResult:
        """
        Create multiple files in a single operation

        Args:
            files: Dictionary mapping file paths to content
            overwrite: If True, overwrite existing files without prompting
            interactive: If True, prompt user for batch confirmation

        Returns:
            BatchOperationResult with detailed results
        """
        operations = []
        successful = 0
        failed = 0

        # Show batch operation summary
        self.console.print(f"\n[cyan]📦 Batch File Creation: {len(files)} file(s) to create[/cyan]")
        for file_path in files.keys():
            self.console.print(f"  • {file_path}")

        if interactive:
            self.console.print("\n[yellow]Proceed with batch creation? (y/N):[/yellow]", end=" ")
            response = input().strip().lower()
            if response not in ["y", "yes", "sim", "s"]:
                self.console.print("[dim]Batch operation cancelled.[/dim]")
                return BatchOperationResult(
                    total_operations=len(files),
                    successful_operations=0,
                    failed_operations=0,
                    operations=[],
                )

        self.console.print("\n[cyan]🚀 Starting batch file creation...[/cyan]\n")

        # Create all files
        for file_path, content in files.items():
            operation = self.create_file(file_path, content, overwrite=overwrite, interactive=False)
            operations.append(operation)

            if operation.success:
                successful += 1
            else:
                failed += 1

        # Show summary
        result = BatchOperationResult(
            total_operations=len(files),
            successful_operations=successful,
            failed_operations=failed,
            operations=operations,
        )

        self._print_batch_summary(result)
        return result

    def batch_update_files(
        self, files: Dict[str, str], create_if_missing: bool = True, interactive: bool = True
    ) -> BatchOperationResult:
        """
        Update multiple files in a single operation

        Args:
            files: Dictionary mapping file paths to new content
            create_if_missing: If True, create files that don't exist
            interactive: If True, prompt user for batch confirmation

        Returns:
            BatchOperationResult with detailed results
        """
        operations = []
        successful = 0
        failed = 0

        # Show batch operation summary
        self.console.print(f"\n[cyan]📦 Batch File Update: {len(files)} file(s) to update[/cyan]")
        for file_path in files.keys():
            exists = Path(file_path).exists()
            status = "✓" if exists else "✗"
            self.console.print(f"  {status} {file_path}")

        if interactive:
            self.console.print("\n[yellow]Proceed with batch update? (y/N):[/yellow]", end=" ")
            response = input().strip().lower()
            if response not in ["y", "yes", "sim", "s"]:
                self.console.print("[dim]Batch operation cancelled.[/dim]")
                return BatchOperationResult(
                    total_operations=len(files),
                    successful_operations=0,
                    failed_operations=0,
                    operations=[],
                )

        self.console.print("\n[cyan]🚀 Starting batch file update...[/cyan]\n")

        # Update all files
        for file_path, content in files.items():
            operation = self.update_file(
                file_path, content, create_if_missing=create_if_missing, interactive=False
            )
            operations.append(operation)

            if operation.success:
                successful += 1
            else:
                failed += 1

        # Show summary
        result = BatchOperationResult(
            total_operations=len(files),
            successful_operations=successful,
            failed_operations=failed,
            operations=operations,
        )

        self._print_batch_summary(result)
        return result

    def validate_file_content(self, content: str, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate file content before writing

        Args:
            content: Content to validate
            file_path: File path (used to determine file type)

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if content is empty
        if not content or not content.strip():
            return False, "Content is empty"

        # Check file extension for syntax validation
        path = Path(file_path)
        ext = path.suffix.lower()

        # Python file validation
        if ext == ".py":
            try:
                compile(content, file_path, "exec")
            except SyntaxError as e:
                return False, f"Python syntax error: {e}"

        # JSON file validation
        elif ext == ".json":
            try:
                import json

                json.loads(content)
            except json.JSONDecodeError as e:
                return False, f"JSON syntax error: {e}"

        # Basic validation for other files
        # Check for common issues like binary data in text files
        try:
            content.encode("utf-8")
        except UnicodeEncodeError as e:
            return False, f"Encoding error: {e}"

        return True, None

    def rollback_operation(self, operation: FileOperation) -> bool:
        """
        Rollback a failed operation using backup

        Args:
            operation: FileOperation to rollback

        Returns:
            True if rollback successful, False otherwise
        """
        if not operation.backup_path:
            self.console.print("[yellow]⚠️  No backup available for rollback[/yellow]")
            return False

        try:
            return self._restore_from_backup(operation.backup_path, operation.file_path)
        except Exception as e:
            self.console.print(f"[red]❌ Rollback failed: {e}[/red]")
            return False

    def _create_backup(self, file_path: Path) -> Path:
        """Create a backup of the given file"""
        backup_path = file_path.with_suffix(file_path.suffix + ".backup")

        # If backup already exists, add timestamp
        if backup_path.exists():
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = file_path.with_suffix(f"{file_path.suffix}.backup.{timestamp}")

        shutil.copy2(file_path, backup_path)
        return backup_path

    def _restore_from_backup(self, backup_path: str, original_path: str) -> bool:
        """Restore a file from its backup"""
        try:
            shutil.copy2(backup_path, original_path)
            self.console.print(f"[green]✅ Restored from backup: {backup_path}[/green]")
            return True
        except Exception as e:
            self.console.print(f"[red]❌ Failed to restore from backup: {e}[/red]")
            return False

    def _print_batch_summary(self, result: BatchOperationResult):
        """Print summary of batch operation"""
        self.console.print("\n" + "=" * 50)
        self.console.print("[cyan]📊 Batch Operation Summary[/cyan]")
        self.console.print("=" * 50)
        self.console.print(f"Total operations: {result.total_operations}")
        self.console.print(f"[green]✅ Successful: {result.successful_operations}[/green]")
        if result.failed_operations > 0:
            self.console.print(f"[red]❌ Failed: {result.failed_operations}[/red]")
        self.console.print(f"Success rate: {result.success_rate:.1f}%")

        # Show failed operations details
        if result.failed_operations > 0:
            self.console.print("\n[yellow]Failed Operations:[/yellow]")
            for op in result.operations:
                if not op.success:
                    self.console.print(f"  • {op.file_path}: {op.error}")

        self.console.print("=" * 50 + "\n")

    def get_operation_history(self) -> List[FileOperation]:
        """Get history of all operations"""
        return self.operations_history.copy()

    def clear_history(self):
        """Clear operation history"""
        self.operations_history.clear()
