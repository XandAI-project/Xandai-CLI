#!/usr/bin/env python3
"""
Comprehensive tests for JavaScript/Node.js code execution in XandAI CLI
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


class TestJavaScriptExecution:
    """Test cases for JavaScript/Node.js code execution"""

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

    def test_javascript_language_config(self, chat_repl):
        """Test JavaScript language configuration"""
        config = chat_repl._get_language_config()

        # Test JavaScript configs
        for lang_key in ["javascript", "js", "node"]:
            js_config = config[lang_key]
            assert js_config["extensions"] == [".js"]
            assert js_config["inline_command"] == "node -e"
            assert js_config["file_command"] == "node"
            assert js_config["supports_inline"] == True
            assert js_config["needs_compilation"] == False
            assert "function " in js_config["complex_keywords"]
            assert "const " in js_config["complex_keywords"]
            assert "require(" in js_config["complex_keywords"]

    def test_simple_javascript_should_use_inline(self, chat_repl):
        """Test that simple JavaScript code uses inline execution"""
        simple_codes = [
            'console.log("Hello World")',
            "console.log(2 + 2)",
            "Math.floor(Math.random() * 10)",
        ]

        # These should use temp files due to complex keywords
        complex_codes = [
            "const x = 5; console.log(x * 2)",  # Contains 'const' keyword
        ]

        for code in simple_codes:
            should_use_temp = chat_repl._should_use_temp_file(code, "javascript")
            assert should_use_temp == False, f"Simple JS code should use inline: {code}"

        for code in complex_codes:
            should_use_temp = chat_repl._should_use_temp_file(code, "javascript")
            assert should_use_temp == True, f"Complex JS code should use temp file: {code}"

    def test_complex_javascript_should_use_temp_file(self, chat_repl):
        """Test that complex JavaScript code uses temp file"""
        complex_codes = [
            # Function definition
            """function greet(name) {
    return `Hello, ${name}!`;
}

console.log(greet("World"));""",
            # Class definition
            """class Calculator {
    add(a, b) {
        return a + b;
    }
}

const calc = new Calculator();
console.log(calc.add(2, 3));""",
            # Loop with braces
            """for (let i = 0; i < 3; i++) {
    console.log(`Number: ${i}`);
}
console.log("Done!");""",
            # Complex quotes
            """console.log("He said: \\"Hello 'world'\\"");""",
            # Long single line (>200 chars)
            'console.log("' + "A" * 250 + '");',
            # Require statement
            """const fs = require('fs');
console.log('File system loaded');""",
            # Module.exports
            """module.exports = {
    greet: function(name) {
        return `Hello ${name}`;
    }
};""",
            # If statement with braces
            """if (true) {
    console.log("This is true");
} else {
    console.log("This is false");
}""",
            # Arrow function
            """const add = (a, b) => {
    return a + b;
};
console.log(add(5, 3));""",
            # Template literals with newlines
            """const message = `
This is a multi-line
template literal
`;
console.log(message.trim());""",
        ]

        for code in complex_codes:
            should_use_temp = chat_repl._should_use_temp_file(code, "javascript")
            assert should_use_temp == True, f"Complex JS code should use temp file: {code[:50]}..."

    @patch("xandai.chat.ChatREPL._execute_command_with_output")
    def test_simple_javascript_inline_execution(self, mock_execute, chat_repl):
        """Test inline execution of simple JavaScript code"""
        code = 'console.log("Hello World")'

        with patch.object(chat_repl.console, "print") as mock_console:
            chat_repl._execute_code_by_language(code, "javascript")

        # Verify inline command was used
        mock_execute.assert_called_once()
        command = mock_execute.call_args[0][0]
        assert "node -e" in command
        assert "Hello World" in command

    @patch("xandai.chat.ChatREPL._execute_command_with_output")
    @patch("tempfile.NamedTemporaryFile")
    @patch("os.unlink")
    def test_complex_javascript_temp_file_execution(
        self, mock_unlink, mock_temp, mock_execute, chat_repl
    ):
        """Test temp file execution of complex JavaScript code"""
        code = """function greet(name) {
    return `Hello, ${name}!`;
}

