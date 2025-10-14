#!/usr/bin/env python3
"""
Final Integration Test for Enhanced File Operations
Tests the complete integration with ChatREPL
"""

import os
import tempfile

from rich.console import Console

from xandai.history import HistoryManager
from xandai.integrations.provider_factory import LLMProviderFactory
from xandai.utils.enhanced_file_handler import EnhancedFileHandler


def test_enhanced_file_handler_initialization():
    """Test that EnhancedFileHandler can be initialized properly"""
    console = Console()
    console.print("\n[bold cyan]Test 1: Initialize EnhancedFileHandler[/bold cyan]")

    try:
        # Mock LLM provider for testing
        llm_provider = LLMProviderFactory.create_provider("ollama")
        history_manager = HistoryManager()

        # Initialize enhanced file handler
        handler = EnhancedFileHandler(
            llm_provider=llm_provider, history_manager=history_manager, console=console
        )

        console.print("[green]✅ EnhancedFileHandler initialized successfully[/green]")
        return True
    except Exception as e:
        console.print(f"[red]❌ Failed to initialize: {e}[/red]")
        return False


def test_file_operations_manager():
    """Test that FileOperationsManager works correctly"""
    console = Console()
    console.print("\n[bold cyan]Test 2: FileOperationsManager Operations[/bold cyan]")

    try:
        llm_provider = LLMProviderFactory.create_provider("ollama")
        history_manager = HistoryManager()
        handler = EnhancedFileHandler(
            llm_provider=llm_provider, history_manager=history_manager, console=console
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            # Test file creation
            file_path = os.path.join(temp_dir, "test.py")
            content = "print('Hello, World!')"

            operation = handler.file_ops.create_file(
                file_path=file_path, content=content, overwrite=False, interactive=False
            )

            if not operation.success:
                console.print(f"[red]❌ File creation failed: {operation.error}[/red]")
                return False

            console.print(f"[green]✅ File created: {file_path}[/green]")

            # Test file update
            new_content = "print('Hello, Updated World!')"
            operation = handler.file_ops.update_file(
                file_path=file_path,
                content=new_content,
                create_if_missing=False,
                interactive=False,
            )

            if not operation.success:
                console.print(f"[red]❌ File update failed: {operation.error}[/red]")
                return False

            console.print(f"[green]✅ File updated with backup: {operation.backup_path}[/green]")

        console.print("[green]✅ All file operations successful[/green]")
        return True

    except Exception as e:
        console.print(f"[red]❌ Test failed: {e}[/red]")
        import traceback

        traceback.print_exc()
        return False


def test_detection_of_file_operations():
    """Test detection of file operations in AI response"""
    console = Console()
    console.print("\n[bold cyan]Test 3: Detect File Operations in AI Response[/bold cyan]")

    try:
        llm_provider = LLMProviderFactory.create_provider("ollama")
        history_manager = HistoryManager()
        handler = EnhancedFileHandler(
            llm_provider=llm_provider, history_manager=history_manager, console=console
        )

        # Simulate AI response with file operations
        ai_response = """
Here's the solution:

<code edit filename="hello.py">
print("Hello, World!")
</code>

<code edit filename="utils.py">
def helper():
    pass
</code>
"""

        operations = handler.detect_file_operations_in_response(ai_response)

        if len(operations) != 2:
            console.print(f"[red]❌ Expected 2 operations, got {len(operations)}[/red]")
            return False

        console.print(f"[green]✅ Detected {len(operations)} file operations[/green]")
        for op_type, filename, content in operations:
            console.print(f"  • [{op_type}] {filename}")

        return True

    except Exception as e:
        console.print(f"[red]❌ Test failed: {e}[/red]")
        return False


def test_batch_file_creation():
    """Test batch file creation"""
    console = Console()
    console.print("\n[bold cyan]Test 4: Batch File Creation[/bold cyan]")

    try:
        llm_provider = LLMProviderFactory.create_provider("ollama")
        history_manager = HistoryManager()
        handler = EnhancedFileHandler(
            llm_provider=llm_provider, history_manager=history_manager, console=console
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            files = {
                os.path.join(temp_dir, "file1.py"): "print('File 1')",
                os.path.join(temp_dir, "file2.py"): "print('File 2')",
                os.path.join(temp_dir, "file3.py"): "print('File 3')",
            }

            results = handler.create_multiple_files(files, interactive=False)

            success_count = sum(1 for success in results.values() if success)

            if success_count != len(files):
                console.print(
                    f"[red]❌ Expected {len(files)} successful, got {success_count}[/red]"
                )
                return False

            console.print(f"[green]✅ Created {success_count}/{len(files)} files[/green]")
            return True

    except Exception as e:
        console.print(f"[red]❌ Test failed: {e}[/red]")
        return False


def test_code_validation():
    """Test code validation"""
    console = Console()
    console.print("\n[bold cyan]Test 5: Code Validation[/bold cyan]")

    try:
        llm_provider = LLMProviderFactory.create_provider("ollama")
        history_manager = HistoryManager()
        handler = EnhancedFileHandler(
            llm_provider=llm_provider, history_manager=history_manager, console=console
        )

        # Valid Python code
        valid_code = "print('Hello')"
        is_valid, error = handler.validate_and_fix_code("test.py", valid_code)

        if not is_valid:
            console.print(f"[red]❌ Valid code marked as invalid: {error}[/red]")
            return False

        console.print("[green]✅ Valid code validated successfully[/green]")

        # Invalid Python code
        invalid_code = "print('Missing closing quote)"
        is_valid, error = handler.validate_and_fix_code("test.py", invalid_code)

        if is_valid:
            console.print("[red]❌ Invalid code marked as valid[/red]")
            return False

        console.print(f"[green]✅ Invalid code detected: {error}[/green]")
        return True

    except Exception as e:
        console.print(f"[red]❌ Test failed: {e}[/red]")
        return False


def main():
    """Run all integration tests"""
    console = Console()

    console.print("\n" + "=" * 70)
    console.print("[bold green]Enhanced File Operations - Final Integration Test[/bold green]")
    console.print("=" * 70)

    tests = [
        ("Initialize Handler", test_enhanced_file_handler_initialization),
        ("File Operations", test_file_operations_manager),
        ("Detect Operations", test_detection_of_file_operations),
        ("Batch Creation", test_batch_file_creation),
        ("Code Validation", test_code_validation),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            console.print(f"[red]❌ {test_name} crashed: {e}[/red]")
            results.append((test_name, False))

    # Summary
    console.print("\n" + "=" * 70)
    console.print("[bold cyan]Test Summary[/bold cyan]")
    console.print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        console.print(f"{status} - {test_name}")

    console.print("=" * 70)
    console.print(f"Results: [bold]{passed}/{total}[/bold] tests passed")

    if passed == total:
        console.print("[bold green]🎉 All tests passed! Integration complete![/bold green]")
        console.print("=" * 70)
        console.print("\n[cyan]✅ Enhanced File Operations is ready for production use![/cyan]\n")
    else:
        console.print(f"[bold red]❌ {total - passed} test(s) failed[/bold red]")
        console.print("=" * 70)

    return passed == total


if __name__ == "__main__":
    import sys

    success = main()
    sys.exit(0 if success else 1)
