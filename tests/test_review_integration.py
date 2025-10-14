"""
Integration Tests for Review Feature
Tests end-to-end review functionality with real Git repositories
"""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest

from xandai.core.app_state import AppState
from xandai.processors.review_processor import ReviewProcessor, ReviewResult
from xandai.utils.git_utils import GitUtils


class MockLLMProvider:
    """Mock LLM provider for integration testing"""

    def chat(self, messages, temperature=0.1, max_tokens=2048):
        class Response:
            content = """EXECUTIVE SUMMARY:
Integration test review completed successfully.

OVERALL SCORE: 7/10
Code analyzed with rule-based and AI analysis.

CRITICAL ISSUES:
• Security vulnerabilities detected

IMPROVEMENT SUGGESTIONS:
• Add error handling
• Improve test coverage

ARCHITECTURE & DESIGN:
• Good modular structure

SECURITY:
• Review input validation

PERFORMANCE:
• Performance is adequate

FILE-SPECIFIC COMMENTS:

test_file.py:
  - Line 1: Test comment
  - Overall: Integration test file

FINAL RECOMMENDATIONS:
• Continue with thorough testing
• Address security concerns"""
            model = "mock-integration"
            total_tokens = 300

        return Response()


class MockHistoryManager:
    """Mock history manager"""

    def add_conversation(self, **kwargs):
        pass

    def get_recent_conversation(self, **kwargs):
        return []


class TestReviewIntegration:
    """Integration tests for review feature"""

    def test_review_with_real_git_repo(self):
        """Test review with actual Git repository"""
        # Create temporary Git repository
        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize Git repo
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

            # Create a Python file with issues
            test_file = Path(tmpdir) / "test_file.py"
            test_file.write_text(
                """
import subprocess

# TODO: Fix this security issue
subprocess.run('ls -la', shell=True)

password = "hardcoded_secret"

def process_data():
    print("Debug output")
    # Missing error handling
    result = risky_operation()
    return result
"""
            )

            # Add and commit
            subprocess.run(["git", "add", "."], cwd=tmpdir, check=True, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", "Initial commit"],
                cwd=tmpdir,
                check=True,
                capture_output=True,
            )

            # Make changes
            test_file.write_text(test_file.read_text() + "\n# New change\n")

            # Run review
            llm = MockLLMProvider()
            history = MockHistoryManager()
            processor = ReviewProcessor(llm, history)
            app_state = AppState()

            result = processor.process(app_state, tmpdir)

            # Verify results
            assert isinstance(result, ReviewResult)
            assert result.code_quality_score > 0
            assert len(result.files_reviewed) > 0

    def test_review_detects_multiple_languages(self):
        """Test review with multiple programming languages"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize Git repo
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

            # Create Python file
            py_file = Path(tmpdir) / "script.py"
            py_file.write_text('print("test")\neval(user_input)')

            # Create JavaScript file
            js_file = Path(tmpdir) / "app.js"
            js_file.write_text("var x = 10;\nelement.innerHTML = data;")

            # Create TypeScript file
            ts_file = Path(tmpdir) / "types.ts"
            ts_file.write_text("function test(x: any): void {}")

            # Add and commit
            subprocess.run(["git", "add", "."], cwd=tmpdir, check=True, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", "Multi-language files"],
                cwd=tmpdir,
                check=True,
                capture_output=True,
            )

            # Make changes to all files (not committed yet)
            py_file.write_text(py_file.read_text() + "\n# Python change\n")
            js_file.write_text(js_file.read_text() + "\n// JS change\n")
            ts_file.write_text(ts_file.read_text() + "\n// TS change\n")

            # Run review
            llm = MockLLMProvider()
            history = MockHistoryManager()
            processor = ReviewProcessor(llm, history)
            app_state = AppState()

            result = processor.process(app_state, tmpdir)

            # Should detect changes in multiple files
            # Note: Git will only report files with uncommitted changes
            assert len(result.files_reviewed) >= 1, "Should process at least one file"
            # All three files were modified, so they should all be detected
            assert (
                len(result.files_reviewed) == 3
            ), f"Expected 3 files, got {len(result.files_reviewed)}: {result.files_reviewed}"

    def test_git_utils_integration(self):
        """Test GitUtils integration with ReviewProcessor"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize Git repo
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

            # Create and commit file
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text('print("initial")')
            subprocess.run(["git", "add", "."], cwd=tmpdir, check=True, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", "Initial"], cwd=tmpdir, check=True, capture_output=True
            )

            # Make changes
            test_file.write_text('print("modified")')

            # Test GitUtils directly
            git_context = GitUtils.prepare_review_context(tmpdir)

            assert git_context["is_git_repo"] == True
            assert len(git_context["changed_files"]) > 0
            assert "test.py" in git_context["changed_files"]
            assert len(git_context["code_files"]) > 0

    def test_review_with_no_changes(self):
        """Test review behavior with no changes"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize Git repo
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

            # Create and commit file
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text('print("test")')
            subprocess.run(["git", "add", "."], cwd=tmpdir, check=True, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", "Initial"], cwd=tmpdir, check=True, capture_output=True
            )

            # No changes - run review
            llm = MockLLMProvider()
            history = MockHistoryManager()
            processor = ReviewProcessor(llm, history)
            app_state = AppState()

            result = processor.process(app_state, tmpdir)

            # Should handle no changes gracefully
            assert isinstance(result, ReviewResult)
            assert len(result.files_reviewed) == 0

    def test_review_with_non_git_directory(self):
        """Test review with non-Git directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Don't initialize Git - just create file
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text('print("test")')

            # Run review
            llm = MockLLMProvider()
            history = MockHistoryManager()
            processor = ReviewProcessor(llm, history)
            app_state = AppState()

            result = processor.process(app_state, tmpdir)

            # Should handle error gracefully
            assert isinstance(result, ReviewResult)
            assert result.code_quality_score == 0
            assert len(result.key_issues) > 0
            assert "git" in result.summary.lower() or "repository" in result.summary.lower()


class TestEndToEndReview:
    """End-to-end tests for complete review workflow"""

    def test_complete_review_workflow(self):
        """Test complete review workflow from Git changes to result"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup Git repository
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

            # Create initial file
            test_file = Path(tmpdir) / "app.py"
            initial_content = """
def calculate(x, y):
    return x + y

if __name__ == '__main__':
    print(calculate(5, 3))
"""
            test_file.write_text(initial_content)

            subprocess.run(["git", "add", "."], cwd=tmpdir, check=True, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", "Initial version"],
                cwd=tmpdir,
                check=True,
                capture_output=True,
            )

            # Make changes with various issues
            modified_content = """
import subprocess

def calculate(x, y):
    # TODO: Add input validation
    return x + y

def dangerous_operation(command):
    # Security issue: shell injection
    subprocess.run(command, shell=True)
    password = "secret123"  # Hardcoded secret

if __name__ == '__main__':
    print(calculate(5, 3))
    console.log('test')  # Wrong language
"""
            test_file.write_text(modified_content)

            # Run review
            llm = MockLLMProvider()
            history = MockHistoryManager()
            processor = ReviewProcessor(llm, history)
            app_state = AppState()

            result = processor.process(app_state, tmpdir)

            # Comprehensive verification
            assert isinstance(result, ReviewResult)
            assert result.code_quality_score > 0
            assert len(result.files_reviewed) > 0
            assert len(result.key_issues) + len(result.suggestions) > 0

            # Check that result has meaningful content
            assert len(result.summary) > 20
            assert result.total_lines_reviewed > 0
            assert result.review_time_estimate is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
