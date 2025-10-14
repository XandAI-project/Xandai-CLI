"""
Tests for Review Processor
Tests the core code review processing functionality
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from xandai.core.app_state import AppState
from xandai.processors.review_processor import ReviewProcessor, ReviewResult


class MockLLMProvider:
    """Mock LLM provider for testing"""

    def __init__(self, response_content=None):
        self.response_content = response_content or self._default_response()
        self.call_count = 0

    def _default_response(self):
        return """EXECUTIVE SUMMARY:
Comprehensive code review completed with detailed analysis of all changes.

OVERALL SCORE: 8/10
Code quality is good with some areas for improvement.

CRITICAL ISSUES:
• test.py Line 15: Security vulnerability detected
• test.py Line 23: Potential memory leak

IMPROVEMENT SUGGESTIONS:
• Add comprehensive error handling
• Implement input validation
• Add unit tests

ARCHITECTURE & DESIGN:
• Good separation of concerns
• Clean interface design

SECURITY:
• Input validation needed
• Sanitize user inputs

PERFORMANCE:
• Consider caching for repeated operations
• Optimize database queries

FILE-SPECIFIC COMMENTS:

test.py:
  - Line 15: Security issue detected
    Code: `subprocess.run(cmd, shell=True)`
    Suggestion: Use shell=False with command list
  - Line 23: Missing error handling
    Code: `result = risky_operation()`
    Suggestion: Add try-except block
  - Overall: Well-structured code

