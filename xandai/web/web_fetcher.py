"""
Web Fetching Module

Responsável por fazer requisições HTTP de forma robusta
com tratamento de erros, timeouts e headers apropriados.
"""

import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests
from requests.exceptions import ConnectionError, RequestException, Timeout


@dataclass
class FetchResult:
    """Resultado de uma requisição web"""

    success: bool
    url: str
    content: Optional[str] = None
    status_code: Optional[int] = None
    headers: Optional[Dict[str, str]] = None
    error_message: Optional[str] = None
    response_time: float = 0.0


class WebFetcher:
    """
    Cliente HTTP robusto para buscar conteúdo web

    Características:
    - Timeouts configuráveis
    - User-Agent apropriado
    - Tratamento de redirects
    - Retry logic para falhas temporárias
    - Validação de content-type
    """

    def __init__(self, timeout: int = 10, max_retries: int = 2):
        """
        Inicializa WebFetcher

        Args:
            timeout: Timeout em segundos para requisições
            max_retries: Número máximo de tentativas
        """
        self.timeout = timeout
        self.max_retries = max_retries

        # Session reutilizável para melhor performance
        self.session = requests.Session()

        # Headers padrão para simular browser real
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        )

    def fetch(self, url: str, **kwargs) -> FetchResult:
        """
        Busca conteúdo de uma URL com retry logic

        Args:
            url: URL para buscar
            **kwargs: Parâmetros adicionais para requests

        Returns:
            FetchResult com resultado da requisição
        """
        start_time = time.time()

        for attempt in range(self.max_retries + 1):
            try:
                result = self._attempt_fetch(url, **kwargs)
                result.response_time = time.time() - start_time
                return result

            except (ConnectionError, Timeout) as e:
                if attempt < self.max_retries:
                    # Wait before retry (exponential backoff)
                    time.sleep(0.5 * (2**attempt))
                    continue
                else:
                    return FetchResult(
                        success=False,
                        url=url,
                        error_message=f"Connection failed after {self.max_retries + 1} attempts: {str(e)}",
                        response_time=time.time() - start_time,
                    )

            except Exception as e:
                return FetchResult(
                    success=False,
                    url=url,
                    error_message=f"Unexpected error: {str(e)}",
                    response_time=time.time() - start_time,
                )

        return FetchResult(
            success=False,
            url=url,
            error_message="Max retries exceeded",
            response_time=time.time() - start_time,
        )

    def _attempt_fetch(self, url: str, **kwargs) -> FetchResult:
        """Única tentativa de buscar URL"""
        # Merge default timeout with any provided
        request_kwargs = {"timeout": self.timeout, "allow_redirects": True, **kwargs}

        response = self.session.get(url, **request_kwargs)

        # Check if response is successful
        response.raise_for_status()

        # Validate content type
        content_type = response.headers.get("content-type", "").lower()
        if not self._is_processable_content_type(content_type):
            return FetchResult(
                success=False,
                url=url,
                status_code=response.status_code,
                headers=dict(response.headers),
                error_message=f"Unsupported content type: {content_type}",
            )

        # Check content size (avoid downloading huge files)
        content_length = response.headers.get("content-length")
        if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB limit
            return FetchResult(
                success=False,
                url=url,
                status_code=response.status_code,
                headers=dict(response.headers),
                error_message=f"Content too large: {content_length} bytes",
            )

        # Handle encoding properly to avoid Unicode errors
        try:
            # Try to get content with proper encoding
            if response.encoding is None:
                response.encoding = "utf-8"  # Default to UTF-8 if not specified
            content = response.text
        except UnicodeDecodeError:
            # Fallback to raw content with error handling
            content = response.content.decode("utf-8", errors="replace")

        return FetchResult(
            success=True,
            url=response.url,  # Final URL after redirects
            content=content,
            status_code=response.status_code,
            headers=dict(response.headers),
        )

    def _is_processable_content_type(self, content_type: str) -> bool:
        """Verifica se o content-type é processável"""
        processable_types = [
            "text/html",
            "application/xhtml+xml",
            "text/plain",
            "application/xml",
            "text/xml",
        ]

        return any(ptype in content_type for ptype in processable_types)

    def close(self):
        """Fecha a session HTTP"""
        self.session.close()
