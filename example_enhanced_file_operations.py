#!/usr/bin/env python3
"""
XandAI - Enhanced File Operations Demo
Demonstration of the new file operations capabilities
"""

import os
import tempfile
from pathlib import Path

from rich.console import Console

from xandai.utils.file_operations import FileOperationsManager


def demo_single_file_creation():
    """Demo: Create a single file"""
    console = Console()
    console.print("\n[bold cyan]Demo 1: Single File Creation[/bold cyan]")
    console.print("=" * 60)

    file_ops = FileOperationsManager(console=console)

    # Create a temporary directory for demo
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "hello.py")

        content = """#!/usr/bin/env python3
\"\"\"Hello World Example\"\"\"

def main():
    print("Hello, World!")

if __name__ == "__main__":
    main()
"""

        operation = file_ops.create_file(
            file_path=file_path, content=content, overwrite=False, interactive=False
        )

        if operation.success:
            console.print(f"[green]✅ Demo 1 Success: File created at {file_path}[/green]")
        else:
            console.print(f"[red]❌ Demo 1 Failed: {operation.error}[/red]")


def demo_file_update_with_backup():
    """Demo: Update a file with automatic backup"""
    console = Console()
    console.print("\n[bold cyan]Demo 2: File Update with Backup[/bold cyan]")
    console.print("=" * 60)

    file_ops = FileOperationsManager(console=console, create_backups=True)

    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "calculator.py")

        # Create initial file
        original_content = """def add(a, b):
    return a + b
"""
        file_ops.create_file(file_path, original_content, interactive=False)

        # Update with new content
        updated_content = """def add(a, b):
    \"\"\"Add two numbers\"\"\"
    return a + b

def subtract(a, b):
    \"\"\"Subtract b from a\"\"\"
    return a - b
"""

        operation = file_ops.update_file(file_path, updated_content, interactive=False)

        if operation.success:
            console.print(f"[green]✅ Demo 2 Success: File updated[/green]")
            console.print(f"[dim]Backup created at: {operation.backup_path}[/dim]")
        else:
            console.print(f"[red]❌ Demo 2 Failed: {operation.error}[/red]")


def demo_batch_file_creation():
    """Demo: Create multiple files at once"""
    console = Console()
    console.print("\n[bold cyan]Demo 3: Batch File Creation[/bold cyan]")
    console.print("=" * 60)

    file_ops = FileOperationsManager(console=console)

    with tempfile.TemporaryDirectory() as temp_dir:
        files = {
            os.path.join(temp_dir, "project", "__init__.py"): '"""Project Package"""',
            os.path.join(
                temp_dir, "project", "main.py"
            ): """#!/usr/bin/env python3
def main():
    print("Main function")

if __name__ == "__main__":
    main()
""",
            os.path.join(
                temp_dir, "project", "utils.py"
            ): """def helper():
    \"\"\"Helper function\"\"\"
    pass
""",
            os.path.join(
                temp_dir, "README.md"
            ): """# Demo Project

This is a demo project created by XandAI Enhanced File Operations.

## Features
- Multiple file creation
- Automatic directory creation
- Batch operations
""",
        }

        result = file_ops.batch_create_files(files, overwrite=False, interactive=False)

        console.print(f"\n[cyan]Batch Operation Results:[/cyan]")
        console.print(f"  Total: {result.total_operations}")
        console.print(f"  [green]✅ Success: {result.successful_operations}[/green]")
        console.print(f"  Success Rate: {result.success_rate:.1f}%")


