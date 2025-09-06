#!/usr/bin/env python3
"""
Comprehensive tests for PowerShell code execution in XandAI CLI (Windows)
Tests both inline and temp file execution methods for PowerShell scripts
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


class TestPowerShellExecution:
    """Test cases for PowerShell code execution (Windows-specific)"""

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

    def test_powershell_language_config(self, chat_repl):
        """Test PowerShell language configuration"""
        config = chat_repl._get_language_config()

        # Test PowerShell configs
        for lang_key in ["powershell", "ps1"]:
            ps_config = config[lang_key]
            assert ps_config["extensions"] == [".ps1"]
            assert ps_config["inline_command"] == "powershell -Command"
            assert ps_config["file_command"] == "powershell -File"
            assert ps_config["supports_inline"] == True
            assert ps_config["needs_compilation"] == False
            assert "function " in ps_config["complex_keywords"]
            assert "$" in ps_config["complex_keywords"]
            assert "Get-" in ps_config["complex_keywords"]
            assert "Set-" in ps_config["complex_keywords"]

    def test_simple_powershell_should_use_inline(self, chat_repl):
        """Test that simple PowerShell code uses inline execution"""
        simple_codes = ['Write-Host "Hello World"', 'Write-Output "Simple command"']

        # Commands with keywords should use temp file
        keyword_codes = [
            "Get-Date",  # Contains 'Get-' keyword
            "$x = 5; Write-Host $x",  # Contains '$' keyword
        ]

        for code in simple_codes:
            should_use_temp = chat_repl._should_use_temp_file(code, "powershell")
            assert should_use_temp == False, f"Simple PowerShell code should use inline: {code}"

        for code in keyword_codes:
            should_use_temp = chat_repl._should_use_temp_file(code, "powershell")
            assert (
                should_use_temp == True
            ), f"PowerShell code with keywords should use temp file: {code}"

    def test_complex_powershell_should_use_temp_file(self, chat_repl):
        """Test that complex PowerShell code uses temp file"""
        complex_codes = [
            # Function definition
            """function Get-Greeting {
    param([string]$Name)
    return "Hello, $Name!"
}

Write-Host (Get-Greeting -Name "World")""",
            # Advanced function with parameters
            """function Test-Connection {
    param(
        [Parameter(Mandatory=$true)]
        [string]$ComputerName,

        [int]$Count = 4
    )

    Test-NetConnection -ComputerName $ComputerName -Count $Count
}""",
            # If statement with blocks
            """if ($env:OS -eq "Windows_NT") {
    Write-Host "Running on Windows"
} else {
    Write-Host "Not Windows"
}""",
            # ForEach loop
            '''$numbers = 1..5
foreach ($number in $numbers) {
    Write-Host "Number: $number"
}
Write-Host "Done!"''',
            # Pipeline with multiple cmdlets
            """Get-Process |
Where-Object {$_.ProcessName -like "*chrome*"} |
Select-Object ProcessName, Id, CPU |
Sort-Object CPU -Descending""",
            # Complex quotes and escaping
            """Write-Host "He said: \\"Hello 'PowerShell'\\"" """,
            # Long single line (>200 chars)
            'Write-Host "' + "A" * 250 + '"',
            # Variable with complex assignment
            '''$data = @{
    Name = "John"
    Age = 30
    City = "New York"
}
Write-Host "Name: $($data.Name)"''',
            # Try-catch block
            """try {
    Get-Item "C:\\NonExistentFile.txt" -ErrorAction Stop
} catch {
    Write-Host "File not found: $($_.Exception.Message)"
}""",
            # While loop
            """$counter = 0
while ($counter -lt 3) {
    Write-Host "Counter: $counter"
    $counter++
}""",
        ]

        for code in complex_codes:
            should_use_temp = chat_repl._should_use_temp_file(code, "powershell")
            assert (
                should_use_temp == True
            ), f"Complex PowerShell code should use temp file: {code[:50]}..."

    @patch("xandai.chat.ChatREPL._execute_command_with_output")
    def test_simple_powershell_inline_execution(self, mock_execute, chat_repl):
        """Test inline execution of simple PowerShell code"""
        code = 'Write-Host "Hello World"'

        with patch.object(chat_repl.console, "print") as mock_console:
            chat_repl._execute_code_by_language(code, "powershell")

        # Verify inline command was used
        mock_execute.assert_called_once()
        command = mock_execute.call_args[0][0]
        assert "powershell -Command" in command
        assert "Hello World" in command

    @patch("xandai.chat.ChatREPL._execute_command_with_output")
    @patch("tempfile.NamedTemporaryFile")
    @patch("os.unlink")
    def test_complex_powershell_temp_file_execution(
        self, mock_unlink, mock_temp, mock_execute, chat_repl
    ):
        """Test temp file execution of complex PowerShell code"""
        code = """function Get-Greeting {
    param([string]$Name)
    return "Hello, $Name!"
}

