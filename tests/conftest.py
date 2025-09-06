#!/usr/bin/env python3
"""
Pytest configuration and shared fixtures for XandAI CLI tests
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def project_root_path():
    """Get the project root path"""
    return project_root


@pytest.fixture
def mock_llm_provider():
    """Create a mock LLM provider for testing"""
    provider = MagicMock()
    provider.is_connected.return_value = True
    provider.get_available_models.return_value = ["test-model"]
    provider.get_current_model.return_value = "test-model"
    return provider


@pytest.fixture
def chat_repl_no_prompt():
    """Create ChatREPL instance without prompt_toolkit for testing"""
    from unittest.mock import MagicMock, patch

    from xandai.chat import ChatREPL
    from xandai.history import HistoryManager

    mock_provider = MagicMock()
    mock_provider.is_connected.return_value = True
    history = HistoryManager()

    # Mock PromptSession to avoid Windows console issues
    with patch("xandai.chat.PromptSession") as mock_prompt:
        mock_session = MagicMock()
        mock_prompt.return_value = mock_session

        # Mock IntelligentCompleter to avoid import issues
        with patch("xandai.chat.IntelligentCompleter"):
            chat_repl = ChatREPL(mock_provider, history)
            return chat_repl


@pytest.fixture
def temp_directory(tmp_path):
    """Create a temporary directory for test files"""
    return tmp_path


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "windows: Windows-specific tests")
    config.addinivalue_line("markers", "unix: Unix/Linux-specific tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "slow: Slow-running tests")


def pytest_collection_modifyitems(config, items):
    """Auto-mark tests based on their location and name"""
    for item in items:
        # Mark Windows-specific tests
        if "windows" in str(item.fspath):
            item.add_marker(pytest.mark.windows)

        # Mark integration tests
        if "integration" in item.name or "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Mark unit tests (default for most tests)
        if not any(marker.name in ["integration", "windows"] for marker in item.iter_markers()):
            item.add_marker(pytest.mark.unit)


# Skip Windows tests on non-Windows platforms
def pytest_runtest_setup(item):
    """Skip Windows tests on non-Windows platforms"""
    if "windows" in [marker.name for marker in item.iter_markers()]:
        if os.name != "nt":
            pytest.skip("Windows-specific test")


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables and state before each test"""
    # Store original environment
    original_env = os.environ.copy()

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def capture_output():
    """Fixture to capture stdout and stderr for testing"""
    import contextlib
    import io

    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    with contextlib.redirect_stdout(stdout_capture):
        with contextlib.redirect_stderr(stderr_capture):
            yield {"stdout": stdout_capture, "stderr": stderr_capture}


# Custom test outcome reporting
def pytest_runtest_makereport(item, call):
    """Custom test reporting"""
    if call.when == "call":
        # Add custom information to test reports if needed
        pass


# Fixture for mocking file operations
@pytest.fixture
def mock_file_operations():
    """Mock file operations for testing"""
    import tempfile

    # Use ExitStack for Python 3.8+ compatibility
    from contextlib import ExitStack
    from unittest.mock import mock_open, patch

    with ExitStack() as stack:
        mock_temp = stack.enter_context(patch("tempfile.NamedTemporaryFile"))
        mock_unlink = stack.enter_context(patch("os.unlink"))
        mock_file = stack.enter_context(patch("builtins.open", mock_open()))

        # Configure mock temporary file
        mock_temp_file = MagicMock()
        mock_temp_file.name = "/tmp/test_file.tmp"
        mock_temp.return_value.__enter__.return_value = mock_temp_file

        yield {
            "temp_file": mock_temp,
            "temp_file_instance": mock_temp_file,
            "unlink": mock_unlink,
            "open": mock_file,
        }


# Custom assertions for multi-language testing
class MultiLanguageAssertions:
    """Custom assertions for multi-language code execution testing"""

    @staticmethod
    def assert_inline_execution(mock_execute, expected_command_prefix):
        """Assert that inline execution was used with correct command"""
        assert mock_execute.called, "Execution command was not called"
        command = mock_execute.call_args[0][0]
        assert (
            expected_command_prefix in command
        ), f"Expected '{expected_command_prefix}' in command: {command}"

    @staticmethod
    def assert_temp_file_execution(mock_temp, mock_unlink, expected_extension):
        """Assert that temp file execution was used with correct extension"""
        assert mock_temp.called, "Temporary file was not created"
        call_args = mock_temp.call_args[1]
        assert (
            call_args["suffix"] == expected_extension
        ), f"Expected extension {expected_extension}, got {call_args['suffix']}"
        assert mock_unlink.called, "Temporary file was not cleaned up"

    @staticmethod
    def assert_error_handled(mock_console, language):
        """Assert that error was properly handled and displayed"""
        error_calls = [
            call
            for call in mock_console.call_args_list
            if f"Error executing {language} code" in str(call)
        ]
        assert len(error_calls) > 0, f"Error not properly handled for {language}"


@pytest.fixture
def multi_lang_assertions():
    """Fixture providing custom assertions for multi-language testing"""
    return MultiLanguageAssertions()
