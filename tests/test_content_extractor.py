"""
Tests for Content Extractor functionality
"""

import sys
import unittest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from xandai.web.content_extractor import ContentExtractor, ExtractedContent


class TestContentExtractor(unittest.TestCase):
    """Test content extraction from HTML"""

    def setUp(self):
        """Set up test fixtures"""
        self.extractor = ContentExtractor()

    def test_basic_content_extraction(self):
        """Test basic HTML content extraction"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Page Title</title>
            <meta name="description" content="This is a test page">
        </head>
        <body>
            <h1>Main Heading</h1>
            <p>This is the main content of the page.</p>
            <p>Another paragraph with useful information.</p>
        </body>
        </html>
        """

        result = self.extractor.extract(html_content, "https://example.com")

        self.assertIsInstance(result, ExtractedContent)
        self.assertEqual(result.title, "Test Page Title")
        self.assertEqual(result.description, "This is a test page")
        self.assertIn("main content", result.main_content)
        self.assertGreater(result.word_count, 0)

    def test_code_block_extraction(self):
        """Test extraction of code blocks"""
        html_content = """
        <html>
        <body>
            <h1>Python Tutorial</h1>
            <p>Here's how to print in Python:</p>
            <pre><code>
def hello_world():
    print("Hello, World!")
    return True
            </code></pre>
            <p>And here's a simple function:</p>
            <code>sum(1, 2)</code>
        </body>
        </html>
        """

        result = self.extractor.extract(html_content)

        self.assertGreater(len(result.code_blocks), 0)
        self.assertIn("hello_world", result.code_blocks[0])
        self.assertIn("print", result.code_blocks[0])

    def test_noise_removal(self):
        """Test removal of noise elements"""
        html_content = """
        <html>
        <body>
            <nav>Navigation menu</nav>
            <header>Site header</header>
            <main>
                <h1>Important Content</h1>
                <p>This is the main content we want.</p>
            </main>
            <sidebar class="ads">Advertisement content</sidebar>
            <footer>Site footer</footer>
            <script>console.log('script content');</script>
            <style>body { color: red; }</style>
        </body>
        </html>
        """

        result = self.extractor.extract(html_content)

        # Main content should be preserved
        self.assertIn("Important Content", result.main_content)
        self.assertIn("main content we want", result.main_content)

        # Noise should be removed
        self.assertNotIn("Navigation menu", result.main_content)
        self.assertNotIn("Advertisement", result.main_content)
        self.assertNotIn("script content", result.main_content)
        self.assertNotIn("color: red", result.main_content)

    def test_title_extraction_fallbacks(self):
        """Test title extraction with various fallback methods"""
        # Test with h1 but no title tag
        html_h1_only = """
        <html>
        <body>
            <h1>Main Page Heading</h1>
            <p>Content here</p>
        </body>
        </html>
        """

        result = self.extractor.extract(html_h1_only)
        self.assertEqual(result.title, "Main Page Heading")

        # Test with og:title
        html_og_title = """
        <html>
        <head>
            <meta property="og:title" content="OpenGraph Title">
        </head>
        <body>
            <p>Content here</p>
        </body>
        </html>
        """

        result = self.extractor.extract(html_og_title)
        self.assertEqual(result.title, "OpenGraph Title")

        # Test fallback to "Untitled"
        html_no_title = """
        <html>
        <body>
            <p>Content with no title</p>
        </body>
        </html>
        """

        result = self.extractor.extract(html_no_title)
        self.assertEqual(result.title, "Untitled")

    def test_description_extraction_fallbacks(self):
        """Test description extraction with various methods"""
        # Test meta description
        html_meta_desc = """
        <html>
        <head>
            <meta name="description" content="Page meta description">
        </head>
        <body><p>Content</p></body>
        </html>
        """

        result = self.extractor.extract(html_meta_desc)
        self.assertEqual(result.description, "Page meta description")

        # Test og:description
        html_og_desc = """
        <html>
        <head>
            <meta property="og:description" content="OpenGraph description">
        </head>
        <body><p>Content</p></body>
        </html>
        """

        result = self.extractor.extract(html_og_desc)
        self.assertEqual(result.description, "OpenGraph description")

        # Test fallback to first paragraph
        html_p_desc = """
        <html>
        <body>
            <p>This is the first paragraph that should become description.</p>
            <p>Second paragraph</p>
        </body>
        </html>
        """

        result = self.extractor.extract(html_p_desc)
        self.assertIn("first paragraph", result.description)

    def test_language_detection(self):
        """Test programming language detection"""
        # Python content
        html_python = """
        <html>
        <body>
            <h1>Python Guide</h1>
            <p>Learn python programming with Django framework</p>
            <pre><code>
import pandas as pd
def process_data():
    return pd.DataFrame()
            </code></pre>
        </body>
        </html>
        """

        result = self.extractor.extract(html_python)
        self.assertEqual(result.language, "python")

        # JavaScript content
        html_js = """
        <html>
        <body>
            <h1>JavaScript Tutorial</h1>
            <p>Learn JavaScript and React development</p>
            <pre><code>
const component = () => {
    return <div>Hello React</div>;
};
            </code></pre>
        </body>
        </html>
        """

        result = self.extractor.extract(html_js)
        self.assertEqual(result.language, "javascript")

    def test_useful_links_extraction(self):
        """Test extraction of useful links"""
        html_content = """
        <html>
        <body>
            <h1>Documentation</h1>
            <p>Useful links:</p>
            <a href="https://docs.python.org">Python Documentation</a>
            <a href="https://github.com/user/repo">Source Code</a>
            <a href="https://example.com/tutorial">Tutorial</a>
            <a href="https://example.com/random">Random Link</a>
            <a href="/internal">Internal Link</a>
        </body>
        </html>
        """

        result = self.extractor.extract(html_content, "https://example.com")

        # Should find useful links based on keywords
        useful_link_texts = [link["text"] for link in result.links]
        self.assertIn("Python Documentation", useful_link_texts)
        self.assertIn("Source Code", useful_link_texts)
        self.assertIn("Tutorial", useful_link_texts)

        # Check link categorization
        doc_links = [link for link in result.links if link["type"] == "documentation"]
        source_links = [link for link in result.links if link["type"] == "source_code"]

        self.assertGreater(len(doc_links), 0)
        self.assertGreater(len(source_links), 0)

    def test_metadata_extraction(self):
        """Test extraction of page metadata"""
        html_content = """
        <html>
        <head>
            <meta name="author" content="John Doe">
            <meta name="keywords" content="python, programming, tutorial">
            <meta property="og:type" content="article">
            <meta property="og:site_name" content="Example Site">
            <meta name="generator" content="Jekyll">
        </head>
        <body>
            <h1>Content</h1>
        </body>
        </html>
        """

        result = self.extractor.extract(html_content)

        self.assertIn("author", result.metadata)
        self.assertIn("keywords", result.metadata)
        self.assertIn("og:type", result.metadata)
        self.assertEqual(result.metadata["author"], "John Doe")
        self.assertEqual(result.metadata["keywords"], "python, programming, tutorial")

    def test_main_content_selectors(self):
        """Test main content area detection"""
        # Test with <main> tag
        html_main = """
        <html>
        <body>
            <header>Header content</header>
            <main>
                <h1>Main Article</h1>
                <p>This is the main content area.</p>
            </main>
            <footer>Footer content</footer>
        </body>
        </html>
        """

        result = self.extractor.extract(html_main)
        self.assertIn("Main Article", result.main_content)
        self.assertIn("main content area", result.main_content)
        self.assertNotIn("Header content", result.main_content)
        self.assertNotIn("Footer content", result.main_content)

        # Test with article tag
        html_article = """
        <html>
        <body>
            <nav>Navigation</nav>
            <article>
                <h2>Article Title</h2>
                <p>Article content goes here.</p>
            </article>
        </body>
        </html>
        """

        result = self.extractor.extract(html_article)
        self.assertIn("Article Title", result.main_content)
        self.assertIn("Article content", result.main_content)
        self.assertNotIn("Navigation", result.main_content)

    def test_content_size_limits(self):
        """Test content size limiting"""
        # Test with very long content
        long_paragraph = "Very long content. " * 500  # ~10,000 characters
        html_long = f"""
        <html>
        <body>
            <h1>Long Content</h1>
            <p>{long_paragraph}</p>
        </body>
        </html>
        """

        result = self.extractor.extract(html_long)

        # Main content should be limited
        self.assertLessEqual(len(result.main_content), 5000)

        # Very long code blocks should be excluded
        very_long_code = "print('code line')\n" * 200  # ~3000 characters
        html_long_code = f"""
        <html>
        <body>
            <pre><code>{very_long_code}</code></pre>
        </body>
        </html>
        """

        result = self.extractor.extract(html_long_code)
        # Code blocks over 2000 chars should be excluded
        for code in result.code_blocks:
            self.assertLessEqual(len(code), 2000)

    def test_text_cleaning(self):
        """Test text cleaning functionality"""
        messy_text = """
        This    has     multiple     spaces.



        And many newlines.


        Should be cleaned.
        """

        cleaned = self.extractor._clean_text(messy_text)

        # Multiple spaces should be reduced to single spaces
        self.assertNotIn("    ", cleaned)
        self.assertNotIn("     ", cleaned)

        # Excessive newlines should be reduced
        self.assertNotIn("\n\n\n\n", cleaned)

        # Content should still be readable
        self.assertIn("multiple spaces", cleaned)
        self.assertIn("Should be cleaned", cleaned)

    def test_empty_and_malformed_html(self):
        """Test handling of empty or malformed HTML"""
        # Empty HTML
        result = self.extractor.extract("")
        self.assertEqual(result.title, "Untitled")
        self.assertEqual(result.word_count, 0)

        # Malformed HTML
        malformed_html = "<html><body><h1>Unclosed tag<p>Content"
        result = self.extractor.extract(malformed_html)

        # Should still extract something
        self.assertIsNotNone(result.title)
        self.assertGreaterEqual(result.word_count, 0)

    def test_word_count_accuracy(self):
        """Test word count calculation"""
        html_content = """
        <html>
        <body>
            <h1>Test Title</h1>
            <p>This paragraph has exactly ten words in total.</p>
            <p>Another sentence with five words.</p>
        </body>
        </html>
        """

        result = self.extractor.extract(html_content)

        # Should count words in main content (excluding title)
        # "This paragraph has exactly ten words in total. Another sentence with five words."
        # = 15 words approximately (may vary slightly due to text processing)
        self.assertGreater(result.word_count, 10)
        self.assertLess(result.word_count, 25)  # Reasonable upper bound


