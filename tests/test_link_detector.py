"""
Tests for Link Detection functionality
"""

import sys
import unittest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from xandai.web.link_detector import LinkDetector


class TestLinkDetector(unittest.TestCase):
    """Test link detection and validation"""

    def setUp(self):
        """Set up test fixtures"""
        self.detector = LinkDetector()

    def test_basic_link_detection(self):
        """Test basic HTTP/HTTPS link detection"""
        test_cases = [
            ("Visit https://example.com for more info", 1),
            ("Check http://test.org and https://demo.net", 2),
            ("No links in this text", 0),
            ("https://python.org/docs", 1),
        ]

        for text, expected_count in test_cases:
            with self.subTest(text=text):
                links = self.detector.find_processable_links(text)
                self.assertEqual(len(links), expected_count)

    def test_domain_only_links(self):
        """Test detection of domain-only links (no protocol)"""
        test_cases = [
            ("Visit python.org for documentation", 1),
            ("Check github.com/user/repo", 1),
            ("Sites: reddit.com and stackoverflow.com", 2),
            ("Email: user@domain.com (should not match)", 0),
        ]

        for text, expected_count in test_cases:
            with self.subTest(text=text):
                links = self.detector.find_processable_links(text)
                self.assertEqual(len(links), expected_count)

    def test_shell_command_avoidance(self):
        """Test that links in shell commands are NOT processed"""
        shell_commands = [
            "git clone https://github.com/user/repo.git",
            "curl -O https://example.com/file.zip",
            "wget https://download.site.com/archive.tar.gz",
            "npm install https://github.com/package/name",
            "pip install git+https://github.com/user/repo.git",
            "docker pull registry.com/image:tag",
            "Run: ansible-playbook -i https://config.com/hosts.yml",
        ]

        for command in shell_commands:
            with self.subTest(command=command):
                links = self.detector.find_processable_links(command)
                self.assertEqual(len(links), 0, f"Should not process links in: {command}")

    def test_context_based_avoidance(self):
        """Test context-based link avoidance"""
        avoid_contexts = [
            "Example: git clone https://github.com/repo",
            "Usage: curl https://api.example.com",
            "Command: wget https://files.com/data.json",
            "Execute: docker run image https://config.com",
            "$ git clone https://github.com/user/repo",
            "# Download from https://site.com/file",
            "> curl https://example.com/api",
        ]

        for text in avoid_contexts:
            with self.subTest(text=text):
                links = self.detector.find_processable_links(text)
                self.assertEqual(len(links), 0, f"Should avoid: {text}")

    def test_quoted_links_avoidance(self):
        """Test that quoted links are avoided"""
        quoted_cases = [
            'See "https://example.com" for details',
            "Run 'curl https://api.com/data'",
            "Use `https://docs.site.com` as reference",
        ]

        for text in quoted_cases:
            with self.subTest(text=text):
                links = self.detector.find_processable_links(text)
                self.assertEqual(len(links), 0, f"Should avoid quoted: {text}")

    def test_processable_links(self):
        """Test links that SHOULD be processed"""
        processable_cases = [
            "Check out this tutorial: https://python.org/tutorial",
            "Great documentation at docs.python.org",
            "I found this helpful: github.com/user/awesome-repo",
            "Reference: https://stackoverflow.com/questions/123456",
            "Learn more: developer.mozilla.org/docs",
        ]

        for text in processable_cases:
            with self.subTest(text=text):
                links = self.detector.find_processable_links(text)
                self.assertGreater(len(links), 0, f"Should process: {text}")

    def test_url_normalization(self):
        """Test URL normalization functionality"""
        test_cases = [
            ("example.com", "https://example.com"),
            ("http://example.com", "http://example.com"),
            ("https://example.com", "https://example.com"),
            ("github.com/user/repo", "https://github.com/user/repo"),
        ]

        for input_url, expected_output in test_cases:
            with self.subTest(input_url=input_url):
                normalized = self.detector.normalize_url(input_url)
                self.assertEqual(normalized, expected_output)

    def test_url_validation(self):
        """Test URL validation"""
        valid_urls = [
            "https://example.com",
            "http://test.org",
            "https://github.com/user/repo",
            "http://subdomain.example.com/path",
        ]

        invalid_urls = [
            "not-a-url",
            "ftp://example.com",  # Wrong protocol
            "https://",  # No domain
            "example",  # No TLD
            "",  # Empty
        ]

        for url in valid_urls:
            with self.subTest(url=url):
                self.assertTrue(self.detector._is_valid_url(url))

        for url in invalid_urls:
            with self.subTest(url=url):
                self.assertFalse(self.detector._is_valid_url(url))

    def test_link_positions(self):
        """Test that link positions are correctly identified"""
        text = "Start https://first.com middle https://second.com end"
        links = self.detector.find_processable_links(text)

        self.assertEqual(len(links), 2)

        # Check first link
        url1, start1, end1 = links[0]
        self.assertEqual(url1, "https://first.com")
        self.assertEqual(text[start1:end1], "https://first.com")

        # Check second link
        url2, start2, end2 = links[1]
        self.assertEqual(url2, "https://second.com")
        self.assertEqual(text[start2:end2], "https://second.com")

    def test_edge_cases(self):
        """Test edge cases and unusual scenarios"""
        edge_cases = [
            ("", 0),  # Empty string
            ("   ", 0),  # Whitespace only
            ("https://", 0),  # Incomplete URL
            ("Multiple dots... but no links", 0),
            ("URL with trailing punctuation: https://example.com.", 1),
            ("URL in parentheses (https://example.com)", 1),
        ]

        for text, expected_count in edge_cases:
            with self.subTest(text=text):
                links = self.detector.find_processable_links(text)
                self.assertEqual(len(links), expected_count)


class TestLinkDetectorPerformance(unittest.TestCase):
    """Test performance and scalability of link detector"""

    def setUp(self):
        self.detector = LinkDetector()

    def test_large_text_processing(self):
        """Test processing of large text blocks"""
        # Create a large text with multiple links
        base_text = "This is a test with https://example.com and some more text. "
        large_text = base_text * 100  # ~6000 characters

        # Should complete quickly and find all links
        links = self.detector.find_processable_links(large_text)
        self.assertEqual(len(links), 100)  # One link per repetition

    def test_many_links_processing(self):
        """Test processing text with many links"""
        # Create text with many different links
        links_text = " ".join([f"https://example{i}.com" for i in range(50)])

        detected_links = self.detector.find_processable_links(links_text)
        self.assertEqual(len(detected_links), 50)


if __name__ == "__main__":
    unittest.main()
