"""
XandAI Web Integration

Enhanced web content fetching and processing.
"""

from xandai.web.content_extractor import ContentExtractor, ExtractedContent
from xandai.web.web_fetcher import FetchResult, WebContent, WebFetcher
from xandai.web.web_search import WebSearch

__all__ = [
    "WebFetcher",
    "WebContent",
    "FetchResult",
    "ContentExtractor",
    "ExtractedContent",
    "WebSearch",
]