class TestContentExtractorEdgeCases(unittest.TestCase):
    """Test edge cases for ContentExtractor"""

    def setUp(self):
        self.extractor = ContentExtractor()

    def test_unicode_content_handling(self):
        """Test handling of Unicode content"""
        unicode_html = """
        <html>
        <body>
            <h1>测试页面</h1>
            <p>This page contains émojis: 🚀 🎉 and special chars: café naïve résumé</p>
            <p>Russian: Привет мир</p>
            <p>Japanese: こんにちは世界</p>
        </body>
        </html>
        """

        result = self.extractor.extract(unicode_html)

        self.assertEqual(result.title, "测试页面")
        self.assertIn("🚀", result.main_content)
        self.assertIn("café", result.main_content)
        self.assertIn("Привет", result.main_content)
        self.assertIn("こんにちは", result.main_content)

    def test_deeply_nested_content(self):
        """Test extraction from deeply nested HTML structures"""
        nested_html = """
        <html>
        <body>
            <div class="container">
                <div class="wrapper">
                    <section class="content">
                        <article class="post">
                            <div class="post-content">
                                <h1>Deeply Nested Title</h1>
                                <div class="text-content">
                                    <p>This content is deeply nested in the HTML structure.</p>
                                </div>
                            </div>
                        </article>
                    </section>
                </div>
            </div>
        </body>
        </html>
        """

        result = self.extractor.extract(nested_html)

        self.assertEqual(result.title, "Deeply Nested Title")
        self.assertIn("deeply nested", result.main_content)

    def test_multiple_code_languages(self):
        """Test detection with multiple programming languages"""
        multi_lang_html = """
        <html>
        <body>
            <h1>Multi-Language Guide</h1>
            <p>Python and JavaScript examples</p>
            <pre class="python"><code>
def python_func():
    import django
    return "Python"
            </code></pre>
            <pre class="javascript"><code>
const jsFunc = () => {
    const react = require('react');
    return 'JavaScript';
};
            </code></pre>
        </body>
        </html>
        """

        result = self.extractor.extract(multi_lang_html)

        # Should detect the more prominent language or first one
        self.assertIn(result.language, ["python", "javascript"])
        self.assertEqual(len(result.code_blocks), 2)


if __name__ == "__main__":
    unittest.main()