FINAL RECOMMENDATIONS:
• Address security vulnerabilities immediately
• Add comprehensive test coverage
• Review error handling patterns"""

    def chat(self, messages, temperature=0.1, max_tokens=2048):
        self.call_count += 1

        class Response:
            def __init__(self, content):
                self.content = content
                self.model = "mock-model"
                self.total_tokens = 500

        return Response(self.response_content)


class MockHistoryManager:
    """Mock history manager for testing"""

    def __init__(self):
        self.messages = []

    def add_conversation(self, **kwargs):
        self.messages.append(kwargs)

    def get_recent_conversation(self, **kwargs):
        return []


class TestReviewProcessor:
    """Test suite for ReviewProcessor"""

    def test_processor_initialization(self):
        """Test that ReviewProcessor initializes correctly"""
        llm = MockLLMProvider()
        history = MockHistoryManager()

        processor = ReviewProcessor(llm, history)

        assert processor.llm_provider == llm
        assert processor.conversation_manager == history
        assert hasattr(processor, "system_prompt")

    def test_system_prompt_structure(self):
        """Test that system prompt has required structure"""
        llm = MockLLMProvider()
        history = MockHistoryManager()
        processor = ReviewProcessor(llm, history)

        prompt = processor.system_prompt

        # Check for key sections
        assert "EXECUTIVE SUMMARY:" in prompt
        assert "FILE-SPECIFIC COMMENTS:" in prompt
        assert "OVERALL SCORE:" in prompt
        assert "CRITICAL ISSUES:" in prompt
        assert "Code:" in prompt  # Should show code snippets
        assert "Suggestion:" in prompt  # Should have suggestions

    @patch("xandai.utils.git_utils.GitUtils.prepare_review_context")
    def test_process_with_valid_git_context(self, mock_git):
        """Test review process with valid Git context"""
        # Mock Git context
        mock_git.return_value = {
            "is_git_repo": True,
            "code_files": ["test.py", "utils.js"],
            "file_contents": {
                "test.py": 'print("Hello")\nsubprocess.run(cmd, shell=True)',
                "utils.js": "var x = 10;\nconsole.log(x);",
            },
            "file_diffs": {},
            "commit_info": {},
            "repo_stats": {},
            "error": None,
        }

        llm = MockLLMProvider()
        history = MockHistoryManager()
        processor = ReviewProcessor(llm, history)
        app_state = AppState()

        result = processor.process(app_state, ".")

        assert isinstance(result, ReviewResult)
        assert result.code_quality_score > 0
        assert len(result.files_reviewed) > 0
        assert llm.call_count > 0

    @patch("xandai.utils.git_utils.GitUtils.prepare_review_context")
    def test_process_with_git_error(self, mock_git):
        """Test review process handles Git errors gracefully"""
        mock_git.return_value = {"error": "Not a Git repository"}

        llm = MockLLMProvider()
        history = MockHistoryManager()
        processor = ReviewProcessor(llm, history)
        app_state = AppState()

        result = processor.process(app_state, ".")

        assert isinstance(result, ReviewResult)
        assert result.code_quality_score == 0
        assert "error" in result.summary.lower() or "Not a Git repository" in result.key_issues[0]

    @patch("xandai.utils.git_utils.GitUtils.prepare_review_context")
    def test_process_with_no_changes(self, mock_git):
        """Test review process with no code changes"""
        mock_git.return_value = {
            "is_git_repo": True,
            "code_files": [],
            "file_contents": {},
            "error": None,
        }

        llm = MockLLMProvider()
        history = MockHistoryManager()
        processor = ReviewProcessor(llm, history)
        app_state = AppState()

        result = processor.process(app_state, ".")

        assert isinstance(result, ReviewResult)
        assert len(result.files_reviewed) == 0


class TestReviewResultParsing:
    """Test parsing of LLM responses into ReviewResult"""

    @patch("xandai.utils.git_utils.GitUtils.prepare_review_context")
    def test_parse_complete_response(self, mock_git):
        """Test parsing a complete, well-formatted response"""
        mock_git.return_value = {
            "is_git_repo": True,
            "code_files": ["test.py"],
            "file_contents": {"test.py": 'print("test")'},
            "file_diffs": {},
            "error": None,
        }

        llm = MockLLMProvider()
        history = MockHistoryManager()
        processor = ReviewProcessor(llm, history)
        app_state = AppState()

        result = processor.process(app_state, ".")

        # Verify all sections are parsed
        assert len(result.summary) > 0
        assert result.code_quality_score > 0
        assert len(result.key_issues) > 0
        assert len(result.suggestions) > 0
        assert len(result.architecture_notes) > 0
        assert len(result.security_concerns) > 0
        assert len(result.performance_notes) > 0

    @patch("xandai.utils.git_utils.GitUtils.prepare_review_context")
    def test_parse_file_specific_comments(self, mock_git):
        """Test parsing file-specific comments"""
        mock_git.return_value = {
            "is_git_repo": True,
            "code_files": ["test.py"],
            "file_contents": {"test.py": 'print("test")'},
            "file_diffs": {},
            "error": None,
        }

        llm = MockLLMProvider()
        history = MockHistoryManager()
        processor = ReviewProcessor(llm, history)
        app_state = AppState()

        result = processor.process(app_state, ".")

        # Should have file-specific comments
        assert len(result.inline_comments) > 0
        assert "test.py" in result.inline_comments or "AI Analysis" in result.inline_comments

    @patch("xandai.utils.git_utils.GitUtils.prepare_review_context")
    def test_fallback_for_malformed_response(self, mock_git):
        """Test fallback mechanism for malformed LLM responses"""
        mock_git.return_value = {
            "is_git_repo": True,
            "code_files": ["test.py"],
            "file_contents": {"test.py": 'subprocess.run(cmd, shell=True)\nprint("test")'},
            "file_diffs": {},
            "error": None,
        }

        # Create LLM that returns malformed response
        llm = MockLLMProvider(response_content="This is a bad response without proper format")
        history = MockHistoryManager()
        processor = ReviewProcessor(llm, history)
        app_state = AppState()

        result = processor.process(app_state, ".")

        # Should still return a result with fallback analysis
        assert isinstance(result, ReviewResult)
        assert result.code_quality_score > 0
        # Fallback should detect the shell injection
        assert (
            any(
                "shell" in issue.lower() or "subprocess" in issue.lower()
                for issue in result.key_issues
            )
            or len(result.suggestions) > 0
        )


class TestRuleBasedAnalysis:
    """Test rule-based static analysis"""

    @patch("xandai.utils.git_utils.GitUtils.prepare_review_context")
    def test_python_security_rules_applied(self, mock_git):
        """Test that Python security rules are applied"""
        dangerous_code = """
