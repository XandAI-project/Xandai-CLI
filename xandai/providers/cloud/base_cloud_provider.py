"""
Base Cloud Provider

Abstract base class for cloud-based LLM providers.
Provides common functionality for API-based providers.
"""

import os
from abc import abstractmethod
from typing import Any, Dict, Iterator, Optional

from xandai.integrations.base_provider import LLMProvider, LLMResponse, ProviderType


class BaseCloudProvider(LLMProvider):
    """
    Base class for cloud LLM providers

    Provides common functionality:
    - API key management
    - Request/response handling
    - Error handling
    - Streaming support
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 60,
        **kwargs,
    ):
        """
        Initialize cloud provider

        Args:
            api_key: API key (or from environment)
            base_url: Custom API base URL
            model: Default model name
            timeout: Request timeout in seconds
            **kwargs: Additional provider-specific options
        """
        self.api_key = api_key or self._get_api_key_from_env()
        self.base_url = base_url or self.get_default_base_url()
        self.current_model = model
        self.timeout = timeout
        self.extra_config = kwargs

        if not self.api_key:
            raise ValueError(f"{self.__class__.__name__} requires an API key")

    @abstractmethod
    def get_provider_type(self) -> ProviderType:
        """Return provider type"""
        pass

    @abstractmethod
    def _get_api_key_from_env(self) -> Optional[str]:
        """Get API key from environment variable"""
        pass

    @abstractmethod
    def get_default_base_url(self) -> str:
        """Get default API base URL"""
        pass

    def is_connected(self) -> bool:
        """Check if provider is accessible"""
        try:
            # Try to list models or make a simple API call
            models = self.list_models()
            return len(models) > 0
        except:
            return False

    def get_base_url(self) -> str:
        """Get current base URL"""
        return self.base_url

    def set_model(self, model: str):
        """Set active model"""
        self.current_model = model

    def get_current_model(self) -> Optional[str]:
        """Get current model name"""
        return self.current_model

    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        Get information about a model

        Args:
            model_name: Model name

        Returns:
            Model information dict
        """
        return {"name": model_name, "provider": self.__class__.__name__}

    def health_check(self) -> bool:
        """Check provider health"""
        return self.is_connected()

    def _build_headers(self, extra_headers: Optional[Dict] = None) -> Dict[str, str]:
        """
        Build HTTP headers for API requests

        Args:
            extra_headers: Additional headers to include

        Returns:
            Complete headers dict
        """
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}

        if extra_headers:
            headers.update(extra_headers)

        return headers

    def _handle_api_error(self, response_data: Dict, status_code: int):
        """
        Handle API error responses

        Args:
            response_data: Error response from API
            status_code: HTTP status code
        """
        error_msg = response_data.get("error", {}).get("message", "Unknown error")
        raise RuntimeError(f"API Error ({status_code}): {error_msg}")

    def _create_llm_response(
        self, content: str, model: str, prompt_tokens: int = 0, completion_tokens: int = 0
    ) -> LLMResponse:
        """
        Create standardized LLM response

        Args:
            content: Generated content
            model: Model used
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens

        Returns:
            LLMResponse object
        """
        return LLMResponse(
            content=content,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        )

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate completion from prompt"""
        pass

    @abstractmethod
    def chat(self, messages: list, **kwargs) -> LLMResponse:
        """Generate chat completion"""
        pass

    def stream_generate(self, prompt: str, **kwargs) -> Iterator[str]:
        """
        Stream generation (optional)

        Args:
            prompt: Input prompt
            **kwargs: Generation parameters

        Yields:
            Token strings
        """
        # Default: non-streaming fallback
        response = self.generate(prompt, **kwargs)
        yield response.content

    def stream_chat(self, messages: list, **kwargs) -> Iterator[str]:
        """
        Stream chat completion (optional)

        Args:
            messages: Chat messages
            **kwargs: Generation parameters

        Yields:
            Token strings
        """
        # Default: non-streaming fallback
        response = self.chat(messages, **kwargs)
        yield response.content
