#!/usr/bin/env python3
"""
Comprehensive tests for Python code execution in XandAI CLI
Tests both inline and temp file execution methods
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from xandai.chat import ChatREPL
from xandai.history import HistoryManager


class TestPythonExecution:
    """Test cases for Python code execution"""

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

    def test_python_language_config(self, chat_repl):
        """Test Python language configuration"""
        config = chat_repl._get_language_config()

        # Test Python config
        python_config = config["python"]
        assert python_config["extensions"] == [".py"]
        assert python_config["inline_command"] == "python -c"
        assert python_config["file_command"] == "python"
        assert python_config["supports_inline"] == True
        assert python_config["needs_compilation"] == False
        assert "def " in python_config["complex_keywords"]
        assert "class " in python_config["complex_keywords"]

        # Test 'py' alias
        py_config = config["py"]
        assert py_config["extensions"] == [".py"]
        assert py_config["supports_inline"] == True

    def test_simple_python_should_use_inline(self, chat_repl):
        """Test that simple Python code uses inline execution"""
        simple_codes = [
            'print("Hello World")',
            "print(2 + 2)",
            "x = 5; print(x * 2)",
        ]

        # These should use temp files due to complex keywords
        complex_codes = [
            "import os; print(os.getcwd())",  # Contains 'import' keyword
        ]

        for code in simple_codes:
            should_use_temp = chat_repl._should_use_temp_file(code, "python")
            assert should_use_temp == False, f"Simple code should use inline: {code}"

        for code in complex_codes:
            should_use_temp = chat_repl._should_use_temp_file(code, "python")
            assert should_use_temp == True, f"Complex code should use temp file: {code}"

    def test_complex_python_should_use_temp_file(self, chat_repl):
        """Test that complex Python code uses temp file"""
        complex_codes = [
            # Multi-line function
            """def greet(name):
    return f"Hello, {name}!"

print(greet("World"))""",
            # Class definition
            """class Calculator:
    def add(self, a, b):
        return a + b

calc = Calculator()
print(calc.add(2, 3))""",
            # Loop with indentation
            """for i in range(3):
    print(f"Number: {i}")
print("Done!")""",
            # Triple quotes
            '''message = """
This is a multi-line
string with triple quotes
"""
print(message.strip())''',
            # Complex quotes
            """print("He said: \\"Hello 'world'\\"")""",
            # Long single line (>200 chars)
            'print("' + "A" * 250 + '")',
            # If statement
            """if True:
    print("This is true")
else:
    print("This is false")""",
        ]

        for code in complex_codes:
            should_use_temp = chat_repl._should_use_temp_file(code, "python")
            assert should_use_temp == True, f"Complex code should use temp file: {code[:50]}..."

    @patch("xandai.chat.ChatREPL._execute_command_with_output")
    def test_simple_python_inline_execution(self, mock_execute, chat_repl):
        """Test inline execution of simple Python code"""
        code = 'print("Hello World")'

        with patch.object(chat_repl.console, "print") as mock_console:
            chat_repl._execute_code_by_language(code, "python")

        # Verify inline command was used
        mock_execute.assert_called_once()
        command = mock_execute.call_args[0][0]
        assert "python -c" in command
        assert "Hello World" in command

    @patch("xandai.chat.ChatREPL._execute_command_with_output")
    @patch("tempfile.NamedTemporaryFile")
    @patch("os.unlink")
    def test_complex_python_temp_file_execution(
        self, mock_unlink, mock_temp, mock_execute, chat_repl
    ):
        """Test temp file execution of complex Python code"""
        code = """def greet(name):
    return f"Hello, {name}!"

