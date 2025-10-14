#!/usr/bin/env python3
"""
Tests for Enhanced File Operations Module
Tests file creation, updates, and batch operations
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from xandai.utils.file_operations import BatchOperationResult, FileOperation, FileOperationsManager


class TestFileOperationsManager(unittest.TestCase):
    """Test suite for FileOperationsManager"""

    def setUp(self):
        """Set up test environment"""
        # Create a temporary directory for tests
        self.test_dir = tempfile.mkdtemp()
        self.file_manager = FileOperationsManager(create_backups=True)

    def tearDown(self):
        """Clean up test environment"""
        # Remove temporary directory and all its contents
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_create_file_success(self):
        """Test successful file creation"""
        file_path = os.path.join(self.test_dir, "test.txt")
        content = "Hello, World!"

        operation = self.file_manager.create_file(
            file_path, content, overwrite=False, interactive=False
        )

        self.assertTrue(operation.success)
        self.assertIsNone(operation.error)
        self.assertTrue(os.path.exists(file_path))

        with open(file_path, "r") as f:
            self.assertEqual(f.read(), content)

    def test_create_file_with_subdirectory(self):
        """Test file creation in a subdirectory"""
        file_path = os.path.join(self.test_dir, "subdir", "test.txt")
        content = "Nested file"

        operation = self.file_manager.create_file(
            file_path, content, overwrite=False, interactive=False
        )

        self.assertTrue(operation.success)
        self.assertTrue(os.path.exists(file_path))

    def test_create_file_overwrite_existing(self):
        """Test overwriting an existing file"""
        file_path = os.path.join(self.test_dir, "test.txt")

        # Create initial file
        self.file_manager.create_file(file_path, "Original", interactive=False)

        # Overwrite with new content
        operation = self.file_manager.create_file(
            file_path, "Updated", overwrite=True, interactive=False
        )

        self.assertTrue(operation.success)
        with open(file_path, "r") as f:
            self.assertEqual(f.read(), "Updated")

    def test_create_file_no_overwrite(self):
        """Test that file is not overwritten when overwrite=False"""
        file_path = os.path.join(self.test_dir, "test.txt")

        # Create initial file
        self.file_manager.create_file(file_path, "Original", interactive=False)

        # Try to create again without overwrite
        operation = self.file_manager.create_file(
            file_path, "Updated", overwrite=False, interactive=False
        )

        self.assertFalse(operation.success)
        self.assertIsNotNone(operation.error)

        # Original content should be preserved
        with open(file_path, "r") as f:
            self.assertEqual(f.read(), "Original")

    def test_update_file_success(self):
        """Test successful file update"""
        file_path = os.path.join(self.test_dir, "test.txt")

        # Create initial file
        self.file_manager.create_file(file_path, "Original", interactive=False)

        # Update the file
        operation = self.file_manager.update_file(
            file_path, "Updated", create_if_missing=False, interactive=False
        )

        self.assertTrue(operation.success)
        self.assertIsNotNone(operation.backup_path)

        # Check updated content
        with open(file_path, "r") as f:
            self.assertEqual(f.read(), "Updated")

        # Verify backup exists
        self.assertTrue(os.path.exists(operation.backup_path))

    def test_update_file_creates_backup(self):
        """Test that file update creates a backup"""
        file_path = os.path.join(self.test_dir, "test.txt")
        original_content = "Original Content"

        # Create initial file
        self.file_manager.create_file(file_path, original_content, interactive=False)

        # Update the file
        operation = self.file_manager.update_file(file_path, "Updated", interactive=False)

        self.assertTrue(operation.success)
        self.assertIsNotNone(operation.backup_path)

        # Verify backup contains original content
        with open(operation.backup_path, "r") as f:
            self.assertEqual(f.read(), original_content)

    def test_update_nonexistent_file_creates_it(self):
        """Test that updating a non-existent file creates it when create_if_missing=True"""
        file_path = os.path.join(self.test_dir, "new_file.txt")
        content = "New Content"

        operation = self.file_manager.update_file(
            file_path, content, create_if_missing=True, interactive=False
        )

        self.assertTrue(operation.success)
        self.assertTrue(os.path.exists(file_path))

        with open(file_path, "r") as f:
            self.assertEqual(f.read(), content)

    def test_update_nonexistent_file_fails_when_create_false(self):
        """Test that updating a non-existent file fails when create_if_missing=False"""
        file_path = os.path.join(self.test_dir, "nonexistent.txt")

        operation = self.file_manager.update_file(
            file_path, "Content", create_if_missing=False, interactive=False
        )

        self.assertFalse(operation.success)
        self.assertIsNotNone(operation.error)
        self.assertFalse(os.path.exists(file_path))

    def test_batch_create_files_success(self):
        """Test batch file creation"""
        files = {
            os.path.join(self.test_dir, "file1.txt"): "Content 1",
            os.path.join(self.test_dir, "file2.txt"): "Content 2",
            os.path.join(self.test_dir, "subdir", "file3.txt"): "Content 3",
        }

        result = self.file_manager.batch_create_files(files, overwrite=False, interactive=False)

        self.assertEqual(result.total_operations, 3)
        self.assertEqual(result.successful_operations, 3)
        self.assertEqual(result.failed_operations, 0)
        self.assertEqual(result.success_rate, 100.0)

        # Verify all files exist with correct content
        for file_path, expected_content in files.items():
            self.assertTrue(os.path.exists(file_path))
            with open(file_path, "r") as f:
                self.assertEqual(f.read(), expected_content)

    def test_batch_create_files_partial_failure(self):
        """Test batch file creation with some failures"""
        # Create one file first
        existing_file = os.path.join(self.test_dir, "existing.txt")
        with open(existing_file, "w") as f:
            f.write("Existing")

        files = {
            existing_file: "New Content",  # This will fail without overwrite
            os.path.join(self.test_dir, "new_file.txt"): "New Content",
        }

        result = self.file_manager.batch_create_files(files, overwrite=False, interactive=False)

        self.assertEqual(result.total_operations, 2)
        self.assertEqual(result.successful_operations, 1)
        self.assertEqual(result.failed_operations, 1)
        self.assertEqual(result.success_rate, 50.0)

    def test_batch_update_files_success(self):
        """Test batch file update"""
        # Create initial files
        files = {
            os.path.join(self.test_dir, "file1.txt"): "Original 1",
            os.path.join(self.test_dir, "file2.txt"): "Original 2",
        }

        for file_path, content in files.items():
            self.file_manager.create_file(file_path, content, interactive=False)

        # Update all files
        updates = {
            os.path.join(self.test_dir, "file1.txt"): "Updated 1",
            os.path.join(self.test_dir, "file2.txt"): "Updated 2",
        }

        result = self.file_manager.batch_update_files(
            updates, create_if_missing=False, interactive=False
        )

        self.assertEqual(result.total_operations, 2)
        self.assertEqual(result.successful_operations, 2)
        self.assertEqual(result.failed_operations, 0)

        # Verify updates
        for file_path, expected_content in updates.items():
            with open(file_path, "r") as f:
                self.assertEqual(f.read(), expected_content)

    def test_validate_file_content_python(self):
        """Test Python file content validation"""
        # Valid Python code
        valid_code = "def hello():\n    print('Hello, World!')\n"
        is_valid, error = self.file_manager.validate_file_content(valid_code, "test.py")
        self.assertTrue(is_valid)
        self.assertIsNone(error)

        # Invalid Python code
        invalid_code = "def hello(\n    print('Missing closing parenthesis')\n"
        is_valid, error = self.file_manager.validate_file_content(invalid_code, "test.py")
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)

    def test_validate_file_content_json(self):
        """Test JSON file content validation"""
        # Valid JSON
        valid_json = '{"name": "test", "value": 123}'
        is_valid, error = self.file_manager.validate_file_content(valid_json, "test.json")
        self.assertTrue(is_valid)
        self.assertIsNone(error)

        # Invalid JSON
        invalid_json = '{"name": "test", "value": }'
        is_valid, error = self.file_manager.validate_file_content(invalid_json, "test.json")
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)

    def test_validate_file_content_empty(self):
        """Test validation of empty content"""
        is_valid, error = self.file_manager.validate_file_content("", "test.txt")
        self.assertFalse(is_valid)
        self.assertEqual(error, "Content is empty")

    def test_rollback_operation(self):
        """Test operation rollback"""
        file_path = os.path.join(self.test_dir, "test.txt")
        original_content = "Original"
        updated_content = "Updated"

        # Create and update file
        self.file_manager.create_file(file_path, original_content, interactive=False)
        operation = self.file_manager.update_file(file_path, updated_content, interactive=False)

        # Rollback
        success = self.file_manager.rollback_operation(operation)
        self.assertTrue(success)

        # Verify rollback restored original content
        with open(file_path, "r") as f:
            self.assertEqual(f.read(), original_content)

    def test_operation_history(self):
        """Test operation history tracking"""
        file_path1 = os.path.join(self.test_dir, "file1.txt")
        file_path2 = os.path.join(self.test_dir, "file2.txt")

        # Perform multiple operations
        self.file_manager.create_file(file_path1, "Content 1", interactive=False)
        self.file_manager.create_file(file_path2, "Content 2", interactive=False)
        self.file_manager.update_file(file_path1, "Updated 1", interactive=False)

        # Check history
        history = self.file_manager.get_operation_history()
        self.assertEqual(len(history), 3)
        self.assertEqual(history[0].operation_type, "create")
        self.assertEqual(history[1].operation_type, "create")
        self.assertEqual(history[2].operation_type, "update")

        # Clear history
        self.file_manager.clear_history()
        self.assertEqual(len(self.file_manager.get_operation_history()), 0)


class TestFileOperationDataClasses(unittest.TestCase):
    """Test data classes for file operations"""

    def test_file_operation_creation(self):
        """Test FileOperation creation"""
        op = FileOperation(
            operation_type="create", file_path="/path/to/file.txt", content="Test content"
        )

        self.assertEqual(op.operation_type, "create")
        self.assertEqual(op.file_path, "/path/to/file.txt")
        self.assertEqual(op.content, "Test content")
        self.assertFalse(op.success)
        self.assertIsNone(op.error)
        self.assertIsNone(op.backup_path)

    def test_batch_operation_result_success_rate(self):
        """Test BatchOperationResult success rate calculation"""
        # 100% success
        result = BatchOperationResult(
            total_operations=5, successful_operations=5, failed_operations=0, operations=[]
        )
        self.assertEqual(result.success_rate, 100.0)

        # 50% success
        result = BatchOperationResult(
            total_operations=4, successful_operations=2, failed_operations=2, operations=[]
        )
        self.assertEqual(result.success_rate, 50.0)

        # 0% success
        result = BatchOperationResult(
            total_operations=3, successful_operations=0, failed_operations=3, operations=[]
        )
        self.assertEqual(result.success_rate, 0.0)

        # No operations
        result = BatchOperationResult(
            total_operations=0, successful_operations=0, failed_operations=0, operations=[]
        )
        self.assertEqual(result.success_rate, 0.0)


if __name__ == "__main__":
    unittest.main()