import subprocess
subprocess.run('ls -la', shell=True)
password = "hardcoded123"
cursor.execute("SELECT * FROM users WHERE id = %s" % user_id)
eval(user_input)
"""

        mock_git.return_value = {
            "is_git_repo": True,
            "code_files": ["dangerous.py"],
            "file_contents": {"dangerous.py": dangerous_code},
            "file_diffs": {},
            "error": None,
        }

        llm = MockLLMProvider(response_content="# Bad response")
        history = MockHistoryManager()
        processor = ReviewProcessor(llm, history)
        app_state = AppState()

        result = processor.process(app_state, ".")

        # Fallback analysis should catch multiple issues
        total_issues = len(result.key_issues) + len(result.suggestions)
        assert total_issues > 0, "Should detect security vulnerabilities"

    @patch("xandai.utils.git_utils.GitUtils.prepare_review_context")
    def test_javascript_rules_applied(self, mock_git):
        """Test that JavaScript rules are applied"""
        js_code = """
var x = 10;
element.innerHTML = userInput;
if (x == y) {
    console.log('test');
}
"""

        mock_git.return_value = {
            "is_git_repo": True,
            "code_files": ["script.js"],
            "file_contents": {"script.js": js_code},
            "file_diffs": {},
            "error": None,
        }

        llm = MockLLMProvider(response_content="# Bad response")
        history = MockHistoryManager()
        processor = ReviewProcessor(llm, history)
        app_state = AppState()

        result = processor.process(app_state, ".")

        # Should detect JavaScript issues
        total_issues = len(result.key_issues) + len(result.suggestions)
        assert total_issues > 0, "Should detect JavaScript issues"


class TestAIPoweredAnalysis:
    """Test AI-powered code analysis"""

    @patch("xandai.utils.git_utils.GitUtils.prepare_review_context")
    def test_ai_analysis_with_structured_response(self, mock_git):
        """Test AI analysis with structured XML response"""
        mock_git.return_value = {
            "is_git_repo": True,
            "code_files": ["test.py"],
            "file_contents": {"test.py": "def test():\n    pass"},
            "file_diffs": {},
            "error": None,
        }

        # LLM returns structured issue tags
        ai_response = """<issue description="Missing docstring">
def test():
    pass
</issue>

<issue description="Function has no implementation">
    pass
</issue>"""

        llm = MockLLMProvider(response_content=ai_response)
        history = MockHistoryManager()
        processor = ReviewProcessor(llm, history)
        app_state = AppState()

        result = processor.process(app_state, ".")

        # Should parse structured issues
        assert isinstance(result, ReviewResult)
        # Check if AI issues were extracted
        assert len(result.inline_comments) > 0 or len(result.key_issues) > 0


class TestHistoryIntegration:
    """Test integration with history/conversation managers"""

    @patch("xandai.utils.git_utils.GitUtils.prepare_review_context")
    def test_adds_to_history(self, mock_git):
        """Test that review results are added to history"""
        mock_git.return_value = {
            "is_git_repo": True,
            "code_files": ["test.py"],
            "file_contents": {"test.py": 'print("test")'},
            "file_diffs": {},
            "error": None,
        }

        llm = MockLLMProvider()
        history = MockHistoryManager()
        processor = ReviewProcessor(llm, history)
        app_state = AppState()

        processor.process(app_state, ".")

        # Should have added messages to history
        assert len(history.messages) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
