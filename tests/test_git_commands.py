"""
Test Git Commands

Tests for AI-powered Git operations
"""

import os
from unittest.mock import MagicMock, Mock, patch

import pytest

from xandai.git.git_commands import GitCommands


class TestGitCommandsBasic:
    """Test basic Git commands functionality"""

    def test_git_commands_import(self):
        """Test that GitCommands can be imported"""
        from xandai.git import GitCommands as GC

        assert GC is not None

    def test_git_commands_init(self):
        """Test GitCommands initialization"""
        mock_llm = Mock()
        git_commands = GitCommands(mock_llm, verbose=False)

        assert git_commands.llm_provider == mock_llm
        assert git_commands.verbose == False

    def test_is_git_repo_false(self):
        """Test _is_git_repo returns False for non-repo"""
        mock_llm = Mock()
        git_commands = GitCommands(mock_llm)

        # Test with a non-existent path
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=1)
            result = git_commands._is_git_repo("/nonexistent/path")
            assert result == False

    def test_is_git_repo_true(self):
        """Test _is_git_repo returns True for valid repo"""
        mock_llm = Mock()
        git_commands = GitCommands(mock_llm)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            result = git_commands._is_git_repo(".")
            assert result == True


class TestCommitMessageGeneration:
    """Test commit message generation"""

    def test_generate_commit_no_repo(self):
        """Test error when not in a Git repo"""
        mock_llm = Mock()
        git_commands = GitCommands(mock_llm)

        with patch.object(git_commands, "_is_git_repo", return_value=False):
            with pytest.raises(ValueError, match="Not a Git repository"):
                git_commands.generate_commit_message()

    def test_generate_commit_no_changes(self):
        """Test error when no staged changes"""
        mock_llm = Mock()
        git_commands = GitCommands(mock_llm)

        with patch.object(git_commands, "_is_git_repo", return_value=True):
            with patch.object(git_commands, "_get_staged_diff", return_value=""):
                with pytest.raises(ValueError, match="No staged changes"):
                    git_commands.generate_commit_message()

    def test_generate_commit_success(self):
        """Test successful commit message generation"""
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "feat: Add new feature\n\nDetailed description"
        mock_llm.generate.return_value = mock_response

        git_commands = GitCommands(mock_llm)

        with patch.object(git_commands, "_is_git_repo", return_value=True):
            with patch.object(
                git_commands, "_get_staged_diff", return_value="diff --git a/file.py"
            ):
                with patch.object(git_commands, "_get_git_status", return_value="M file.py"):
                    message = git_commands.generate_commit_message()

                    assert message == "feat: Add new feature\n\nDetailed description"
                    assert mock_llm.generate.called


class TestPRSummarization:
    """Test PR summarization"""

    def test_summarize_pr_no_repo(self):
        """Test error when not in a Git repo"""
        mock_llm = Mock()
        git_commands = GitCommands(mock_llm)

        with patch.object(git_commands, "_is_git_repo", return_value=False):
            with pytest.raises(ValueError, match="Not a Git repository"):
                git_commands.summarize_pr()

    def test_summarize_pr_no_diff(self):
        """Test error when no differences"""
        mock_llm = Mock()
        git_commands = GitCommands(mock_llm)

        with patch.object(git_commands, "_is_git_repo", return_value=True):
            with patch.object(git_commands, "_get_current_branch", return_value="feature"):
                with patch.object(git_commands, "_get_branch_diff", return_value=""):
                    with pytest.raises(ValueError, match="No differences"):
                        git_commands.summarize_pr()

    def test_summarize_pr_success(self):
        """Test successful PR summarization"""
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = """SUMMARY:
This PR adds a new feature

CHANGES:
- Added new function
- Updated tests

RISKS:
- May break existing API"""
        mock_llm.generate.return_value = mock_response

        git_commands = GitCommands(mock_llm)

        with patch.object(git_commands, "_is_git_repo", return_value=True):
            with patch.object(git_commands, "_get_current_branch", return_value="feature"):
                with patch.object(git_commands, "_get_branch_diff", return_value="diff content"):
                    with patch.object(git_commands, "_get_commit_log", return_value="commit log"):
                        summary = git_commands.summarize_pr()

                        assert "summary" in summary
                        assert "changes" in summary
                        assert "risks" in summary
                        assert "new feature" in summary["summary"].lower()


