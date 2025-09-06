"""
Base LLM Provider Abstraction

Unified interface for different LLM providers (Ollama, LM Studio, etc.)
Engineered for extensibility and backward compatibility.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Generator, List, Optional


class ProviderType(Enum):
    """Supported LLM provider types"""

    OLLAMA = "ollama"
    LM_STUDIO = "lm_studio"


@dataclass
class LLMResponse:
    """
    Standardized response format for all LLM providers

    Replaces provider-specific response classes with unified interface
    """

    content: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    finish_reason: str = "stop"
    provider: str = "unknown"
    context_length: int = 4096  # Default context length for percentage calculation

    @property
    def context_usage(self) -> str:
        """Context usage information with percentage for backward compatibility"""
        percentage = (
            (self.total_tokens / self.context_length * 100) if self.context_length > 0 else 0
        )
        return f"Context: {self.prompt_tokens}+{self.completion_tokens} tokens ({self.total_tokens} total, {percentage:.1f}%) [{self.provider}]"

    def print_with_context(self) -> str:
        """Format response with context usage information"""
        return f"{self.content}{self.context_usage}"


@dataclass
class LLMConfig:
    """Configuration container for LLM providers"""

    provider_type: ProviderType
    base_url: str
    model: Optional[str] = None
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 2048
    context_length: int = 4096
    timeout: int = 120
    headers: Optional[Dict[str, str]] = None
    extra_options: Optional[Dict[str, Any]] = None


class LLMProvider(ABC):
    """
    Abstract base class for all LLM providers

    Provides unified interface that all providers must implement.
    Ensures consistent behavior across different LLM backends.
    """

    def __init__(self, config: LLMConfig):
        self.config = config
        self.current_model = config.model

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if the provider is available and connected"""
        pass

    @abstractmethod
    def list_models(self) -> List[str]:
        """Get list of available models from the provider"""
        pass

    @abstractmethod
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific model"""
        pass

    @abstractmethod
    def set_model(self, model_name: str) -> bool:
        """Set the current model for subsequent requests"""
        pass

    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        stream: bool = False,
        progress_callback=None,
        **options,
    ) -> "LLMResponse":
        """
        Send chat completion request

        Args:
            messages: List of messages [{"role": "user", "content": "..."}, ...]
            model: Model to use (overrides current_model if provided)
            stream: Whether to stream the response
            progress_callback: Function to call for progress updates (Ollama compatibility)
            **options: Provider-specific options

        Returns:
            LLMResponse with standardized format
        """
        pass

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        **options,
    ) -> "LLMResponse":
        """
        Generate completion from a single prompt

        Args:
            prompt: The input prompt
            system_prompt: Optional system prompt
            model: Model to use (overrides current_model if provided)
            **options: Provider-specific options

        Returns:
            LLMResponse with standardized format
        """
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """
        Get comprehensive health/status information

        Returns:
            Dict with health check results including:
            - connected: bool
            - endpoint: str
            - current_model: str
            - available_models: List[str]
            - models_available: int
            - provider_type: str
        """
        pass

    def get_current_model(self) -> Optional[str]:
        """Get the currently selected model"""
        return self.current_model

    def get_provider_type(self) -> ProviderType:
        """Get the provider type"""
        return self.config.provider_type

    def get_base_url(self) -> str:
        """Get the base URL for the provider"""
        return self.config.base_url

    def update_config(self, **kwargs):
        """Update configuration parameters dynamically"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