print(greet("World"))"""

        # Mock temporary file
        mock_file = MagicMock()
        mock_file.name = "/tmp/test.py"
        mock_temp.return_value.__enter__.return_value = mock_file

        with patch.object(chat_repl.console, "print") as mock_console:
            chat_repl._execute_code_by_language(code, "python")

        # Verify temp file creation
        mock_temp.assert_called_once()
        call_args = mock_temp.call_args[1]
        assert call_args["suffix"] == ".py"
        assert call_args["delete"] == False
        assert call_args["encoding"] == "utf-8"

        # Verify code was written to file
        mock_file.write.assert_called_once_with(code)

        # Verify execution command
        mock_execute.assert_called_once()
        command = mock_execute.call_args[0][0]
        assert 'python "' in command
        assert mock_file.name in command

        # Verify cleanup
        mock_unlink.assert_called_once_with(mock_file.name)

        # Verify console messages
        mock_console.assert_any_call("[dim]Creating temporary python file for execution...[/dim]")
        mock_console.assert_any_call("[dim]Temporary python file cleaned up.[/dim]")

    @patch("xandai.chat.ChatREPL._execute_command_with_output")
    def test_python_error_handling(self, mock_execute, chat_repl):
        """Test error handling in Python execution"""
        # Mock execution to raise an exception
        mock_execute.side_effect = Exception("Execution failed")

        with patch.object(chat_repl.console, "print") as mock_console:
            chat_repl._execute_code_by_language('print("test")', "python")

        # Verify error message was displayed
        error_calls = [
            call
            for call in mock_console.call_args_list
            if "Error executing python code" in str(call)
        ]
        assert len(error_calls) > 0

    def test_python_keyword_detection(self, chat_repl):
        """Test detection of Python-specific keywords"""
        keyword_tests = [
            ("def function():", True),
            ("class MyClass:", True),
            ('if __name__ == "__main__":', True),
            ("for item in list:", True),
            ("while condition:", True),
            ("with open() as f:", True),
            ("try:", True),
            ("import module", True),
            ("from module import", True),
            ('print("simple")', False),
            ("x = 5", False),
        ]

        for code, expected in keyword_tests:
            result = chat_repl._should_use_temp_file(code, "python")
            assert result == expected, f"Keyword detection failed for: {code}"

    @patch("xandai.chat.ChatREPL._execute_command_with_output")
    def test_python_quote_escaping(self, mock_execute, chat_repl):
        """Test quote handling - now uses temp file for complex quotes"""
        code = 'print("Hello \\"World\\"")'

        chat_repl._execute_code_by_language(code, "python")

        # Complex quotes now use temp file instead of inline
        command = mock_execute.call_args[0][0]
        assert "python " in command and ".py" in command  # temp file execution

    def test_python_edge_cases(self, chat_repl):
        """Test edge cases in Python code detection"""
        edge_cases = [
            # Empty code - fixed to expect True
            ("", True),  # Default to temp file for safety
            # Only whitespace - fixed to expect True
            ("   \n\n   ", True),
            # Single character
            ("x", False),
            # Very long single line
            ("x = " + "a" * 300, True),
            # Backslashes - now correctly handled
            ('print("C:\\\\path\\\\to\\\\file")', False),  # Simple print should be inline
            # Multiple quotes
            ('print("a"); print("b"); print("c")', True),  # More than 2 quotes
        ]

        for code, expected in edge_cases:
            result = chat_repl._should_use_temp_file(code, "python")
            assert result == expected, f"Edge case failed for: {repr(code)}"

    @patch("xandai.chat.ChatREPL._execute_command_with_output")
    @patch("tempfile.NamedTemporaryFile")
    @patch("os.unlink")
    def test_temp_file_cleanup_on_exception(self, mock_unlink, mock_temp, mock_execute, chat_repl):
        """Test that temp files are cleaned up even when execution fails"""
        code = "def test(): pass"

        # Mock temporary file
        mock_file = MagicMock()
        mock_file.name = "/tmp/test.py"
        mock_temp.return_value.__enter__.return_value = mock_file

        # Mock execution to raise exception
        mock_execute.side_effect = Exception("Execution failed")

        with patch.object(chat_repl.console, "print"):
            chat_repl._execute_code_by_language(code, "python")

        # Verify cleanup still happened despite exception
        mock_unlink.assert_called_once_with(mock_file.name)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
