"""
Tests for Web Fetcher functionality
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import requests

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from xandai.web.web_fetcher import FetchResult, WebFetcher


class TestWebFetcher(unittest.TestCase):
    """Test web fetching functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.fetcher = WebFetcher(timeout=5, max_retries=1)

    def tearDown(self):
        """Clean up after tests"""
        self.fetcher.close()

    def test_fetcher_initialization(self):
        """Test WebFetcher initializes correctly"""
        self.assertEqual(self.fetcher.timeout, 5)
        self.assertEqual(self.fetcher.max_retries, 1)
        self.assertIsNotNone(self.fetcher.session)

    def test_successful_fetch_result_structure(self):
        """Test FetchResult structure"""
        # Test successful result
        success_result = FetchResult(
            success=True,
            url="https://example.com",
            content="<html>test</html>",
            status_code=200,
            headers={"content-type": "text/html"},
            response_time=0.5,
        )

        self.assertTrue(success_result.success)
        self.assertEqual(success_result.url, "https://example.com")
        self.assertIsNotNone(success_result.content)
        self.assertEqual(success_result.status_code, 200)

        # Test failed result
        failed_result = FetchResult(
            success=False, url="https://example.com", error_message="Connection failed"
        )

        self.assertFalse(failed_result.success)
        self.assertIsNotNone(failed_result.error_message)

    @patch("xandai.web.web_fetcher.requests.Session.get")
    def test_successful_fetch(self, mock_get):
        """Test successful web fetch"""
        # Mock successful response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.url = "https://example.com"
        mock_response.text = "<html><body>Test content</body></html>"
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/html; charset=utf-8"}
        mock_response.encoding = "utf-8"

        mock_get.return_value = mock_response

        result = self.fetcher.fetch("https://example.com")

        self.assertTrue(result.success)
        self.assertEqual(result.url, "https://example.com")
        self.assertIn("Test content", result.content)
        self.assertEqual(result.status_code, 200)
        self.assertIsNone(result.error_message)

    @patch("xandai.web.web_fetcher.requests.Session.get")
    def test_http_error_handling(self, mock_get):
        """Test handling of HTTP errors"""
        # Mock HTTP error
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")

        mock_get.return_value = mock_response

        result = self.fetcher.fetch("https://example.com/nonexistent")

        self.assertFalse(result.success)
        self.assertIsNotNone(result.error_message)
        self.assertIn("404", result.error_message)

    @patch("xandai.web.web_fetcher.requests.Session.get")
    def test_connection_error_handling(self, mock_get):
        """Test handling of connection errors"""
        # Mock connection error
        mock_get.side_effect = requests.ConnectionError("Connection refused")

        result = self.fetcher.fetch("https://unreachable.example.com")

        self.assertFalse(result.success)
        self.assertIsNotNone(result.error_message)
        self.assertIn("Connection failed", result.error_message)

    @patch("xandai.web.web_fetcher.requests.Session.get")
    def test_timeout_handling(self, mock_get):
        """Test handling of timeouts"""
        # Mock timeout
        mock_get.side_effect = requests.Timeout("Request timed out")

        result = self.fetcher.fetch("https://slow.example.com")

        self.assertFalse(result.success)
        self.assertIsNotNone(result.error_message)
        self.assertIn("Connection failed", result.error_message)

    @patch("xandai.web.web_fetcher.requests.Session.get")
    def test_retry_logic(self, mock_get):
        """Test retry logic for temporary failures"""
        fetcher_with_retries = WebFetcher(timeout=5, max_retries=2)

        # First call fails, second succeeds
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.url = "https://example.com"
        mock_response.text = "Success after retry"
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/html"}
        mock_response.encoding = "utf-8"

        mock_get.side_effect = [
            requests.ConnectionError("First attempt fails"),
            mock_response,  # Second attempt succeeds
        ]

        result = fetcher_with_retries.fetch("https://example.com")

        self.assertTrue(result.success)
        self.assertEqual(mock_get.call_count, 2)

        fetcher_with_retries.close()

    @patch("xandai.web.web_fetcher.requests.Session.get")
    def test_content_type_validation(self, mock_get):
        """Test content type validation"""
        # Test unsupported content type
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.url = "https://example.com/image.jpg"
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "image/jpeg"}

        mock_get.return_value = mock_response

        result = self.fetcher.fetch("https://example.com/image.jpg")

        self.assertFalse(result.success)
        self.assertIn("Unsupported content type", result.error_message)

    @patch("xandai.web.web_fetcher.requests.Session.get")
    def test_content_size_validation(self, mock_get):
        """Test content size validation"""
        # Test content too large
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.url = "https://example.com/large-file"
        mock_response.status_code = 200
        mock_response.headers = {
            "content-type": "text/html",
            "content-length": str(15 * 1024 * 1024),  # 15MB > 10MB limit
        }

        mock_get.return_value = mock_response

        result = self.fetcher.fetch("https://example.com/large-file")

        self.assertFalse(result.success)
        self.assertIn("Content too large", result.error_message)

    @patch("xandai.web.web_fetcher.requests.Session.get")
    def test_encoding_handling(self, mock_get):
        """Test proper encoding handling"""
        # Test response with no encoding specified
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.url = "https://example.com"
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/html"}
        mock_response.encoding = None  # No encoding specified
        mock_response.text = "Content with special chars: café naïve résumé"
        mock_response.content = (
            b"Content with special chars: caf\xc3\xa9 na\xc3\xafve r\xc3\xa9sum\xc3\xa9"
        )

        mock_get.return_value = mock_response

        result = self.fetcher.fetch("https://example.com")

        self.assertTrue(result.success)
        self.assertIn("café", result.content)  # Should handle UTF-8 properly

    def test_processable_content_types(self):
        """Test content type validation logic"""
        processable_types = [
            "text/html",
            "text/html; charset=utf-8",
            "application/xhtml+xml",
            "text/plain",
            "application/xml",
            "text/xml",
        ]

        non_processable_types = [
            "image/jpeg",
            "application/pdf",
            "video/mp4",
            "application/octet-stream",
            "text/css",  # CSS is text but not processable content
            "application/javascript",
        ]

        for content_type in processable_types:
            with self.subTest(content_type=content_type):
                self.assertTrue(
                    self.fetcher._is_processable_content_type(content_type),
                    f"Should be processable: {content_type}",
                )

        for content_type in non_processable_types:
            with self.subTest(content_type=content_type):
                self.assertFalse(
                    self.fetcher._is_processable_content_type(content_type),
                    f"Should not be processable: {content_type}",
                )

    def test_response_time_tracking(self):
        """Test that response time is tracked"""
        with patch("xandai.web.web_fetcher.time.time") as mock_time:
            mock_time.side_effect = [0.0, 0.5]  # Start and end times

            with patch.object(self.fetcher, "_attempt_fetch") as mock_attempt:
                mock_result = FetchResult(success=True, url="https://example.com", content="test")
                mock_attempt.return_value = mock_result

                result = self.fetcher.fetch("https://example.com")

                self.assertEqual(result.response_time, 0.5)


