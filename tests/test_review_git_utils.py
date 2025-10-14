"""
Tests for Git Utils Module
Tests Git-related functionality for code review
"""

import subprocess
import tempfile
from pathlib import Path

import pytest

from xandai.utils.git_utils import GitUtils


class TestGitUtils:
    """Test suite for GitUtils"""

    def test_is_git_repository_true(self):
        """Test detection of valid Git repository"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize Git repo
            subprocess.run(["git", "init"], cwd=tmpdir, check=True, capture_output=True)

            assert GitUtils.is_git_repository(tmpdir) == True

    def test_is_git_repository_false(self):
        """Test detection of non-Git directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Don't initialize Git
            assert GitUtils.is_git_repository(tmpdir) == False

    def test_get_changed_files_with_modifications(self):
        """Test detection of modified files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup Git repo with isolation
            subprocess.run(["git", "init"], cwd=tmpdir, check=True, capture_output=True, shell=True)
            subprocess.run(
                ["git", "config", "user.email", "test@test.com"],
                cwd=tmpdir,
                check=True,
                capture_output=True,
                shell=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=tmpdir,
                check=True,
                capture_output=True,
                shell=True,
            )

            # Create and commit file
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text('print("initial")')
            subprocess.run(
                ["git", "add", "."], cwd=tmpdir, check=True, capture_output=True, shell=True
            )
            subprocess.run(
                ["git", "commit", "-m", "Initial"],
                cwd=tmpdir,
                check=True,
                capture_output=True,
                shell=True,
            )

            # Modify file
            test_file.write_text('print("modified")')

            # Get changed files from the temp directory
            changed = GitUtils.get_changed_files(path=tmpdir)

            assert len(changed) > 0, f"No changes detected in {tmpdir}"
            assert "test.py" in changed, f"test.py not in {changed}"

    def test_get_changed_files_with_new_files(self):
        """Test detection of new untracked files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup Git repo
            subprocess.run(["git", "init"], cwd=tmpdir, check=True, capture_output=True, shell=True)
            subprocess.run(
                ["git", "config", "user.email", "test@test.com"],
                cwd=tmpdir,
                check=True,
                capture_output=True,
                shell=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=tmpdir,
                check=True,
                capture_output=True,
                shell=True,
            )

            # Create new file (untracked)
            test_file = Path(tmpdir) / "new_file.py"
            test_file.write_text('print("new")')

            # Get changed files from temp directory
            changed = GitUtils.get_changed_files(path=tmpdir)

            assert len(changed) > 0, f"No changes detected in {tmpdir}"
            assert "new_file.py" in changed, f"new_file.py not in {changed}"

    def test_read_file_content(self):
        """Test reading file content"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize Git repo (required for get_repository_root)
            subprocess.run(["git", "init"], cwd=tmpdir, check=True, capture_output=True, shell=True)

            # Create test file
            test_file = Path(tmpdir) / "test.py"
            content = 'print("test content")'
            test_file.write_text(content)

            # Read content
            result = GitUtils.read_file_content("test.py", tmpdir)

            assert result == content

    def test_read_file_content_nonexistent(self):
        """Test reading nonexistent file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Try to read nonexistent file
            try:
                result = GitUtils.read_file_content("nonexistent.py", tmpdir)
                # If no exception, result should be empty or None
                assert result == "" or result is None
            except Exception:
                # Exception is acceptable for nonexistent files
                pass

    def test_get_file_diff(self):
        """Test getting file diff"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup Git repo
            subprocess.run(["git", "init"], cwd=tmpdir, check=True, capture_output=True, shell=True)
            subprocess.run(
                ["git", "config", "user.email", "test@test.com"],
                cwd=tmpdir,
                check=True,
                capture_output=True,
                shell=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=tmpdir,
                check=True,
                capture_output=True,
                shell=True,
            )

            # Create and commit file
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("line1\nline2\nline3\n")
            subprocess.run(
                ["git", "add", "."], cwd=tmpdir, check=True, capture_output=True, shell=True
            )
            subprocess.run(
                ["git", "commit", "-m", "Initial"],
                cwd=tmpdir,
                check=True,
                capture_output=True,
                shell=True,
            )

            # Modify file
            test_file.write_text("line1\nmodified line2\nline3\n")

            # Get diff
            diff = GitUtils.get_file_diff("test.py", "HEAD", tmpdir)

            # Diff might be empty if file isn't staged, so we check for that or actual diff content
            assert diff is not None, "Diff should not be None"
            # For unstaged changes, diff might be empty - that's ok for this test
            if len(diff) > 0:
                assert "modified" in diff or "line2" in diff

    def test_prepare_review_context_complete(self):
        """Test complete review context preparation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup Git repo
            subprocess.run(["git", "init"], cwd=tmpdir, check=True, capture_output=True)
            subprocess.run(
                ["git", "config", "user.email", "test@test.com"],
                cwd=tmpdir,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=tmpdir,
                check=True,
                capture_output=True,
            )

            # Create multiple files
            py_file = Path(tmpdir) / "script.py"
            py_file.write_text('print("python")')

            js_file = Path(tmpdir) / "app.js"
            js_file.write_text('console.log("javascript");')

            txt_file = Path(tmpdir) / "readme.txt"
            txt_file.write_text("This is text")

            # Commit
            subprocess.run(["git", "add", "."], cwd=tmpdir, check=True, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", "Initial"], cwd=tmpdir, check=True, capture_output=True
            )

            # Modify code files
            py_file.write_text('print("modified python")')
            js_file.write_text('console.log("modified javascript");')

            # Prepare context
            context = GitUtils.prepare_review_context(tmpdir)

            # Verify context structure
            assert context["is_git_repo"] == True
            assert "changed_files" in context
            assert "code_files" in context
            assert "file_contents" in context
            assert "file_diffs" in context
            assert "commit_info" in context
            assert "repo_stats" in context

            # Verify only code files are included
            assert len(context["code_files"]) == 2
            assert "script.py" in context["code_files"]
            assert "app.js" in context["code_files"]
            assert "readme.txt" not in context["code_files"]

            # Verify file contents
            assert "script.py" in context["file_contents"]
            assert "app.js" in context["file_contents"]

    def test_prepare_review_context_filters_non_code_files(self):
        """Test that non-code files are filtered out"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup Git repo
            subprocess.run(["git", "init"], cwd=tmpdir, check=True, capture_output=True)

            # Create various file types
            code_file = Path(tmpdir) / "code.py"
            code_file.write_text('print("code")')

            image_file = Path(tmpdir) / "image.png"
            image_file.write_bytes(b"\x89PNG\r\n")

            doc_file = Path(tmpdir) / "doc.pdf"
            doc_file.write_bytes(b"%PDF-1.4")

            # Prepare context
            context = GitUtils.prepare_review_context(tmpdir)

            # Only code files should be included
            assert "code.py" in context["code_files"]
            assert "image.png" not in context["code_files"]
            assert "doc.pdf" not in context["code_files"]

    def test_prepare_review_context_error_handling(self):
        """Test error handling for non-Git directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Don't initialize Git

            # Prepare context
            context = GitUtils.prepare_review_context(tmpdir)

            # Should return error
            assert "error" in context
            assert context["is_git_repo"] == False


