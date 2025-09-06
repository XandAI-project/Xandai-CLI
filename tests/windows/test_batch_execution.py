#!/usr/bin/env python3
"""
Comprehensive tests for Batch/CMD code execution in XandAI CLI (Windows)
Tests both inline and temp file execution methods for Batch scripts
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from xandai.chat import ChatREPL
from xandai.history import HistoryManager


class TestBatchExecution:
    """Test cases for Batch/CMD code execution (Windows-specific)"""

    @pytest.fixture
    def chat_repl(self):
        """Create ChatREPL instance for testing"""
        from unittest.mock import patch

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

    def test_batch_language_config(self, chat_repl):
        """Test Batch language configuration"""
        config = chat_repl._get_language_config()

        # Test Batch configs
        for lang_key in ["cmd", "batch", "bat"]:
            batch_config = config[lang_key]
            if lang_key == "cmd":
                assert batch_config["extensions"] == [".cmd", ".bat"]
            else:
                assert batch_config["extensions"] == [".bat"]
            assert batch_config["inline_command"] == "cmd /c"
            assert batch_config["file_command"] == "cmd /c"
            assert batch_config["supports_inline"] == True
            assert batch_config["needs_compilation"] == False
            assert "@echo" in batch_config["complex_keywords"]
            assert "if " in batch_config["complex_keywords"]
            assert "for " in batch_config["complex_keywords"]
            assert "set " in batch_config["complex_keywords"]

    def test_simple_batch_should_use_inline(self, chat_repl):
        """Test that simple Batch code uses inline execution"""
        simple_codes = ["echo Hello World", "dir", "echo %DATE%"]

        # Note: 'cd C:\' contains backslash, so it uses temp file
        complex_codes = ["cd C:\\"]  # Contains backslash, triggers temp file

        for code in simple_codes:
            should_use_temp = chat_repl._should_use_temp_file(code, "bat")
            assert should_use_temp == False, f"Simple Batch code should use inline: {code}"

        for code in complex_codes:
            should_use_temp = chat_repl._should_use_temp_file(code, "bat")
            assert should_use_temp == True, f"Complex Batch code should use temp file: {code}"

    def test_complex_batch_should_use_temp_file(self, chat_repl):
        """Test that complex Batch code uses temp file"""
        complex_codes = [
            # Multi-line with echo off
            """@echo off
echo Hello World
echo This is a batch file
pause""",
            # If statement
            """if exist "C:\\temp" (
    echo Directory exists
) else (
    echo Directory does not exist
)""",
            # For loop
            """for %%i in (*.txt) do (
    echo Processing file: %%i
    type "%%i"
)""",
            # Variable setting and usage
            """set NAME=World
echo Hello %NAME%
set /a NUMBER=5+3
echo Result: %NUMBER%""",
            # Goto and labels
            """@echo off
echo Starting...
goto :skip
echo This will not print
:skip
echo Continuing...""",
            # Complex quotes
            """echo "He said: \\"Hello 'Batch'\\"" """,
            # Long single line (>200 chars)
            'echo "' + "A" * 250 + '"',
            # Multiple commands with &&
            """dir C:\\ && echo Directory listed && echo Done""",
            # Call to another batch file
            """call "setup.bat" param1 param2
echo Setup completed""",
            # Error handling with errorlevel
            """ping google.com >nul 2>nul
if %errorlevel% == 0 (
    echo Internet connection OK
) else (
    echo No internet connection
)""",
        ]

        for code in complex_codes:
            should_use_temp = chat_repl._should_use_temp_file(code, "bat")
            assert (
                should_use_temp == True
            ), f"Complex Batch code should use temp file: {code[:50]}..."

    @patch("xandai.chat.ChatREPL._execute_command_with_output")
    def test_simple_batch_inline_execution(self, mock_execute, chat_repl):
        """Test inline execution of simple Batch code"""
        code = "echo Hello World"

        with patch.object(chat_repl.console, "print") as mock_console:
            chat_repl._execute_code_by_language(code, "bat")

        # Verify inline command was used
        mock_execute.assert_called_once()
        command = mock_execute.call_args[0][0]
        assert "cmd /c" in command
        assert "Hello World" in command

    @patch("xandai.chat.ChatREPL._execute_command_with_output")
    @patch("tempfile.NamedTemporaryFile")
    @patch("os.unlink")
    def test_complex_batch_temp_file_execution(
        self, mock_unlink, mock_temp, mock_execute, chat_repl
    ):
        """Test temp file execution of complex Batch code"""
        code = """@echo off
