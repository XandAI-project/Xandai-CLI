"""
Web Fetcher

Smart web content fetching with caching and rate limiting.
"""

import hashlib
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup


@dataclass
class FetchResult:
    """Result of a web fetch operation"""

    success: bool
    content: Optional["WebContent"] = None
    error: Optional[str] = None
    status_code: int = 0


@dataclass
class WebContent:
    """Web content container"""

    url: str
    title: str
    content: str
    html: str
    links: list
    images: list
    metadata: Dict[str, str]
    status_code: int

    def to_markdown(self) -> str:
        """Convert to markdown format"""
        md = f"# {self.title}\n\n"
        md += f"**URL**: {self.url}\n\n"
        md += "---\n\n"
        md += self.content
        return md


class WebFetcher:
    """
    Web Fetcher

    Fetches web content with respect for robots.txt and rate limiting.
    """

    def __init__(
        self,
        cache_dir: Optional[str] = None,
        rate_limit: float = 1.0,
        timeout: int = 10,
        user_agent: str = "XandAI/1.0",
    ):
        """
        Initialize web fetcher

        Args:
            cache_dir: Cache directory path
            rate_limit: Minimum seconds between requests
            timeout: Request timeout
            user_agent: User agent string
        """
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            home = Path.home()
            self.cache_dir = home / ".xandai" / "web_cache"

        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.rate_limit = rate_limit
        self.timeout = timeout
        self.user_agent = user_agent
        self.last_request_time = {}
        self.robots_parsers = {}

    def fetch(
        self, url: str, use_cache: bool = True, respect_robots: bool = True
    ) -> Optional[WebContent]:
        """
        Fetch web content

        Args:
            url: URL to fetch
            use_cache: Use cached content if available
            respect_robots: Respect robots.txt

        Returns:
            WebContent or None
        """
        # Check cache
        if use_cache:
            cached = self._get_cached(url)
            if cached:
                return cached

        # Check robots.txt
        if respect_robots and not self._can_fetch(url):
            return None

        # Rate limiting
        self._rate_limit(url)

        try:
            # Fetch content
            headers = {"User-Agent": self.user_agent}
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()

            # Parse content
            soup = BeautifulSoup(response.content, "html.parser")

            # Extract title
            title = soup.title.string if soup.title else urlparse(url).path

            # Extract main content (simple heuristic)
            content = self._extract_text(soup)

            # Extract links
            links = [urljoin(url, a.get("href")) for a in soup.find_all("a", href=True)]

            # Extract images
            images = [urljoin(url, img.get("src")) for img in soup.find_all("img", src=True)]

            # Extract metadata
            metadata = self._extract_metadata(soup)

            web_content = WebContent(
                url=url,
                title=title.strip() if title else "Untitled",
                content=content,
                html=str(soup),
                links=links,
                images=images,
                metadata=metadata,
                status_code=response.status_code,
            )

            # Cache content
            if use_cache:
                self._cache_content(url, web_content)

            return web_content

        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def _can_fetch(self, url: str) -> bool:
        """Check if URL can be fetched according to robots.txt"""
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"

        if domain not in self.robots_parsers:
            robots_parser = RobotFileParser()
            robots_parser.set_url(urljoin(domain, "/robots.txt"))
            try:
                robots_parser.read()
                self.robots_parsers[domain] = robots_parser
            except:
                # If robots.txt cannot be fetched, allow crawling
                return True

        return self.robots_parsers[domain].can_fetch(self.user_agent, url)

    def _rate_limit(self, url: str):
        """Apply rate limiting"""
        domain = urlparse(url).netloc

        if domain in self.last_request_time:
            elapsed = time.time() - self.last_request_time[domain]
            if elapsed < self.rate_limit:
                time.sleep(self.rate_limit - elapsed)

        self.last_request_time[domain] = time.time()

    def _extract_text(self, soup: BeautifulSoup) -> str:
        """Extract main text content"""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Try to find main content area
        main_content = (
            soup.find("main")
            or soup.find("article")
            or soup.find("div", class_="content")
            or soup.find("div", id="content")
            or soup.body
        )

        if main_content:
            text = main_content.get_text(separator="\n", strip=True)
        else:
            text = soup.get_text(separator="\n", strip=True)

        # Clean up whitespace
        lines = [line.strip() for line in text.split("\n")]
        lines = [line for line in lines if line]

        return "\n\n".join(lines)

    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract page metadata"""
        metadata = {}

        # Meta tags
        for meta in soup.find_all("meta"):
            name = meta.get("name") or meta.get("property")
            content = meta.get("content")
            if name and content:
                metadata[name] = content

        return metadata

    def _get_cached(self, url: str) -> Optional[WebContent]:
        """Get cached content"""
        cache_key = hashlib.md5(url.encode()).hexdigest()
        cache_file = self.cache_dir / f"{cache_key}.json"

        if cache_file.exists():
            import json

            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return WebContent(**data)
            except:
                pass

        return None

    def _cache_content(self, url: str, content: WebContent):
        """Cache web content"""
        cache_key = hashlib.md5(url.encode()).hexdigest()
        cache_file = self.cache_dir / f"{cache_key}.json"

        import json

        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                data = {
                    "url": content.url,
                    "title": content.title,
                    "content": content.content,
                    "html": content.html,
                    "links": content.links,
                    "images": content.images,
                    "metadata": content.metadata,
                    "status_code": content.status_code,
                }
                json.dump(data, f, ensure_ascii=False, indent=2)
        except:
            pass

    def clear_cache(self):
        """Clear all cached content"""
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
