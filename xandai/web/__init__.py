"""
XandAI Web Integration Module

Módulo para integração web com funcionalidade de busca,
parsing e extração de conteúdo usando BeautifulSoup4.

Características:
- Detecção inteligente de links
- Sistema de toggle configurável
- Tratamento robusto de erros
- Arquitetura modular e extensível
"""

from .content_extractor import ContentExtractor
from .link_detector import LinkDetector
from .web_fetcher import WebFetcher
from .web_manager import WebManager

__all__ = ["WebFetcher", "LinkDetector", "ContentExtractor", "WebManager"]
