"""
Content Extractor

Advanced content extraction from HTML.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional

from bs4 import BeautifulSoup, Tag


@dataclass
class ExtractedContent:
    """Container for extracted web content"""

    url: str
    title: str
    text_content: str
    code_blocks: List[Dict[str, str]]
    links: List[str]
    images: List[str]
    metadata: Dict[str, str]

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "url": self.url,
            "title": self.title,
            "text_content": self.text_content,
            "code_blocks": self.code_blocks,
            "links": self.links,
            "images": self.images,
            "metadata": self.metadata,
        }


class ContentExtractor:
    """
    Content Extractor

    Extracts structured content from HTML.
    """

    def __init__(self):
        """Initialize content extractor"""
        pass

    def extract_code_blocks(self, html: str) -> List[Dict[str, str]]:
        """
        Extract code blocks from HTML

        Args:
            html: HTML content

        Returns:
            List of code blocks with language and content
        """
        soup = BeautifulSoup(html, "html.parser")
        code_blocks = []

        # Find <pre><code> blocks
        for pre in soup.find_all("pre"):
            code = pre.find("code")
            if code:
                language = self._detect_language(code)
                content = code.get_text()

                code_blocks.append({"language": language, "content": content})

        # Find standalone <code> blocks
        for code in soup.find_all("code"):
            if code.parent.name != "pre":
                content = code.get_text()
                if len(content) > 20:  # Only significant code blocks
                    code_blocks.append({"language": "unknown", "content": content})

        return code_blocks

    def extract_tables(self, html: str) -> List[List[List[str]]]:
        """
        Extract tables from HTML

        Args:
            html: HTML content

        Returns:
            List of tables (each table is list of rows)
        """
        soup = BeautifulSoup(html, "html.parser")
        tables = []

        for table in soup.find_all("table"):
            rows = []

            for tr in table.find_all("tr"):
                cells = []
                for td in tr.find_all(["td", "th"]):
                    cells.append(td.get_text(strip=True))
                if cells:
                    rows.append(cells)

            if rows:
                tables.append(rows)

        return tables

    def extract_lists(self, html: str) -> Dict[str, List[str]]:
        """
        Extract lists from HTML

        Args:
            html: HTML content

        Returns:
            Dict with 'ordered' and 'unordered' lists
        """
        soup = BeautifulSoup(html, "html.parser")

        ordered = []
        unordered = []

        for ol in soup.find_all("ol"):
            items = [li.get_text(strip=True) for li in ol.find_all("li", recursive=False)]
            if items:
                ordered.append(items)

        for ul in soup.find_all("ul"):
            items = [li.get_text(strip=True) for li in ul.find_all("li", recursive=False)]
            if items:
                unordered.append(items)

        return {"ordered": ordered, "unordered": unordered}

    def extract_headings(self, html: str) -> Dict[str, List[str]]:
        """
        Extract headings from HTML

        Args:
            html: HTML content

        Returns:
            Dict with headings by level (h1, h2, etc.)
        """
        soup = BeautifulSoup(html, "html.parser")
        headings = {}

        for i in range(1, 7):
            tag = f"h{i}"
            found = [h.get_text(strip=True) for h in soup.find_all(tag)]
            if found:
                headings[tag] = found

        return headings

    def extract_images_with_context(self, html: str, base_url: str = "") -> List[Dict[str, str]]:
        """
        Extract images with surrounding context

        Args:
            html: HTML content
            base_url: Base URL for relative links

        Returns:
            List of image dicts with src, alt, and context
        """
        soup = BeautifulSoup(html, "html.parser")
        images = []

        for img in soup.find_all("img"):
            src = img.get("src", "")
            alt = img.get("alt", "")

            # Get surrounding text for context
            parent = img.parent
            context = ""
            if parent:
                context = parent.get_text(strip=True)[:200]  # First 200 chars

            images.append({"src": src, "alt": alt, "context": context})

        return images

    def to_markdown(self, html: str) -> str:
        """
        Convert HTML to Markdown

        Args:
            html: HTML content

        Returns:
            Markdown text
        """
        soup = BeautifulSoup(html, "html.parser")

        # This is a simple conversion
        # For production, use a library like html2text

        md_lines = []

        # Convert headings
        for i in range(1, 7):
            for h in soup.find_all(f"h{i}"):
                prefix = "#" * i
                md_lines.append(f"{prefix} {h.get_text(strip=True)}\n")
                h.decompose()

        # Convert paragraphs
        for p in soup.find_all("p"):
            md_lines.append(f"{p.get_text(strip=True)}\n")

        # Convert lists
        for ul in soup.find_all("ul"):
            for li in ul.find_all("li", recursive=False):
                md_lines.append(f"- {li.get_text(strip=True)}")
            md_lines.append("")

        for ol in soup.find_all("ol"):
            for i, li in enumerate(ol.find_all("li", recursive=False), 1):
                md_lines.append(f"{i}. {li.get_text(strip=True)}")
            md_lines.append("")

        return "\n".join(md_lines)

    def _detect_language(self, code_tag: Tag) -> str:
        """Detect programming language from code tag"""
        # Check class attribute
        classes = code_tag.get("class", [])
        for cls in classes:
            if cls.startswith("language-"):
                return cls.replace("language-", "")
            elif cls.startswith("lang-"):
                return cls.replace("lang-", "")

        # Try parent's class
        if code_tag.parent:
            classes = code_tag.parent.get("class", [])
            for cls in classes:
                if cls.startswith("language-"):
                    return cls.replace("language-", "")

        return "unknown"