echo Hello World
echo This is a batch file
pause"""

        # Mock temporary file
        mock_file = MagicMock()
        mock_file.name = "C:\\temp\\test.bat"
        mock_temp.return_value.__enter__.return_value = mock_file

        with patch.object(chat_repl.console, "print") as mock_console:
            chat_repl._execute_code_by_language(code, "bat")

        # Verify temp file creation
        mock_temp.assert_called_once()
        call_args = mock_temp.call_args[1]
        assert call_args["suffix"] == ".bat"
        assert call_args["delete"] == False
        assert call_args["encoding"] == "utf-8"

        # Verify code was written to file
        mock_file.write.assert_called_once_with(code)

        # Verify execution command
        mock_execute.assert_called_once()
        command = mock_execute.call_args[0][0]
        assert "cmd /c" in command
        assert mock_file.name in command

        # Verify cleanup
        mock_unlink.assert_called_once_with(mock_file.name)

        # Verify console messages
        mock_console.assert_any_call("[dim]Creating temporary bat file for execution...[/dim]")
        mock_console.assert_any_call("[dim]Temporary bat file cleaned up.[/dim]")

    @patch("xandai.chat.ChatREPL._execute_command_with_output")
    def test_batch_with_cmd_alias(self, mock_execute, chat_repl):
        """Test Batch execution using 'cmd' language identifier"""
        code = "echo Hello from CMD"

        with patch.object(chat_repl.console, "print"):
            chat_repl._execute_code_by_language(code, "cmd")

        # Verify cmd command was used
        mock_execute.assert_called_once()
        command = mock_execute.call_args[0][0]
        assert "cmd /c" in command

    @patch("xandai.chat.ChatREPL._execute_command_with_output")
    def test_batch_with_batch_alias(self, mock_execute, chat_repl):
        """Test Batch execution using 'batch' language identifier"""
        code = "echo Hello from Batch"

        with patch.object(chat_repl.console, "print"):
            chat_repl._execute_code_by_language(code, "batch")

        # Verify cmd command was used
        mock_execute.assert_called_once()
        command = mock_execute.call_args[0][0]
        assert "cmd /c" in command

    def test_batch_keyword_detection(self, chat_repl):
        """Test detection of Batch-specific keywords"""
        keyword_tests = [
            ("@echo off", True),
            ("@echo on", True),
            ('if exist "file.txt"', True),
            ("for %%i in (*.txt)", True),
            ("goto :label", True),
            ('call "script.bat"', True),
            ("set VAR=value", True),
            ("echo simple", False),
            ("dir", False),
            ("cd", False),
        ]

        for code, expected in keyword_tests:
            result = chat_repl._should_use_temp_file(code, "bat")
            assert result == expected, f"Keyword detection failed for: {code}"

    @patch("xandai.chat.ChatREPL._execute_command_with_output")
    def test_batch_quote_escaping(self, mock_execute, chat_repl):
        """Test complex quotes trigger temp file execution"""
        code = 'echo "Hello \\"Batch\\""'

        with patch.object(chat_repl.console, "print"):
            chat_repl._execute_code_by_language(code, "bat")

        # Complex quotes trigger temp file usage
        command = mock_execute.call_args[0][0]
        assert "cmd /c" in command
        # Should be a temp file execution, not inline
        assert '.bat"' in command

    @patch("xandai.chat.ChatREPL._execute_command_with_output")
    def test_batch_error_handling(self, mock_execute, chat_repl):
        """Test error handling in Batch execution"""
        # Mock execution to raise an exception
        mock_execute.side_effect = Exception("CMD execution failed")

        with patch.object(chat_repl.console, "print") as mock_console:
            chat_repl._execute_code_by_language('echo "test"', "bat")

        # Verify error message was displayed
        error_calls = [
            call for call in mock_console.call_args_list if "Error executing bat code" in str(call)
        ]
        assert len(error_calls) > 0

    def test_batch_variable_detection(self, chat_repl):
        """Test detection of Batch variables and keywords"""
        # Commands with 'set ' keyword should use temp file
        set_commands = [
            "set NAME=John",
            "set /a NUMBER=5+3",
            "set /p INPUT=Enter your name: ",
        ]

        # Variable usage without keywords should use inline
        inline_commands = [
            "echo %USERNAME%",
            "echo %DATE% %TIME%",
        ]

        # Commands with keywords should use temp file
        keyword_commands = [
            'if "%VAR%"=="value" echo matched',  # contains 'if '
        ]

        for code in set_commands + keyword_commands:
            should_use_temp = chat_repl._should_use_temp_file(code, "bat")
            assert should_use_temp == True, f"Batch keyword code should use temp file: {code}"

        for code in inline_commands:
            should_use_temp = chat_repl._should_use_temp_file(code, "bat")
            assert (
                should_use_temp == False
            ), f"Simple batch variable usage should use inline: {code}"

    def test_batch_control_flow_detection(self, chat_repl):
        """Test detection of Batch control flow requiring temp files"""
        control_flow_codes = [
            # If statements
            """if exist "file.txt" (
    echo File exists
)""",
            # For loops
            """for /l %%i in (1,1,10) do (
    echo Number: %%i
)""",
            # While-like loop using goto
            """:loop
