"""
Tests for XandAI Web Integration functionality
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from xandai.web.content_extractor import ContentExtractor, ExtractedContent
from xandai.web.link_detector import LinkDetector
from xandai.web.web_fetcher import FetchResult, WebFetcher
from xandai.web.web_manager import WebIntegrationResult, WebManager


class TestWebIntegration(unittest.TestCase):
    """Test complete web integration workflow"""

    def setUp(self):
        """Set up test fixtures"""
        self.web_manager = WebManager(enabled=False)  # Start disabled

    def tearDown(self):
        """Clean up after tests"""
        self.web_manager.close()

    def test_web_manager_initialization(self):
        """Test WebManager initializes correctly"""
        self.assertIsInstance(self.web_manager, WebManager)
        self.assertFalse(self.web_manager.is_enabled())
        self.assertEqual(self.web_manager.timeout, 10)
        self.assertEqual(self.web_manager.max_links, 3)

    def test_enable_disable_functionality(self):
        """Test enabling/disabling web integration"""
        # Initially disabled
        self.assertFalse(self.web_manager.is_enabled())

        # Enable
        self.web_manager.set_enabled(True)
        self.assertTrue(self.web_manager.is_enabled())

        # Disable
        self.web_manager.set_enabled(False)
        self.assertFalse(self.web_manager.is_enabled())

    def test_disabled_processing(self):
        """Test that disabled web manager doesn't process links"""
        self.web_manager.set_enabled(False)

        user_input = "Check this out: https://example.com"
        result = self.web_manager.process_user_input(user_input)

        self.assertIsInstance(result, WebIntegrationResult)
        self.assertEqual(result.original_text, user_input)
        self.assertEqual(result.processed_text, user_input)
        self.assertEqual(len(result.extracted_contents), 0)
        self.assertFalse(result.processing_info["enabled"])

    def test_no_links_processing(self):
        """Test processing input with no links"""
        self.web_manager.set_enabled(True)

        user_input = "This has no links in it"
        result = self.web_manager.process_user_input(user_input)

        self.assertEqual(result.original_text, user_input)
        self.assertEqual(result.processed_text, user_input)
        self.assertEqual(len(result.extracted_contents), 0)
        self.assertEqual(result.processing_info["links_found"], 0)

    @patch("xandai.web.web_manager.WebManager._fetch_and_extract")
    def test_successful_link_processing(self, mock_fetch):
        """Test successful processing of links"""
        # Setup
        self.web_manager.set_enabled(True)

        # Mock successful content extraction
        mock_content = ExtractedContent(
            title="Test Page",
            description="A test page",
            main_content="This is test content",
            code_blocks=["print('hello')"],
            links=[],
            metadata={},
            word_count=100,
            language="python",
        )
        mock_fetch.return_value = mock_content

        user_input = "Check this tutorial: https://example.com/tutorial"
        result = self.web_manager.process_user_input(user_input)

        self.assertTrue(result.success)
        self.assertEqual(len(result.extracted_contents), 1)
        self.assertEqual(result.extracted_contents[0].title, "Test Page")
        self.assertIn("Web Content Context", result.processed_text)

    def test_cache_functionality(self):
        """Test URL caching functionality"""
        self.web_manager.set_enabled(True)

        # Test cache info
        cache_info = self.web_manager.get_cache_info()
        self.assertIn("size", cache_info)
        self.assertIn("max_size", cache_info)
        self.assertIn("urls", cache_info)

        # Test cache clearing
        self.web_manager.clear_cache()
        cache_info_after = self.web_manager.get_cache_info()
        self.assertEqual(cache_info_after["size"], 0)

    def test_stats_functionality(self):
        """Test statistics functionality"""
        stats = self.web_manager.get_stats()

        expected_keys = ["enabled", "timeout", "max_links", "cache_size", "components"]
        for key in expected_keys:
            self.assertIn(key, stats)

        # Test components are ready
        components = stats["components"]
        self.assertEqual(components["link_detector"], "ready")
        self.assertEqual(components["web_fetcher"], "ready")
        self.assertEqual(components["content_extractor"], "ready")

    def test_error_handling(self):
        """Test error handling in web processing"""
        self.web_manager.set_enabled(True)

        # Test with malformed input that might cause errors
        user_input = "Invalid link: not-a-real-url"
        result = self.web_manager.process_user_input(user_input)

        # Should handle gracefully
        self.assertTrue(result.success)  # Should not crash
        self.assertEqual(len(result.extracted_contents), 0)


class TestWebIntegrationEdgeCases(unittest.TestCase):
    """Test edge cases and error scenarios"""

    def setUp(self):
        self.web_manager = WebManager(enabled=True, timeout=5, max_links=2)

    def tearDown(self):
        self.web_manager.close()

    def test_max_links_limit(self):
        """Test that max_links parameter is respected"""
        user_input = """
        Multiple links here:
        https://example1.com
        https://example2.com
        https://example3.com
        https://example4.com
        """

        # Mock the link detector to find all links
        with patch.object(
            self.web_manager.link_detector, "find_processable_links"
        ) as mock_detector:
            mock_detector.return_value = [
                ("https://example1.com", 0, 20),
                ("https://example2.com", 21, 41),
                ("https://example3.com", 42, 62),
                ("https://example4.com", 63, 83),
            ]

            result = self.web_manager.process_user_input(user_input)

            # Should only process max_links (2 in this case)
            self.assertEqual(result.processing_info["links_found"], 4)
            self.assertEqual(result.processing_info["links_processed"], 2)

    @patch("xandai.web.web_manager.WebManager._fetch_and_extract")
    def test_mixed_success_failure(self, mock_fetch):
        """Test scenario where some links succeed and others fail"""
        self.web_manager.max_links = 3

        # First call succeeds, second fails, third succeeds
        mock_content = ExtractedContent(
            title="Success",
            description="",
            main_content="content",
            code_blocks=[],
            links=[],
            metadata={},
            word_count=10,
        )

        mock_fetch.side_effect = [mock_content, None, mock_content]

        user_input = "Links: https://good1.com https://bad.com https://good2.com"

        with patch.object(
            self.web_manager.link_detector, "find_processable_links"
        ) as mock_detector:
            mock_detector.return_value = [
                ("https://good1.com", 0, 20),
                ("https://bad.com", 21, 35),
                ("https://good2.com", 36, 55),
            ]

            result = self.web_manager.process_user_input(user_input)

            self.assertEqual(result.processing_info["successful_extractions"], 2)
            self.assertEqual(result.processing_info["failed_extractions"], 1)
            self.assertEqual(len(result.extracted_contents), 2)


if __name__ == "__main__":
    unittest.main()