class TestDiffExplanation:
    """Test diff explanation"""

    def test_explain_diff_no_repo(self):
        """Test error when not in a Git repo"""
        mock_llm = Mock()
        git_commands = GitCommands(mock_llm)

        with patch.object(git_commands, "_is_git_repo", return_value=False):
            with pytest.raises(ValueError, match="Not a Git repository"):
                git_commands.explain_diff()

    def test_explain_diff_no_changes(self):
        """Test error when no changes"""
        mock_llm = Mock()
        git_commands = GitCommands(mock_llm)

        with patch.object(git_commands, "_is_git_repo", return_value=True):
            with patch.object(git_commands, "_get_working_diff", return_value=""):
                with pytest.raises(ValueError, match="No changes found"):
                    git_commands.explain_diff()

    def test_explain_diff_success(self):
        """Test successful diff explanation"""
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "This change adds error handling to the function"
        mock_llm.generate.return_value = mock_response

        git_commands = GitCommands(mock_llm)

        with patch.object(git_commands, "_is_git_repo", return_value=True):
            with patch.object(git_commands, "_get_working_diff", return_value="diff content"):
                explanation = git_commands.explain_diff()

                assert explanation == "This change adds error handling to the function"
                assert mock_llm.generate.called


class TestBlameExplanation:
    """Test blame explanation"""

    def test_explain_blame_no_file(self):
        """Test error when file not provided"""
        mock_llm = Mock()
        git_commands = GitCommands(mock_llm)

        with pytest.raises(ValueError, match="file_path is required"):
            git_commands.explain_blame()

    def test_explain_blame_no_repo(self):
        """Test error when not in a Git repo"""
        mock_llm = Mock()
        git_commands = GitCommands(mock_llm)

        with patch.object(git_commands, "_is_git_repo", return_value=False):
            with pytest.raises(ValueError, match="Not a Git repository"):
                git_commands.explain_blame(file_path="test.py")

    def test_explain_blame_success(self):
        """Test successful blame explanation"""
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "This line was added to fix a bug in the authentication flow"
        mock_llm.generate.return_value = mock_response

        git_commands = GitCommands(mock_llm)

        blame_info = {
            "commit": "abc123",
            "line_content": "if user.is_authenticated():",
            "line_number": 42,
        }

        commit_details = {
            "hash": "abc123",
            "author": "John Doe",
            "timestamp": "1234567890",
            "subject": "Fix authentication bug",
            "body": "Added proper authentication check",
        }

        with patch.object(git_commands, "_is_git_repo", return_value=True):
            with patch.object(git_commands, "_get_blame_info", return_value=blame_info):
                with patch.object(git_commands, "_get_commit_details", return_value=commit_details):
                    explanation = git_commands.explain_blame(file_path="test.py", line_number=42)

                    assert "authentication" in explanation.lower()
                    assert mock_llm.generate.called


class TestHelperMethods:
    """Test helper methods"""

    def test_parse_pr_summary(self):
        """Test PR summary parsing"""
        mock_llm = Mock()
        git_commands = GitCommands(mock_llm)

        content = """SUMMARY:
This is a summary

CHANGES:
- Change 1
- Change 2

RISKS:
- Risk 1"""

        result = git_commands._parse_pr_summary(content)

        assert result["summary"] == "This is a summary"
        assert "Change 1" in result["changes"]
        assert "Risk 1" in result["risks"]

    def test_build_commit_prompt(self):
        """Test commit prompt building"""
        mock_llm = Mock()
        git_commands = GitCommands(mock_llm)

        prompt = git_commands._build_commit_prompt("diff content", "status")

        assert "commit message" in prompt.lower()
        assert "diff content" in prompt
        assert "status" in prompt

    def test_build_pr_prompt(self):
        """Test PR prompt building"""
        mock_llm = Mock()
        git_commands = GitCommands(mock_llm)

        prompt = git_commands._build_pr_prompt("diff", "commits", "main", "feature")

        assert "pull request" in prompt.lower()
        assert "main" in prompt
        assert "feature" in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