console.log(greet("World"));"""

        # Mock temporary file
        mock_file = MagicMock()
        mock_file.name = "/tmp/test.js"
        mock_temp.return_value.__enter__.return_value = mock_file

        with patch.object(chat_repl.console, "print") as mock_console:
            chat_repl._execute_code_by_language(code, "javascript")

        # Verify temp file creation
        mock_temp.assert_called_once()
        call_args = mock_temp.call_args[1]
        assert call_args["suffix"] == ".js"
        assert call_args["delete"] == False
        assert call_args["encoding"] == "utf-8"

        # Verify code was written to file
        mock_file.write.assert_called_once_with(code)

        # Verify execution command
        mock_execute.assert_called_once()
        command = mock_execute.call_args[0][0]
        assert 'node "' in command
        assert mock_file.name in command

        # Verify cleanup
        mock_unlink.assert_called_once_with(mock_file.name)

        # Verify console messages
        mock_console.assert_any_call(
            "[dim]Creating temporary javascript file for execution...[/dim]"
        )
        mock_console.assert_any_call("[dim]Temporary javascript file cleaned up.[/dim]")

    @patch("xandai.chat.ChatREPL._execute_command_with_output")
    def test_javascript_with_node_alias(self, mock_execute, chat_repl):
        """Test JavaScript execution using 'node' language identifier"""
        code = 'console.log("Hello from Node")'

        with patch.object(chat_repl.console, "print"):
            chat_repl._execute_code_by_language(code, "node")

        # Verify node command was used
        mock_execute.assert_called_once()
        command = mock_execute.call_args[0][0]
        assert "node -e" in command

    @patch("xandai.chat.ChatREPL._execute_command_with_output")
    def test_javascript_with_js_alias(self, mock_execute, chat_repl):
        """Test JavaScript execution using 'js' language identifier"""
        code = 'console.log("Hello from JS")'

        with patch.object(chat_repl.console, "print"):
            chat_repl._execute_code_by_language(code, "js")

        # Verify node command was used
        mock_execute.assert_called_once()
        command = mock_execute.call_args[0][0]
        assert "node -e" in command

    def test_javascript_keyword_detection(self, chat_repl):
        """Test detection of JavaScript-specific keywords"""
        keyword_tests = [
            ("function test() {}", True),
            ("const x = 5", True),
            ("let y = 10", True),
            ("var z = 15", True),
            ("class MyClass {}", True),
            ('import something from "module"', True),
            ('require("module")', True),
            ("module.exports = {}", True),
            ('console.log("simple")', False),
            ("Math.random()", False),
            ("x + y", False),
        ]

        for code, expected in keyword_tests:
            result = chat_repl._should_use_temp_file(code, "javascript")
            assert result == expected, f"Keyword detection failed for: {code}"

    @patch("xandai.chat.ChatREPL._execute_command_with_output")
    def test_javascript_quote_escaping(self, mock_execute, chat_repl):
        """Test quote handling - now uses temp file for complex quotes"""
        code = 'console.log("Hello \\"World\\"")'

        chat_repl._execute_code_by_language(code, "javascript")

        # Complex quotes now use temp file instead of inline
        command = mock_execute.call_args[0][0]
        assert "node " in command and ".js" in command  # temp file execution

    @patch("xandai.chat.ChatREPL._execute_command_with_output")
    def test_javascript_error_handling(self, mock_execute, chat_repl):
        """Test error handling in JavaScript execution"""
        # Mock execution to raise an exception
        mock_execute.side_effect = Exception("Node execution failed")

        with patch.object(chat_repl.console, "print") as mock_console:
            chat_repl._execute_code_by_language('console.log("test")', "javascript")

        # Verify error message was displayed
        error_calls = [
            call
            for call in mock_console.call_args_list
            if "Error executing javascript code" in str(call)
        ]
        assert len(error_calls) > 0

    def test_javascript_template_literals(self, chat_repl):
        """Test detection of template literals requiring temp files"""
        template_literal_codes = [
            # Multi-line template literal
            """const message = `
Hello ${name},
Welcome to our application!
`;""",
            # Template literal with expressions
            """const result = `The sum of ${a} and ${b} is ${a + b}`;""",
            # Nested template literals
            """const html = `<div>${`Hello ${user.name}`}</div>`;""",
        ]

        for code in template_literal_codes:
            should_use_temp = chat_repl._should_use_temp_file(code, "javascript")
            assert should_use_temp == True, f"Template literal should use temp file: {code[:30]}..."

    def test_javascript_es6_features(self, chat_repl):
        """Test detection of ES6+ features that require temp files"""
        es6_codes = [
            # Destructuring
            """const {name, age} = person;
console.log(name, age);""",
            # Arrow functions
            """const add = (a, b) => a + b;
console.log(add(5, 3));""",
            # Async/await
            """async function fetchData() {
    const result = await fetch('/api/data');
    return result.json();
}""",
            # Spread operator
            """const arr1 = [1, 2, 3];
const arr2 = [...arr1, 4, 5];
console.log(arr2);""",
        ]

        for code in es6_codes:
            should_use_temp = chat_repl._should_use_temp_file(code, "javascript")
            assert should_use_temp == True, f"ES6+ code should use temp file: {code[:30]}..."

    @patch("xandai.chat.ChatREPL._execute_command_with_output")
    @patch("tempfile.NamedTemporaryFile")
    @patch("os.unlink")
    def test_temp_file_cleanup_on_exception(self, mock_unlink, mock_temp, mock_execute, chat_repl):
        """Test that temp files are cleaned up even when execution fails"""
        code = 'function test() { console.log("test"); }'

        # Mock temporary file
        mock_file = MagicMock()
        mock_file.name = "/tmp/test.js"
        mock_temp.return_value.__enter__.return_value = mock_file

        # Mock execution to raise exception
        mock_execute.side_effect = Exception("Node execution failed")

        with patch.object(chat_repl.console, "print"):
            chat_repl._execute_code_by_language(code, "javascript")

        # Verify cleanup still happened despite exception
        mock_unlink.assert_called_once_with(mock_file.name)

    def test_javascript_edge_cases(self, chat_repl):
        """Test edge cases in JavaScript code detection"""
        edge_cases = [
            # Single semicolon
            (";", False),
            # Empty function call
            ("test()", False),
            # Simple variable assignment
            ("x = 5", False),
            # Complex nested quotes
            (
                'console.log("Say \\"Hello\\" to \'World\'"); console.log("Again");',
                True,
            ),
            # Very long method chain
            ("obj." + "method()." * 50 + "result()", True),  # >200 chars
        ]

        for code, expected in edge_cases:
            result = chat_repl._should_use_temp_file(code, "javascript")
            assert result == expected, f"Edge case failed for: {repr(code)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
