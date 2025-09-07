"""
Content Extraction Module

Extrai informações relevantes de páginas web usando BeautifulSoup4.
Foca em conteúdo útil para assistência de código e documentação.
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup, NavigableString


@dataclass
class ExtractedContent:
    """Conteúdo extraído de uma página web"""

    title: str
    description: str
    main_content: str
    code_blocks: List[str]
    links: List[Dict[str, str]]
    metadata: Dict[str, Any]
    word_count: int
    language: Optional[str] = None


class ContentExtractor:
    """
    Extrator inteligente de conteúdo web

    Foca em extrair informações úteis para assistência de código:
    - Documentação técnica
    - Tutoriais e guides
    - Código de exemplo
    - APIs e referências
    """

    # Tags que normalmente contêm conteúdo principal
    MAIN_CONTENT_SELECTORS = [
        "main",
        "article",
        ".content",
        ".main-content",
        ".post-content",
        ".entry-content",
        "#content",
        "#main",
        ".documentation",
        ".readme",
        ".wiki-content",
    ]

    # Tags a serem removidas (noise)
    NOISE_SELECTORS = [
        "nav",
        "footer",
        "header",
        ".navigation",
        ".sidebar",
        ".ads",
        ".advertisement",
        ".popup",
        ".modal",
        ".cookie-banner",
        "script",
        "style",
        "noscript",
    ]

    # Selectors for code content
    CODE_SELECTORS = ["pre", "code", ".highlight", ".code-block", ".language-*", ".hljs"]

    def __init__(self):
        self.soup = None

    def extract(self, html_content: str, url: str = "") -> ExtractedContent:
        """
        Extrai conteúdo estruturado de HTML

        Args:
            html_content: Conteúdo HTML da página
            url: URL original (para contexto)

        Returns:
            ExtractedContent com informações extraídas
        """
        self.soup = BeautifulSoup(html_content, "html.parser")

        # Remove noise
        self._remove_noise_elements()

        # Extract components
        title = self._extract_title()
        description = self._extract_description()
        main_content = self._extract_main_content()
        code_blocks = self._extract_code_blocks()
        links = self._extract_useful_links(url)
        metadata = self._extract_metadata()

        # Calculate word count of main content
        word_count = len(main_content.split()) if main_content else 0

        # Detect language/technology
        language = self._detect_language()

        return ExtractedContent(
            title=title,
            description=description,
            main_content=main_content,
            code_blocks=code_blocks,
            links=links,
            metadata=metadata,
            word_count=word_count,
            language=language,
        )

    def _remove_noise_elements(self):
        """Remove elementos que são ruído (nav, ads, etc.)"""
        for selector in self.NOISE_SELECTORS:
            for element in self.soup.select(selector):
                element.decompose()

    def _extract_title(self) -> str:
        """Extrai título da página"""
        # Try multiple title sources
        title_sources = [
            ("h1", lambda x: x.get_text().strip()),
            ("title", lambda x: x.get_text().strip()),
            (".page-title", lambda x: x.get_text().strip()),
            (".post-title", lambda x: x.get_text().strip()),
            ('meta[property="og:title"]', lambda x: x.get("content", "")),
        ]

        for selector, extractor in title_sources:
            elements = self.soup.select(selector)
            if elements:
                title = extractor(elements[0])
                if title and len(title) > 3:
                    return title[:200]  # Limit title length

        return "Untitled"

    def _extract_description(self) -> str:
        """Extrai descrição/resumo da página"""
        # Try multiple description sources
        desc_sources = [
            ('meta[name="description"]', lambda x: x.get("content", "")),
            ('meta[property="og:description"]', lambda x: x.get("content", "")),
            (".summary", lambda x: x.get_text().strip()),
            (".intro", lambda x: x.get_text().strip()),
            ("p", lambda x: x.get_text().strip()),
        ]

        for selector, extractor in desc_sources:
            elements = self.soup.select(selector)
            if elements:
                desc = extractor(elements[0])
                if desc and len(desc) > 20:
                    return desc[:500]  # Limit description length

        return ""

    def _extract_main_content(self) -> str:
        """Extrai conteúdo principal da página"""
        main_text = ""

        # Try to find main content container
        for selector in self.MAIN_CONTENT_SELECTORS:
            main_container = self.soup.select_one(selector)
            if main_container:
                main_text = self._extract_text_from_element(main_container)
                if len(main_text) > 100:  # Must have substantial content
                    break

        # Fallback: extract from body if no main container found
        if not main_text or len(main_text) < 100:
            body = self.soup.find("body")
            if body:
                main_text = self._extract_text_from_element(body)

        # Clean and limit text
        main_text = self._clean_text(main_text)
        return main_text[:5000]  # Limit content length

    def _extract_text_from_element(self, element) -> str:
        """Extrai texto limpo de um elemento, preservando estrutura básica"""
        text_parts = []

        for elem in element.descendants:
            if isinstance(elem, NavigableString):
                text = str(elem).strip()
                if text:
                    text_parts.append(text)
            elif elem.name in ["br", "p", "div", "h1", "h2", "h3", "h4", "h5", "h6"]:
                text_parts.append("\n")

        return " ".join(text_parts)

    def _extract_code_blocks(self) -> List[str]:
        """Extrai blocos de código da página"""
        code_blocks = []

        # Find all code elements
        for selector in ["pre", "code", ".highlight", ".code-block"]:
            elements = self.soup.select(selector)
            for element in elements:
                code_text = element.get_text().strip()
                if code_text and len(code_text) > 5:  # Must have meaningful code
                    # Limit code block size
                    if len(code_text) <= 2000:
                        code_blocks.append(code_text)

        # Remove duplicates while preserving order
        seen = set()
        unique_blocks = []
        for block in code_blocks:
            if block not in seen:
                seen.add(block)
                unique_blocks.append(block)

        return unique_blocks[:10]  # Limit number of code blocks

    def _extract_useful_links(self, base_url: str) -> List[Dict[str, str]]:
        """Extrai links úteis (documentação, exemplos, etc.)"""
        useful_links = []

        # Keywords that indicate useful links
        useful_keywords = [
            "documentation",
            "docs",
            "guide",
            "tutorial",
            "example",
            "api",
            "reference",
            "manual",
            "readme",
            "github",
            "source",
        ]

        links = self.soup.find_all("a", href=True)
        for link in links:
            href = link.get("href", "")
            text = link.get_text().strip()

            if href and text:
                # Check if link seems useful
                link_useful = any(
                    keyword in href.lower() or keyword in text.lower()
                    for keyword in useful_keywords
                )

                if link_useful:
                    useful_links.append(
                        {
                            "url": href,
                            "text": text[:100],  # Limit text length
                            "type": self._categorize_link(href, text),
                        }
                    )

        return useful_links[:10]  # Limit number of links

    def _categorize_link(self, url: str, text: str) -> str:
        """Categoriza tipo do link baseado na URL e texto"""
        url_lower = url.lower()
        text_lower = text.lower()

        if "github.com" in url_lower or "gitlab.com" in url_lower:
            return "source_code"
        elif any(word in url_lower or word in text_lower for word in ["doc", "guide", "manual"]):
            return "documentation"
        elif any(word in url_lower or word in text_lower for word in ["example", "demo", "sample"]):
            return "example"
        elif any(word in url_lower or word in text_lower for word in ["api", "reference"]):
            return "reference"
        else:
            return "general"

    def _extract_metadata(self) -> Dict[str, Any]:
        """Extrai metadados úteis da página"""
        metadata = {}

        # Meta tags
        meta_tags = self.soup.find_all("meta")
        for tag in meta_tags:
            name = tag.get("name") or tag.get("property") or tag.get("itemprop")
            content = tag.get("content")
            if name and content:
                metadata[name] = content

        # Specific useful metadata
        useful_meta = [
            "author",
            "keywords",
            "language",
            "generator",
            "og:type",
            "og:site_name",
            "article:author",
            "article:published_time",
            "article:modified_time",
        ]

        return {key: value for key, value in metadata.items() if key in useful_meta}

    def _detect_language(self) -> Optional[str]:
        """Detecta linguagem/tecnologia principal baseada no conteúdo"""
        if not self.soup:
            return None

        # Check for language indicators in code blocks
        code_elements = self.soup.select("pre, code, .highlight")

        language_indicators = {
            "python": ["python", "py", "django", "flask", "pandas"],
            "javascript": ["javascript", "js", "node", "react", "vue", "angular"],
            "java": ["java", "spring", "maven", "gradle"],
            "csharp": ["c#", "csharp", ".net", "dotnet"],
            "cpp": ["c++", "cpp", "cxx"],
            "go": ["golang", "go"],
            "rust": ["rust", "cargo"],
            "php": ["php", "laravel", "symfony"],
            "ruby": ["ruby", "rails"],
            "sql": ["sql", "mysql", "postgresql", "sqlite"],
        }

        text_content = self.soup.get_text().lower()

        for lang, keywords in language_indicators.items():
            if any(keyword in text_content for keyword in keywords):
                return lang

        return None

    def _clean_text(self, text: str) -> str:
        """Limpa texto removendo espaços em excesso e caracteres especiais"""
        # Remove multiple whitespaces
        text = re.sub(r"\s+", " ", text)

        # Remove excessive newlines
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)

        return text.strip()