Write-Host (Get-Greeting -Name "World")"""

        # Mock temporary file
        mock_file = MagicMock()
        mock_file.name = "C:\\temp\\test.ps1"
        mock_temp.return_value.__enter__.return_value = mock_file

        with patch.object(chat_repl.console, "print") as mock_console:
            chat_repl._execute_code_by_language(code, "powershell")

        # Verify temp file creation
        mock_temp.assert_called_once()
        call_args = mock_temp.call_args[1]
        assert call_args["suffix"] == ".ps1"
        assert call_args["delete"] == False
        assert call_args["encoding"] == "utf-8"

        # Verify code was written to file
        mock_file.write.assert_called_once_with(code)

        # Verify execution command
        mock_execute.assert_called_once()
        command = mock_execute.call_args[0][0]
        assert "powershell -File" in command
        assert mock_file.name in command

        # Verify cleanup
        mock_unlink.assert_called_once_with(mock_file.name)

        # Verify console messages
        mock_console.assert_any_call(
            "[dim]Creating temporary powershell file for execution...[/dim]"
        )
        mock_console.assert_any_call("[dim]Temporary powershell file cleaned up.[/dim]")

    @patch("xandai.chat.ChatREPL._execute_command_with_output")
    def test_powershell_with_ps1_alias(self, mock_execute, chat_repl):
        """Test PowerShell execution using 'ps1' language identifier"""
        code = "Get-Date"  # Contains 'Get-' keyword, will use temp file

        with patch.object(chat_repl.console, "print"):
            chat_repl._execute_code_by_language(code, "ps1")

        # Verify powershell command was used (temp file due to Get- keyword)
        mock_execute.assert_called_once()
        command = mock_execute.call_args[0][0]
        assert "powershell -File" in command

    def test_powershell_keyword_detection(self, chat_repl):
        """Test detection of PowerShell-specific keywords"""
        keyword_tests = [
            ("function Test-Function {}", True),
            ("param([string]$name)", True),
            ("if ($condition) {}", True),
            ("foreach ($item in $collection) {}", True),
            ("while ($condition) {}", True),
            ('$variable = "value"', True),  # Contains '$' keyword
            ("Get-Process", True),  # Contains 'Get-' keyword
            ("Set-Location", True),  # Contains 'Set-' keyword
            ('Write-Host "simple"', False),
            ("Get-Date", True),  # Contains 'Get-' keyword - this was wrong in test
            ('"simple string"', False),
        ]

        for code, expected in keyword_tests:
            result = chat_repl._should_use_temp_file(code, "powershell")
            assert result == expected, f"Keyword detection failed for: {code}"

    @patch("xandai.chat.ChatREPL._execute_command_with_output")
    def test_powershell_quote_escaping(self, mock_execute, chat_repl):
        """Test complex quotes trigger temp file execution"""
        code = 'Write-Host "Hello \\"PowerShell\\""'

        with patch.object(chat_repl.console, "print"):
            chat_repl._execute_code_by_language(code, "powershell")

        # Complex quotes trigger temp file usage
        command = mock_execute.call_args[0][0]
        assert "powershell -File" in command
        # Should be a temp file execution due to complex quotes
        assert '.ps1"' in command

    @patch("xandai.chat.ChatREPL._execute_command_with_output")
    def test_powershell_error_handling(self, mock_execute, chat_repl):
        """Test error handling in PowerShell execution"""
        # Mock execution to raise an exception
        mock_execute.side_effect = Exception("PowerShell execution failed")

        with patch.object(chat_repl.console, "print") as mock_console:
            chat_repl._execute_code_by_language('Write-Host "test"', "powershell")

        # Verify error message was displayed
        error_calls = [
            call
            for call in mock_console.call_args_list
            if "Error executing powershell code" in str(call)
        ]
        assert len(error_calls) > 0

    def test_powershell_variable_detection(self, chat_repl):
        """Test detection of PowerShell variables requiring temp files"""
        variable_codes = [
            # Variable assignments
            '$name = "John"',
            "$numbers = 1..10",
            '$hash = @{key="value"}',
            '$array = @("item1", "item2")',
            # Variable expansion
            '"Hello $name"',
            '"The result is $($calculation)"',
        ]

        for code in variable_codes:
            should_use_temp = chat_repl._should_use_temp_file(code, "powershell")
            assert should_use_temp == True, f"PowerShell variable code should use temp file: {code}"

    def test_powershell_cmdlet_detection(self, chat_repl):
        """Test detection of PowerShell cmdlets"""
        cmdlet_tests = [
            # Should use temp file (complex cmdlets with keywords)
            (
                "Get-ChildItem | Where-Object {$_.Length -gt 1000}",
                True,
            ),  # Contains 'Get-' and '$'
            (
                "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned",
                True,
            ),  # Contains 'Set-'
            (
                "New-Object System.Collections.ArrayList",
                False,
            ),  # No keywords matched, long but <200 chars
            # All Get- and Set- cmdlets use temp file due to keywords
            ("Get-Date", True),  # Contains 'Get-' keyword
            ("Get-Location", True),  # Contains 'Get-' keyword
            ("Set-Location", True),  # Contains 'Set-' keyword
            ("Clear-Host", False),  # No keywords matched
        ]

        for code, expected in cmdlet_tests:
            result = chat_repl._should_use_temp_file(code, "powershell")
            assert result == expected, f"Cmdlet detection failed for: {code}"

    def test_powershell_pipeline_detection(self, chat_repl):
        """Test detection of PowerShell pipelines requiring temp files"""
        pipeline_codes = [
            # Multi-stage pipelines
            """Get-Process |
