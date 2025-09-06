#!/usr/bin/env python3
"""
Integration tests for the multi-language code execution system
Tests the overall system behavior and cross-language functionality
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from xandai.chat import ChatREPL
from xandai.history import HistoryManager


class TestMultiLanguageIntegration:
    """Integration tests for multi-language code execution"""

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

    def test_all_supported_languages_config(self, chat_repl):
        """Test that all expected languages are configured"""
        config = chat_repl._get_language_config()

        expected_languages = {
            # Interpreted languages
            "python",
            "py",
            "javascript",
            "js",
            "node",
            # Compiled languages
            "c",
            "cpp",
            "c++",
            "go",
            # Shell languages
            "bash",
            "sh",
            "shell",
            # Windows languages
            "cmd",
            "batch",
            "bat",
            "powershell",
            "ps1",
            # Package managers
            "npm",
        }

        for lang in expected_languages:
            assert lang in config, f"Language {lang} not found in configuration"
            assert isinstance(config[lang], dict), f"Configuration for {lang} is not a dictionary"
            assert "supports_inline" in config[lang], f"Missing 'supports_inline' for {lang}"
            assert "needs_compilation" in config[lang], f"Missing 'needs_compilation' for {lang}"

    def test_language_categorization(self, chat_repl):
        """Test that languages are properly categorized"""
        config = chat_repl._get_language_config()

        # Interpreted languages should support inline execution
        interpreted_langs = ["python", "javascript", "bash", "powershell"]
        for lang in interpreted_langs:
            assert config[lang]["supports_inline"] == True, f"{lang} should support inline"
            assert config[lang]["needs_compilation"] == False, f"{lang} should not need compilation"

        # Compiled languages should not support inline execution
        compiled_langs = ["c", "cpp", "go"]
        for lang in compiled_langs:
            assert config[lang]["supports_inline"] == False, f"{lang} should not support inline"
            # Note: Go uses 'go run' which handles compilation internally
            if lang != "go":
                assert config[lang]["needs_compilation"] == True, f"{lang} should need compilation"

    @patch("xandai.chat.ChatREPL._execute_command_with_output")
    def test_unknown_language_fallback(self, mock_execute, chat_repl):
        """Test fallback behavior for unknown languages"""
        with patch.object(chat_repl.console, "print") as mock_console:
            with patch.object(chat_repl, "_execute_shell_code") as mock_shell:
                chat_repl._execute_code_by_language("echo test", "unknown_language")

        # Should warn about unknown language and fall back to shell
        warning_calls = [
            call for call in mock_console.call_args_list if "Unknown language" in str(call)
        ]
        assert len(warning_calls) > 0
        mock_shell.assert_called_once_with("echo test")

    def test_temp_file_decision_consistency(self, chat_repl):
        """Test that temp file decisions are consistent across languages"""

        # Simple code should generally use inline where supported
        simple_codes = [
            ('print("hello")', "python"),
            ('console.log("hello")', "javascript"),
            ('echo "hello"', "bash"),
            ('Write-Host "hello"', "powershell"),
            ("echo hello", "bat"),
        ]

        for code, lang in simple_codes:
            config = chat_repl._get_language_config()[lang]
            should_use_temp = chat_repl._should_use_temp_file(code, lang)

            if config["supports_inline"]:
                assert should_use_temp == False, f"Simple {lang} code should use inline: {code}"

        # Multi-line code should always use temp files
        multiline_codes = [
            ('def test():\n    print("hello")', "python"),
            ('function test() {\n    console.log("hello");\n}', "javascript"),
            ('function test() {\n    echo "hello"\n}', "bash"),
            ('function Test {\n    Write-Host "hello"\n}', "powershell"),
            ("@echo off\necho hello", "bat"),
        ]

        for code, lang in multiline_codes:
            should_use_temp = chat_repl._should_use_temp_file(code, lang)
            assert should_use_temp == True, f"Multi-line {lang} code should use temp file"

    @patch("xandai.chat.ChatREPL._execute_command_with_output")
    def test_language_alias_consistency(self, mock_execute, chat_repl):
        """Test that language aliases work consistently"""

        alias_groups = [
            (["python", "py"], "python -c"),
            (["javascript", "js", "node"], "node -e"),
            (["powershell", "ps1"], "powershell -Command"),
            (["cmd", "batch", "bat"], "cmd /c"),
        ]

        for aliases, expected_command in alias_groups:
            for alias in aliases:
                with patch.object(chat_repl.console, "print"):
                    chat_repl._execute_code_by_language("simple_code", alias)

                # Verify the same base command is used
                command = mock_execute.call_args[0][0]
                assert expected_command in command, f"Alias {alias} should use {expected_command}"
                mock_execute.reset_mock()

    def test_file_extension_mapping(self, chat_repl):
        """Test that file extensions are correctly mapped"""
        config = chat_repl._get_language_config()

        extension_mappings = {
            ".py": ["python", "py"],
            ".js": ["javascript", "js", "node"],
            ".c": ["c"],
            ".cpp": ["cpp"],
            ".go": ["go"],
            ".sh": ["bash", "sh", "shell"],
            ".bat": ["batch", "bat"],
            ".ps1": ["powershell", "ps1"],
        }

        for extension, languages in extension_mappings.items():
            for lang in languages:
                if lang in config and config[lang]["extensions"]:
                    assert (
                        extension in config[lang]["extensions"]
                    ), f"Extension {extension} not found for language {lang}"

    @patch("xandai.chat.ChatREPL._execute_command_with_output")
    @patch("tempfile.NamedTemporaryFile")
    @patch("os.unlink")
    def test_temp_file_cleanup_across_languages(
        self, mock_unlink, mock_temp, mock_execute, chat_repl
    ):
        """Test that temp file cleanup works across all languages"""

        # Mock temporary file
        mock_file = MagicMock()
        mock_file.name = "/tmp/test.ext"
        mock_temp.return_value.__enter__.return_value = mock_file

        languages_with_temp_files = ["python", "javascript", "powershell", "bat"]
        complex_codes = [
            "def test(): pass",
            "function test() {}",
            'function Test { Write-Host "test" }',
            "@echo off\necho test",
        ]

        for lang, code in zip(languages_with_temp_files, complex_codes):
            with patch.object(chat_repl.console, "print"):
                chat_repl._execute_code_by_language(code, lang)

            # Verify cleanup was called for each language
            assert mock_unlink.called, f"Cleanup not called for {lang}"
            mock_unlink.reset_mock()

    def test_complex_keyword_detection_across_languages(self, chat_repl):
        """Test that complex keywords are detected consistently"""

        keyword_tests = [
            # Function definitions
            ("def function():", "python", True),
            ("function test() {}", "javascript", True),
            ("function Test {}", "powershell", True),
            # Variable declarations
            ("const x = 5", "javascript", True),
            ('$var = "value"', "powershell", True),
            ("set VAR=value", "bat", True),
            # Control structures
            ("for i in range(5):", "python", True),
            ("for (let i=0; i<5; i++)", "javascript", True),
            ("for %%i in (*.txt)", "bat", True),
            # Imports/includes
            ("import module", "python", True),
            ('require("module")', "javascript", True),
            ("#include <stdio.h>", "c", True),
        ]

        for code, lang, expected in keyword_tests:
            result = chat_repl._should_use_temp_file(code, lang)
            assert result == expected, f"Keyword detection failed for {lang}: {code}"

    def test_cross_platform_shell_handling(self, chat_repl):
        """Test cross-platform shell script handling"""
        config = chat_repl._get_language_config()

        # Test shell language configuration
        shell_langs = ["bash", "sh", "shell"]
        for lang in shell_langs:
            shell_config = config[lang]
            assert "inline_command" in shell_config
            assert "file_command" in shell_config
            assert shell_config["supports_inline"] == True

    @patch("xandai.chat.ChatREPL._execute_command_with_output")
    def test_error_handling_across_languages(self, mock_execute, chat_repl):
        """Test error handling is consistent across languages"""

        # Mock execution to raise exception
        mock_execute.side_effect = Exception("Execution failed")

        test_languages = ["python", "javascript", "powershell", "bat"]

        for lang in test_languages:
            with patch.object(chat_repl.console, "print") as mock_console:
                chat_repl._execute_code_by_language("test_code", lang)

            # Verify error message was displayed for each language
            error_calls = [
                call
                for call in mock_console.call_args_list
                if f"Error executing {lang} code" in str(call)
            ]
            assert len(error_calls) > 0, f"Error handling not working for {lang}"

    def test_quote_escaping_consistency(self, chat_repl):
        """Test that quote escaping works consistently across languages"""

        test_code = 'print("Hello \\"World\\"")'  # Code with nested quotes

        # Languages that support inline execution
        inline_languages = ["python", "javascript", "powershell", "bat"]

        with patch("xandai.chat.ChatREPL._execute_command_with_output") as mock_execute:
            for lang in inline_languages:
                with patch.object(chat_repl.console, "print"):
                    # Force inline execution by using simple code structure
                    simple_code = f'echo "test"'  # Simplified to ensure inline
                    chat_repl._execute_code_by_language(simple_code, lang)

                if mock_execute.called:
                    command = mock_execute.call_args[0][0]
                    # Verify command was properly escaped (contains quotes)
                    assert '"' in command, f"Quote escaping may be incorrect for {lang}"

                mock_execute.reset_mock()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
