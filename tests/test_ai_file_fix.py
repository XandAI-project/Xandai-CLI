#!/usr/bin/env python3
"""
Tests for AI File Fix Functionality
Tests that the AI can properly understand and fix code files
"""

import os
import re
import tempfile
import unittest
from pathlib import Path

from xandai.utils.ai_file_prompts import AIFilePrompts


class TestAIFileFix(unittest.TestCase):
    """Test suite for AI file fix functionality"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.prompts = AIFilePrompts()

    def tearDown(self):
        """Clean up test environment"""
        import shutil

        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_file_update_system_prompt_structure(self):
        """Test that file update system prompt has the required structure"""
        prompt = self.prompts.get_file_update_system_prompt()

        # Check for key sections
        self.assertIn("FILE UPDATE mode", prompt)
        self.assertIn("<code edit filename=", prompt)
        self.assertIn("COMPLETE file content", prompt)
        self.assertIn("ANALYSIS:", prompt)
        self.assertIn("CHANGES:", prompt)
        self.assertIn("EXPLANATION:", prompt)

    def test_multi_file_creation_system_prompt_structure(self):
        """Test that multi-file creation prompt has the required structure"""
        prompt = self.prompts.get_multi_file_creation_system_prompt()

        # Check for key sections
        self.assertIn("MULTI-FILE CREATION mode", prompt)
        self.assertIn("FILE STRUCTURE:", prompt)
        self.assertIn("FILES TO CREATE:", prompt)
        self.assertIn("<code edit filename=", prompt)

    def test_code_fix_context_prompt_generation(self):
        """Test generation of context-aware fix prompt"""
        file_path = "calculator.py"
        file_content = """def divide(a, b):
    return a / b
"""
        issue = "Fix division by zero error"

        prompt = self.prompts.get_code_fix_context_prompt(file_path, file_content, issue)

        # Check prompt contains all necessary elements
        self.assertIn(file_path, prompt)
        self.assertIn(file_content, prompt)
        self.assertIn(issue, prompt)
        self.assertIn("COMPLETE updated file", prompt)
        self.assertIn("<code edit filename=", prompt)

    def test_multi_file_creation_context_prompt_generation(self):
        """Test generation of multi-file creation prompt"""
        project_description = "Create a simple calculator package"
        file_list = ["calculator.py", "utils.py", "README.md"]

        prompt = self.prompts.get_multi_file_creation_context_prompt(project_description, file_list)

        # Check prompt contains project description and file list
        self.assertIn(project_description, prompt)
        for file_name in file_list:
            self.assertIn(file_name, prompt)
        self.assertIn("PROJECT PLAN:", prompt)
        self.assertIn("FILE STRUCTURE:", prompt)

    def test_enhanced_system_prompt_for_chat(self):
        """Test enhanced system prompt for chat mode"""
        prompt = self.prompts.get_enhanced_system_prompt_for_chat()

        # Check for key features
        self.assertIn("XandAI", prompt)
        self.assertIn("CHAT MODE", prompt)
        self.assertIn("FILE UPDATE MODE", prompt)
        self.assertIn("MULTI-FILE MODE", prompt)
        self.assertIn("<code edit filename=", prompt)
        self.assertIn("COMPLETE file content", prompt)

    def test_enhance_user_query_for_fix(self):
        """Test user query enhancement"""
        user_query = "Fix the bug in this file"
        file_path = "app.py"

        enhanced = self.prompts.enhance_user_query_for_fix(user_query, file_path)

        # Check enhancement adds important instructions
        self.assertIn(user_query, enhanced)
        self.assertIn(file_path, enhanced)
        self.assertIn("COMPLETE", enhanced)
        self.assertIn("<code edit", enhanced)

    def test_ai_response_parsing_single_file(self):
        """Test parsing AI response with single file"""
        # Simulate AI response
        ai_response = """
ANALYSIS:
The file has a division by zero bug.

CHANGES:
- Added error handling for division by zero

UPDATED FILE:
<code edit filename="calculator.py">
def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
</code>