Where-Object {$_.CPU -gt 100} |
Select-Object Name, CPU |
Sort-Object CPU -Descending""",
            # Complex pipeline with formatting
            """Get-Service |
Where-Object {$_.Status -eq "Running"} |
Format-Table Name, Status, StartType -AutoSize""",
            # Pipeline with ForEach-Object
            """1..5 | ForEach-Object {
    Write-Host "Processing item: $_"
    $_ * 2
}""",
        ]

        for code in pipeline_codes:
            should_use_temp = chat_repl._should_use_temp_file(code, "powershell")
            assert (
                should_use_temp == True
            ), f"PowerShell pipeline should use temp file: {code[:30]}..."

    @patch("xandai.chat.ChatREPL._execute_command_with_output")
    @patch("tempfile.NamedTemporaryFile")
    @patch("os.unlink")
    def test_temp_file_cleanup_on_exception(self, mock_unlink, mock_temp, mock_execute, chat_repl):
        """Test that temp files are cleaned up even when execution fails"""
        code = 'function Test { Write-Host "test" }'

        # Mock temporary file
        mock_file = MagicMock()
        mock_file.name = "C:\\temp\\test.ps1"
        mock_temp.return_value.__enter__.return_value = mock_file

        # Mock execution to raise exception
        mock_execute.side_effect = Exception("PowerShell execution failed")

        with patch.object(chat_repl.console, "print"):
            chat_repl._execute_code_by_language(code, "powershell")

        # Verify cleanup still happened despite exception
        mock_unlink.assert_called_once_with(mock_file.name)

    def test_powershell_edge_cases(self, chat_repl):
        """Test edge cases in PowerShell code detection"""
        edge_cases = [
            # Empty command - now correctly expects temp file for safety
            ("", True),
            # Single variable - contains '$' keyword
            ("$x", True),
            # Simple string
            ('"hello"', False),
            # Complex nested quotes - >2 quotes triggers temp file
            (
                'Write-Host "Say \\"Hello\\" to \'PowerShell\'"; Write-Host "Again"',
                True,
            ),
            # Very long cmdlet - >200 chars triggers temp file
            ("Get-" + "A" * 200, True),
        ]

        for code, expected in edge_cases:
            result = chat_repl._should_use_temp_file(code, "powershell")
            assert result == expected, f"Edge case failed for: {repr(code)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
