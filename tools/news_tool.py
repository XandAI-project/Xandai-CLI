"""
News Tool - Search and retrieve news articles using SearxNG
"""

import os
from typing import Optional
from urllib.parse import quote

import requests


class NewsTool:
    """Search for news articles using self-hosted SearxNG instance."""

    # SearxNG instance URL (can be configured via environment variable or config)
    @staticmethod
    def get_searxng_url():
        """Get SearxNG URL from environment or config."""
        # Try environment variable first
        env_url = os.environ.get("SEARXNG_URL", "").strip()
        if env_url:
            # Ensure it has /search endpoint
            if not env_url.endswith("/search"):
                env_url = env_url.rstrip("/") + "/search"
            return env_url

        # Try reading from config file
        try:
            from pathlib import Path

            config_file = Path.home() / ".xandai" / "config.env"
            if config_file.exists():
                with open(config_file, "r") as f:
                    for line in f:
                        if line.startswith("SEARXNG_URL="):
                            url = line.split("=", 1)[1].strip().strip('"').strip("'")
                            if not url.endswith("/search"):
                                url = url.rstrip("/") + "/search"
                            return url
        except Exception:
            pass

        # Default URL
        return "http://192.168.3.46:4000/search"

    # Language code mapping
    LANGUAGE_CODES = {
        "portuguese": "pt-BR",
        "english": "en-US",
        "spanish": "es-ES",
        "french": "fr-FR",
        "german": "de-DE",
        "italian": "it-IT",
        "japanese": "ja-JP",
        "chinese": "zh-CN",
        "russian": "ru-RU",
        "arabic": "ar-SA",
    }

    @staticmethod
    def get_name():
        """Return the tool's name."""
        return "news_tool"

    @staticmethod
    def get_description():
        """Return description of what the tool does."""
        return "Search for recent news articles on any topic using SearxNG search engine"

    @staticmethod
    def get_parameters():
        """Return the parameters this tool accepts."""
        return {
            "topic": "string (required) - Topic or keyword to search for (e.g., 'technology', 'sports', 'politics')",
            "language": "string (optional) - Language for results: 'auto', 'portuguese', 'english', 'spanish', etc. or language code like 'pt-BR' (default: 'auto')",
            "time_range": "string (optional) - Time range: 'day', 'week', 'month', 'year' (default: 'day')",
            "max_results": "integer (optional) - Maximum number of results to return (default: 10, max: 20)",
        }

    def execute(
        self, topic: str, language: str = "auto", time_range: str = "day", max_results: int = 10
    ):
        """
        Execute the news search.

        Args:
            topic: Topic or keyword to search for
            language: Language for results (auto or language code)
            time_range: Time range for news (day, week, month, year)
            max_results: Maximum number of results to return

        Returns:
            Dictionary with news articles
        """
        try:
            # Validate time_range
            valid_time_ranges = ["day", "week", "month", "year"]
            if time_range.lower() not in valid_time_ranges:
                time_range = "day"

            # Normalize language
            language = language.lower().strip()
            if language in self.LANGUAGE_CODES:
                language = self.LANGUAGE_CODES[language]
            elif language not in ["auto"] and "-" not in language:
                # If it's not 'auto' and not a proper code, default to auto
                language = "auto"

            # Limit max_results
            max_results = max(1, min(max_results, 20))

            # Build search query
            params = {
                "q": topic,
                "language": language,
                "time_range": time_range.lower(),
                "safesearch": "0",
                "categories": "news",
                "format": "json",  # Request JSON format
            }

            # Get SearxNG URL
            searxng_url = self.get_searxng_url()

            # Make request to SearxNG
            if self._verbose_mode():
                print(f"[News Tool] Searching SearxNG for: {topic}")
                print(f"[News Tool] URL: {searxng_url}")
                print(f"[News Tool] Language: {language}, Time range: {time_range}")

            response = requests.get(
                searxng_url, params=params, timeout=10, headers={"User-Agent": "XandAI-CLI/2.1.9"}
            )

            response.raise_for_status()

            # Parse JSON response
            data = response.json()

            if "results" not in data:
                return {
                    "success": False,
                    "error": "No results found in SearxNG response",
                    "topic": topic,
                }

            results = data.get("results", [])

            if not results:
                return {
                    "success": True,
                    "topic": topic,
                    "language": language,
                    "time_range": time_range,
                    "total_results": 0,
                    "articles": [],
                    "message": f"No news articles found for '{topic}' in the last {time_range}",
                }

            # Process and format results
            articles = []
            for i, result in enumerate(results[:max_results]):
                article = {
                    "title": result.get("title", "No title"),
                    "url": result.get("url", ""),
                    "content": result.get("content", "No description available"),
                    "source": self._extract_domain(result.get("url", "")),
                    "published": result.get("publishedDate", "Unknown date"),
                }

                # Add optional fields if available
                if "engine" in result:
                    article["engine"] = result["engine"]
                if "img_src" in result:
                    article["image"] = result["img_src"]

                articles.append(article)

            return {
                "success": True,
                "topic": topic,
                "language": language,
                "time_range": time_range,
                "total_results": len(results),
                "results_returned": len(articles),
                "articles": articles,
                "search_url": response.url,
            }

        except requests.Timeout:
            return {
                "success": False,
                "error": "Search request timed out. SearxNG instance may be unavailable.",
                "topic": topic,
            }
        except requests.ConnectionError:
            return {
                "success": False,
                "error": f"Cannot connect to SearxNG at {self.get_searxng_url()}. Please check if the service is running.",
                "topic": topic,
            }
        except requests.HTTPError as e:
            return {
                "success": False,
                "error": f"HTTP error from SearxNG: {e.response.status_code} - {e.response.reason}",
                "topic": topic,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"News search error: {str(e)}",
                "topic": topic,
            }

    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extract domain name from URL."""
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            domain = parsed.netloc
            # Remove 'www.' prefix if present
            if domain.startswith("www."):
                domain = domain[4:]
            return domain
        except:
            return "Unknown source"

    @staticmethod
    def _verbose_mode() -> bool:
        """Check if verbose mode is enabled."""
        import os

        return os.environ.get("XANDAI_VERBOSE", "").lower() in ["1", "true", "yes"]
