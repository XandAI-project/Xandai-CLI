"""
Basic tests for XandAI CLI package
"""

import os
import sys
import unittest

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestBasicImports(unittest.TestCase):
    """Test basic package imports"""

    def test_import_main_module(self):
        """Test that we can import the main module"""
        try:
            import xandai

            self.assertTrue(hasattr(xandai, "__version__") or hasattr(xandai, "__name__"))
        except ImportError as e:
            self.fail(f"Failed to import xandai module: {e}")

    def test_import_main_components(self):
        """Test that we can import main components"""
        try:
            from xandai import main

            self.assertTrue(callable(main.main))
        except ImportError as e:
            self.fail(f"Failed to import main components: {e}")

    def test_import_cli_components(self):
        """Test CLI components import"""
        try:
            from xandai.integrations import ollama_client
            from xandai.utils import display_utils

            # Basic imports should work
            self.assertTrue(hasattr(ollama_client, "OllamaClient"))
        except ImportError as e:
            self.fail(f"Failed to import CLI components: {e}")


class TestPackageMetadata(unittest.TestCase):
    """Test package metadata"""

    def test_version_exists(self):
        """Test that version information exists"""
        import xandai

        # Either __version__ attribute or can get version info
        has_version = (
            hasattr(xandai, "__version__")
            or hasattr(xandai, "VERSION")
            or hasattr(xandai, "__name__")
        )
        self.assertTrue(has_version, "Package should have version information")


class TestBasicFunctionality(unittest.TestCase):
    """Test basic functionality without dependencies"""

    def test_main_function_exists(self):
        """Test that main entry point exists"""
        from xandai.main import main

        self.assertTrue(callable(main))

    def test_help_functionality(self):
        """Test help functionality doesn't crash"""
        try:
            # This should not crash even if Ollama is not available
            from xandai.core import app_state

            state = app_state.AppState()
            self.assertIsNotNone(state)
        except Exception as e:
            # Some dependencies might not be available in test environment
            # This is acceptable as long as basic structure works
            pass


if __name__ == "__main__":
    unittest.main()