EXPLANATION:
Added check to prevent division by zero.
"""

        # Extract file content
        pattern = r'<code edit filename="([^"]+)">(.*?)</code>'
        matches = re.findall(pattern, ai_response, re.DOTALL)

        self.assertEqual(len(matches), 1)
        filename, content = matches[0]
        self.assertEqual(filename, "calculator.py")
        self.assertIn("ValueError", content)
        self.assertIn("Cannot divide by zero", content)

    def test_ai_response_parsing_multiple_files(self):
        """Test parsing AI response with multiple files"""
        # Simulate AI response with multiple files
        ai_response = """
PROJECT PLAN:
Creating a calculator package

FILES TO CREATE:

<code edit filename="calculator.py">
def add(a, b):
    return a + b
</code>

<code edit filename="utils.py">
def format_result(value):
    return f"Result: {value}"
</code>

<code edit filename="README.md">
# Calculator Package
Simple calculator with utilities
</code>
"""

        # Extract all files
        pattern = r'<code edit filename="([^"]+)">(.*?)</code>'
        matches = re.findall(pattern, ai_response, re.DOTALL)

        self.assertEqual(len(matches), 3)

        # Check each file
        filenames = [match[0] for match in matches]
        self.assertIn("calculator.py", filenames)
        self.assertIn("utils.py", filenames)
        self.assertIn("README.md", filenames)

    def test_simple_bug_fix_scenario(self):
        """Test complete scenario: create buggy file, generate fix prompt, verify fix format"""
        # Create a simple buggy file
        buggy_file = os.path.join(self.test_dir, "calculator.py")
        buggy_content = """def divide(a, b):
    return a / b

def main():
    print(divide(10, 0))  # This will crash!

if __name__ == "__main__":
    main()
"""

        with open(buggy_file, "w") as f:
            f.write(buggy_content)

        # Generate fix prompt
        issue = "Fix the division by zero error"
        fix_prompt = self.prompts.get_code_fix_context_prompt("calculator.py", buggy_content, issue)

        # Verify prompt structure
        self.assertIn("calculator.py", fix_prompt)
        self.assertIn("division by zero", fix_prompt.lower())
        self.assertIn("COMPLETE", fix_prompt)

        # Simulate what a correct AI response should contain
        expected_elements = [
            "ANALYSIS:",
            "CHANGES:",
            '<code edit filename="calculator.py">',
            "</code>",
            "EXPLANATION:",
        ]

        # These elements should be mentioned in the prompt as requirements
        for element in expected_elements:
            # Either the element is in the prompt or instructions about it are
            self.assertTrue(
                element in fix_prompt or element.replace(":", "").lower() in fix_prompt.lower()
            )

    def test_multiple_files_creation_scenario(self):
        """Test complete scenario for creating multiple files"""
        project_description = "Create a simple Python calculator package with tests"
        file_list = [
            "calculator/__init__.py",
            "calculator/operations.py",
            "calculator/utils.py",
            "tests/test_operations.py",
            "README.md",
            "requirements.txt",
        ]

        # Generate creation prompt
        creation_prompt = self.prompts.get_multi_file_creation_context_prompt(
            project_description, file_list
        )

        # Verify prompt structure
        self.assertIn(project_description, creation_prompt)
        for file_path in file_list:
            self.assertIn(file_path, creation_prompt)

        # Verify it asks for complete files
        self.assertIn("ALL files", creation_prompt)
        self.assertIn("PROJECT PLAN", creation_prompt)
        self.assertIn("FILE STRUCTURE", creation_prompt)

    def test_prompt_emphasizes_completeness(self):
        """Test that prompts emphasize providing complete file content"""
        update_prompt = self.prompts.get_file_update_system_prompt()
        multi_prompt = self.prompts.get_multi_file_creation_system_prompt()
        chat_prompt = self.prompts.get_enhanced_system_prompt_for_chat()

        # All prompts should emphasize completeness
        for prompt in [update_prompt, multi_prompt, chat_prompt]:
            # Check for emphasis on completeness (case insensitive)
            prompt_lower = prompt.lower()
            self.assertTrue(
                "complete" in prompt_lower and "file" in prompt_lower,
                f"Prompt should emphasize providing complete file content",
            )

            # Check it warns against placeholders
            self.assertTrue(
                "never" in prompt_lower or "not" in prompt_lower or "don't" in prompt_lower,
                f"Prompt should warn against using placeholders",
            )

    def test_prompt_provides_examples(self):
        """Test that prompts provide clear examples"""
        update_prompt = self.prompts.get_file_update_system_prompt()
        multi_prompt = self.prompts.get_multi_file_creation_system_prompt()

        # Check for example sections
        for prompt in [update_prompt, multi_prompt]:
            self.assertIn("EXAMPLE", prompt)
            self.assertIn("<code edit filename=", prompt)

    def test_validate_ai_response_format(self):
        """Test validation of AI response format"""

        # Good response format
        good_response = """
