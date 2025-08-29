#!/usr/bin/env python3
"""
Test script to verify the new behavior
"""

print("🧪 Testing new command execution behavior:")
print("=" * 50)

# Test cases
test_cases = [
    ("dir", "Should execute (exact command)"),
    ("ls", "Should execute (exact command)"),
    ("pwd", "Should execute (exact command)"),
    ("list files in directory", "Should call AI (not execute)"),
    ("show files", "Should call AI (not execute)"),
    ("a script in powershell to list the 50 biggest files", "Should call AI (not execute)"),
    ("help me create a script", "Should call AI (not execute)"),
    ("git status", "Should execute (exact command)"),
]

from xandai.shell_executor import ShellExecutor

shell = ShellExecutor()

for command, expected in test_cases:
    is_shell = shell.is_shell_command(command)
    result = "EXECUTE" if is_shell else "CALL AI"
    status = "✅" if (
        (is_shell and "Should execute" in expected) or 
        (not is_shell and "Should call AI" in expected)
    ) else "❌"
    
    print(f"{status} '{command}' -> {result} ({expected})")

print("\n✨ The new behavior should:")
print("  • Only execute EXACT commands like 'dir', 'ls', 'git status'")
print("  • Send everything else to AI (requests, questions, scripts)")
print("  • No more smart interpretation of natural language")