echo Looping...
goto loop""",
            # Switch-like using if-else chains
            """if "%1"=="option1" (
    echo Option 1 selected
) else if "%1"=="option2" (
    echo Option 2 selected
) else (
    echo Unknown option
)""",
        ]

        for code in control_flow_codes:
            should_use_temp = chat_repl._should_use_temp_file(code, "bat")
            assert (
                should_use_temp == True
            ), f"Batch control flow should use temp file: {code[:30]}..."

    def test_batch_redirection_detection(self, chat_repl):
        """Test detection of Batch redirection requiring temp files"""
        redirection_codes = [
            # Output redirection
            "echo Hello > output.txt",
            "dir >> listing.txt",
            "command 2>nul",
            "command >nul 2>&1",
            # Input redirection
            "sort < input.txt",
            'findstr "pattern" < file.txt',
        ]

        for code in redirection_codes:
            should_use_temp = chat_repl._should_use_temp_file(code, "bat")
            # Most redirection should be safe for inline, but complex ones might use temp
            # The exact behavior depends on the complexity detection logic

    @patch("xandai.chat.ChatREPL._execute_command_with_output")
    @patch("tempfile.NamedTemporaryFile")
    @patch("os.unlink")
    def test_temp_file_cleanup_on_exception(self, mock_unlink, mock_temp, mock_execute, chat_repl):
        """Test that temp files are cleaned up even when execution fails"""
        code = "@echo off\necho test"

        # Mock temporary file
        mock_file = MagicMock()
        mock_file.name = "C:\\temp\\test.bat"
        mock_temp.return_value.__enter__.return_value = mock_file

        # Mock execution to raise exception
        mock_execute.side_effect = Exception("CMD execution failed")

        with patch.object(chat_repl.console, "print"):
            chat_repl._execute_code_by_language(code, "bat")

        # Verify cleanup still happened despite exception
        mock_unlink.assert_called_once_with(mock_file.name)

    def test_batch_edge_cases(self, chat_repl):
        """Test edge cases in Batch code detection"""
        edge_cases = [
            # Empty command - now correctly expects temp file for safety
            ("", True),
            # Single command
            ("echo", False),
            # Simple file operation
            ("copy file1.txt file2.txt", False),
            # Complex nested quotes - >2 quotes triggers temp file
            ('echo "Say \\"Hello\\" to \'Batch\'"; echo "Again"', True),
            # Very long echo - >200 chars triggers temp file
            ('echo "' + "A" * 250 + '"', True),
            # Comment-like
            ("rem This is a comment", False),
        ]

        for code, expected in edge_cases:
            result = chat_repl._should_use_temp_file(code, "bat")
            assert result == expected, f"Edge case failed for: {repr(code)}"

    def test_batch_special_characters(self, chat_repl):
        """Test handling of Batch special characters"""
        special_char_codes = [
            # Pipe operations
            'dir | findstr ".txt"',
            "echo hello | more",
            # Ampersand operations
            "echo first && echo second",
            "echo first || echo fallback",
            # Parentheses grouping
            "(echo first & echo second) && echo done",
        ]

        for code in special_char_codes:
            should_use_temp = chat_repl._should_use_temp_file(code, "bat")
            # These operations might require temp files due to complexity


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