def demo_validation():
    """Demo: Code validation before writing"""
    console = Console()
    console.print("\n[bold cyan]Demo 4: Code Validation[/bold cyan]")
    console.print("=" * 60)

    file_ops = FileOperationsManager(console=console)

    # Test valid Python code
    valid_code = """def hello():
    print("Hello")
"""
    is_valid, error = file_ops.validate_file_content(valid_code, "test.py")
    console.print(f"Valid Python code: [green]✅ {is_valid}[/green]")

    # Test invalid Python code
    invalid_code = """def hello(
    print("Missing closing parenthesis")
"""
    is_valid, error = file_ops.validate_file_content(invalid_code, "test.py")
    console.print(f"Invalid Python code: [red]❌ {is_valid}[/red]")
    if error:
        console.print(f"[dim]Error: {error}[/dim]")

    # Test valid JSON
    valid_json = '{"name": "test", "value": 123}'
    is_valid, error = file_ops.validate_file_content(valid_json, "test.json")
    console.print(f"Valid JSON: [green]✅ {is_valid}[/green]")

    # Test invalid JSON
    invalid_json = '{"name": "test", "value": }'
    is_valid, error = file_ops.validate_file_content(invalid_json, "test.json")
    console.print(f"Invalid JSON: [red]❌ {is_valid}[/red]")
    if error:
        console.print(f"[dim]Error: {error}[/dim]")


def demo_rollback():
    """Demo: Rollback after failed operation"""
    console = Console()
    console.print("\n[bold cyan]Demo 5: Rollback Operation[/bold cyan]")
    console.print("=" * 60)

    file_ops = FileOperationsManager(console=console, create_backups=True)

    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "app.py")

        # Create initial file
        original_content = "print('Original version')"
        file_ops.create_file(file_path, original_content, interactive=False)

        # Update file (this creates a backup)
        updated_content = "print('Updated version')"
        operation = file_ops.update_file(file_path, updated_content, interactive=False)

        console.print("[green]✅ File updated[/green]")

        # Read current content
        with open(file_path, "r") as f:
            current_content = f.read()
        console.print(f"[dim]Current content: {current_content.strip()}[/dim]")

        # Rollback to original
        if file_ops.rollback_operation(operation):
            console.print("[green]✅ Rollback successful[/green]")

            # Read content after rollback
            with open(file_path, "r") as f:
                restored_content = f.read()
            console.print(f"[dim]Restored content: {restored_content.strip()}[/dim]")
        else:
            console.print("[red]❌ Rollback failed[/red]")


def demo_operation_history():
    """Demo: Track operation history"""
    console = Console()
    console.print("\n[bold cyan]Demo 6: Operation History[/bold cyan]")
    console.print("=" * 60)

    file_ops = FileOperationsManager(console=console)

    with tempfile.TemporaryDirectory() as temp_dir:
        # Perform several operations
        file1 = os.path.join(temp_dir, "file1.txt")
        file2 = os.path.join(temp_dir, "file2.txt")

        file_ops.create_file(file1, "Content 1", interactive=False)
        file_ops.create_file(file2, "Content 2", interactive=False)
        file_ops.update_file(file1, "Updated Content 1", interactive=False)

        # Get history
        history = file_ops.get_operation_history()

        console.print(f"\n[cyan]Operation History ({len(history)} operations):[/cyan]")
        for i, op in enumerate(history, 1):
            status = "✅" if op.success else "❌"
            console.print(f"  {i}. {status} [{op.operation_type}] {op.file_path}")


def main():
    """Run all demos"""
    console = Console()

    console.print("\n" + "=" * 60)
    console.print("[bold green]XandAI Enhanced File Operations - Demo Suite[/bold green]")
    console.print("=" * 60)

    try:
        demo_single_file_creation()
        demo_file_update_with_backup()
        demo_batch_file_creation()
        demo_validation()
        demo_rollback()
        demo_operation_history()

        console.print("\n" + "=" * 60)
        console.print("[bold green]✅ All Demos Completed Successfully![/bold green]")
        console.print("=" * 60)
        console.print("\n[cyan]💡 Tip:[/cyan] Check out the following files for more information:")
        console.print("  • README_FILE_OPERATIONS.md - Quick start guide")
        console.print("  • ENHANCED_FILE_OPERATIONS.md - Detailed documentation")
        console.print("  • IMPROVEMENTS_SUMMARY.md - Executive summary")
        console.print("\n")

    except Exception as e:
        console.print(f"\n[red]❌ Demo failed with error: {e}[/red]")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
