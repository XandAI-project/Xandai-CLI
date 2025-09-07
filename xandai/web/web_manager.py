"""
Web Integration Manager

Coordena todos os componentes da integração web:
detecção de links, busca, extração e gerenciamento de estado.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .content_extractor import ContentExtractor, ExtractedContent
from .link_detector import LinkDetector
from .web_fetcher import FetchResult, WebFetcher


@dataclass
class WebIntegrationResult:
    """Resultado do processamento de integração web"""

    original_text: str
    processed_text: str
    extracted_contents: List[ExtractedContent]
    processing_info: Dict[str, Any]
    success: bool = True
    error_message: Optional[str] = None


class WebManager:
    """
    Gerenciador principal da integração web

    Coordena o pipeline completo:
    1. Detecção de links processáveis
    2. Busca de conteúdo web
    3. Extração de informações
    4. Formatação para contexto LLM
    """

    def __init__(self, enabled: bool = False, timeout: int = 10, max_links: int = 3):
        """
        Inicializa WebManager

        Args:
            enabled: Se a integração web está habilitada
            timeout: Timeout para requisições em segundos
            max_links: Máximo de links a processar por input
        """
        self.enabled = enabled
        self.timeout = timeout
        self.max_links = max_links

        # Initialize components
        self.link_detector = LinkDetector()
        self.web_fetcher = WebFetcher(timeout=timeout)
        self.content_extractor = ContentExtractor()

        # Cache for processed URLs to avoid reprocessing
        self.url_cache: Dict[str, ExtractedContent] = {}
        self.cache_max_size = 50

    def set_enabled(self, enabled: bool):
        """Habilita ou desabilita a integração web"""
        self.enabled = enabled

    def is_enabled(self) -> bool:
        """Retorna se a integração web está habilitada"""
        return self.enabled

    def process_user_input(self, user_input: str) -> WebIntegrationResult:
        """
        Processa entrada do usuário buscando e integrando conteúdo web

        Args:
            user_input: Texto de entrada do usuário

        Returns:
            WebIntegrationResult com resultado do processamento
        """
        if not self.enabled:
            return WebIntegrationResult(
                original_text=user_input,
                processed_text=user_input,
                extracted_contents=[],
                processing_info={"enabled": False},
            )

        try:
            # 1. Detect processable links
            links = self.link_detector.find_processable_links(user_input)

            if not links:
                return WebIntegrationResult(
                    original_text=user_input,
                    processed_text=user_input,
                    extracted_contents=[],
                    processing_info={"links_found": 0},
                )

            # Limit number of links to process
            links_to_process = links[: self.max_links]

            # 2. Fetch and extract content
            extracted_contents = []
            successful_extractions = 0
            failed_extractions = []

            for url, start_pos, end_pos in links_to_process:
                normalized_url = self.link_detector.normalize_url(url)

                # Check cache first
                if normalized_url in self.url_cache:
                    extracted_contents.append(self.url_cache[normalized_url])
                    successful_extractions += 1
                    continue

                # Fetch and extract
                extraction_result = self._fetch_and_extract(normalized_url)
                if extraction_result:
                    extracted_contents.append(extraction_result)
                    self._cache_content(normalized_url, extraction_result)
                    successful_extractions += 1
                else:
                    failed_extractions.append(normalized_url)

            # 3. Enhance user input with extracted content
            enhanced_text = self._enhance_user_input(user_input, extracted_contents)

            processing_info = {
                "enabled": True,
                "links_found": len(links),
                "links_processed": len(links_to_process),
                "successful_extractions": successful_extractions,
                "failed_extractions": len(failed_extractions),
                "failed_urls": failed_extractions,
                "cache_size": len(self.url_cache),
            }

            return WebIntegrationResult(
                original_text=user_input,
                processed_text=enhanced_text,
                extracted_contents=extracted_contents,
                processing_info=processing_info,
            )

        except Exception as e:
            return WebIntegrationResult(
                original_text=user_input,
                processed_text=user_input,
                extracted_contents=[],
                processing_info={"error": str(e)},
                success=False,
                error_message=f"Web integration error: {str(e)}",
            )

    def _fetch_and_extract(self, url: str) -> Optional[ExtractedContent]:
        """
        Busca conteúdo de uma URL e extrai informações

        Args:
            url: URL para buscar

        Returns:
            ExtractedContent ou None se falhou
        """
        try:
            # Fetch content
            fetch_result = self.web_fetcher.fetch(url)

            if not fetch_result.success or not fetch_result.content:
                return None

            # Extract content
            extracted_content = self.content_extractor.extract(fetch_result.content, url)

            # Add fetch metadata
            extracted_content.metadata.update(
                {
                    "fetch_url": fetch_result.url,
                    "status_code": fetch_result.status_code,
                    "response_time": fetch_result.response_time,
                    "content_type": (
                        fetch_result.headers.get("content-type") if fetch_result.headers else None
                    ),
                }
            )

            return extracted_content

        except Exception as e:
            # Log error but don't fail the entire process
            return None

    def _enhance_user_input(self, original_input: str, contents: List[ExtractedContent]) -> str:
        """
        Melhora entrada do usuário com conteúdo extraído

        Args:
            original_input: Entrada original do usuário
            contents: Lista de conteúdo extraído

        Returns:
            Texto melhorado com contexto adicional
        """
        if not contents:
            return original_input

        # Build context information
        context_parts = ["\n--- Web Content Context ---"]

        for i, content in enumerate(contents, 1):
            context_parts.append(f"\n[Page {i}: {content.title}]")

            if content.description:
                context_parts.append(f"Description: {content.description}")

            if content.main_content:
                # Limit content size for LLM context
                main_content = content.main_content[:1500]
                if len(content.main_content) > 1500:
                    main_content += "... (truncated)"
                context_parts.append(f"Content: {main_content}")

            if content.code_blocks:
                context_parts.append("Code examples found:")
                for j, code in enumerate(content.code_blocks[:3], 1):  # Max 3 code blocks per page
                    code_preview = code[:500]
                    if len(code) > 500:
                        code_preview += "... (truncated)"
                    context_parts.append(f"  Code {j}: {code_preview}")

            if content.language:
                context_parts.append(f"Technology: {content.language}")

        context_parts.append("--- End Web Content Context ---\n")

        # Combine original input with context
        enhanced_input = original_input + "\n" + "\n".join(context_parts)

        return enhanced_input

    def _cache_content(self, url: str, content: ExtractedContent):
        """
        Cache extracted content to avoid reprocessing

        Args:
            url: URL da content
            content: Content extraída
        """
        # Implement LRU-like behavior
        if len(self.url_cache) >= self.cache_max_size:
            # Remove oldest entries
            oldest_keys = list(self.url_cache.keys())[: -self.cache_max_size // 2]
            for key in oldest_keys:
                del self.url_cache[key]

        self.url_cache[url] = content

    def clear_cache(self):
        """Limpa o cache de conteúdo"""
        self.url_cache.clear()

    def get_cache_info(self) -> Dict[str, Any]:
        """Retorna informações sobre o cache"""
        return {
            "size": len(self.url_cache),
            "max_size": self.cache_max_size,
            "urls": list(self.url_cache.keys()),
        }

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da integração web"""
        return {
            "enabled": self.enabled,
            "timeout": self.timeout,
            "max_links": self.max_links,
            "cache_size": len(self.url_cache),
            "components": {
                "link_detector": "ready",
                "web_fetcher": "ready",
                "content_extractor": "ready",
            },
        }

    def close(self):
        """Cleanup resources"""
        self.web_fetcher.close()
        self.url_cache.clear()