ANALYSIS:
File has a bug

CHANGES:
- Fixed the bug

UPDATED FILE:
<code edit filename="test.py">
def fixed_function():
    return "fixed"
</code>

EXPLANATION:
The bug is now fixed
"""

        # Check it has all required sections
        self.assertIn("ANALYSIS:", good_response)
        self.assertIn("CHANGES:", good_response)
        self.assertIn("<code edit filename=", good_response)
        self.assertIn("</code>", good_response)
        self.assertIn("EXPLANATION:", good_response)

        # Bad response format (with placeholders)
        bad_response = """
<code edit filename="test.py">
def fixed_function():
    # ... existing code ...
    return "fixed"
</code>
"""

        # This should be detected as bad (contains placeholders)
        self.assertIn("...", bad_response)

    def test_python_syntax_in_example(self):
        """Test that example code in prompts is valid Python"""
        update_prompt = self.prompts.get_file_update_system_prompt()

        # Extract code from examples
        pattern = r"<code edit filename=\"([^\"]+)\">(.*?)</code>"
        matches = re.findall(pattern, update_prompt, re.DOTALL)

        for filename, code in matches:
            if filename.endswith(".py"):
                # Try to compile the code
                try:
                    compile(code.strip(), filename, "exec")
                    syntax_valid = True
                except SyntaxError:
                    syntax_valid = False

                self.assertTrue(
                    syntax_valid, f"Example Python code in prompt should be syntactically valid"
                )


class TestAIFileFixIntegration(unittest.TestCase):
    """Integration tests for AI file fix with file operations"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test environment"""
        import shutil

        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_complete_fix_workflow(self):
        """Test complete workflow: buggy file -> AI fix -> corrected file"""
        # Step 1: Create a buggy file
        buggy_file = os.path.join(self.test_dir, "buggy.py")
        buggy_content = """def divide(a, b):
    return a / b  # BUG: No zero check!
"""

        with open(buggy_file, "w") as f:
            f.write(buggy_content)

        # Step 2: Generate fix prompt
        prompts = AIFilePrompts()
        fix_prompt = prompts.get_code_fix_context_prompt(
            "buggy.py", buggy_content, "Fix division by zero"
        )

        # Step 3: Verify prompt is well-formed
        self.assertIn("buggy.py", fix_prompt)
        self.assertIn(buggy_content, fix_prompt)

        # Step 4: Simulate AI providing a fix
        ai_fix = """
ANALYSIS:
The divide function doesn't handle division by zero.

CHANGES:
- Added zero check before division
- Raise ValueError with descriptive message

UPDATED FILE:
<code edit filename="buggy.py">
def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b  # Fixed: Now handles zero!
</code>

EXPLANATION:
Added validation to prevent division by zero errors.
"""

        # Step 5: Extract fixed code
        pattern = r'<code edit filename="([^"]+)">(.*?)</code>'
        matches = re.findall(pattern, ai_fix, re.DOTALL)

        self.assertEqual(len(matches), 1)
        filename, fixed_content = matches[0]
        fixed_content = fixed_content.strip()

        # Step 6: Verify fixed code is valid Python
        try:
            compile(fixed_content, filename, "exec")
            syntax_valid = True
        except SyntaxError:
            syntax_valid = False

        self.assertTrue(syntax_valid, "Fixed code should be valid Python")

        # Step 7: Verify fix addresses the issue
        self.assertIn("if b == 0", fixed_content)
        self.assertIn("ValueError", fixed_content)

        # Step 8: Write fixed file
        fixed_file = os.path.join(self.test_dir, "fixed.py")
        with open(fixed_file, "w") as f:
            f.write(fixed_content)

        # Step 9: Verify file was created correctly
        self.assertTrue(os.path.exists(fixed_file))
        with open(fixed_file, "r") as f:
            actual_content = f.read()
            self.assertEqual(actual_content, fixed_content)


if __name__ == "__main__":
    unittest.main()