class TestWebFetcherEdgeCases(unittest.TestCase):
    """Test edge cases and error scenarios for WebFetcher"""

    def setUp(self):
        self.fetcher = WebFetcher()

    def tearDown(self):
        self.fetcher.close()

    @patch("xandai.web.web_fetcher.requests.Session.get")
    def test_unicode_decode_error_handling(self, mock_get):
        """Test handling of Unicode decode errors"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.url = "https://example.com"
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/html"}
        mock_response.encoding = None

        # Simulate UnicodeDecodeError
        mock_response.text = Mock()
        mock_response.text.__str__ = Mock(
            side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "test error")
        )
        mock_response.content = b"Test content with problematic encoding"

        mock_get.return_value = mock_response

        result = self.fetcher.fetch("https://example.com")

        # Should handle the error gracefully and use fallback decoding
        self.assertTrue(result.success)
        self.assertIsNotNone(result.content)

    def test_custom_headers(self):
        """Test that custom headers are set properly"""
        # Check that user-agent and other headers are set
        headers = self.fetcher.session.headers

        self.assertIn("User-Agent", headers)
        self.assertIn("Mozilla", headers["User-Agent"])  # Should look like a real browser
        self.assertIn("Accept", headers)
        self.assertIn("Accept-Language", headers)


if __name__ == "__main__":
    unittest.main()
