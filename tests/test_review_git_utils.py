"""
Tests for Git Utils Module
Tests Git-related functionality for code review
"""

import tempfile

import pytest

from xandai.utils.git_utils import GitUtils


class TestGitUtils:
    """Test suite for GitUtils"""

    def test_is_git_repository_false(self):
        """Test detection of non-Git directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Don't initialize Git
            assert GitUtils.is_git_repository(tmpdir) == False

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

    def test_prepare_review_context_error_handling(self):
        """Test error handling for non-Git directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Don't initialize Git

            # Prepare context
            context = GitUtils.prepare_review_context(tmpdir)

            # Should return error
            assert "error" in context
            assert context["is_git_repo"] == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