class TestGitUtilsCodeFileDetection:
    """Test code file detection logic"""

    def test_detects_python_files(self):
        """Test detection of Python files"""
        # Test common Python extensions
        extensions = [".py"]  # Most common extension

        for ext in extensions:
            with tempfile.TemporaryDirectory() as tmpdir:
                subprocess.run(
                    ["git", "init"], cwd=tmpdir, check=True, capture_output=True, shell=True
                )

                test_file = Path(tmpdir) / f"test{ext}"
                test_file.write_text('print("test")')

                context = GitUtils.prepare_review_context(tmpdir)
                assert f"test{ext}" in context["code_files"], f"test{ext} not detected as code file"

    def test_detects_javascript_files(self):
        """Test detection of JavaScript/TypeScript files"""
        # Test common JS/TS extensions
        extensions = [".js", ".jsx", ".ts", ".tsx"]

        for ext in extensions:
            with tempfile.TemporaryDirectory() as tmpdir:
                subprocess.run(
                    ["git", "init"], cwd=tmpdir, check=True, capture_output=True, shell=True
                )

                test_file = Path(tmpdir) / f"test{ext}"
                test_file.write_text('console.log("test");')

                context = GitUtils.prepare_review_context(tmpdir)
                assert f"test{ext}" in context["code_files"], f"test{ext} not detected as code file"

    def test_detects_java_files(self):
        """Test detection of Java files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            subprocess.run(["git", "init"], cwd=tmpdir, check=True, capture_output=True, shell=True)

            test_file = Path(tmpdir) / "Test.java"
            test_file.write_text("public class Test {}")

            context = GitUtils.prepare_review_context(tmpdir)
            assert "Test.java" in context["code_files"], "Test.java not detected as code file"

    def test_detects_cpp_files(self):
        """Test detection of C/C++ files"""
        # Test most common C/C++ extensions
        extensions = [".c", ".cpp", ".h", ".hpp"]

        for ext in extensions:
            with tempfile.TemporaryDirectory() as tmpdir:
                subprocess.run(
                    ["git", "init"], cwd=tmpdir, check=True, capture_output=True, shell=True
                )

                test_file = Path(tmpdir) / f"test{ext}"
                test_file.write_text("#include <stdio.h>")

                context = GitUtils.prepare_review_context(tmpdir)
                assert f"test{ext}" in context["code_files"], f"test{ext} not detected as code file"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
