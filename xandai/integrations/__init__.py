"""
XandAI Integrations - External service integrations (Ollama, LM Studio, etc.)

Provides unified interface for different LLM providers through standardized abstractions.
"""

from .base_provider import LLMConfig, LLMProvider, LLMResponse, ProviderType
from .lm_studio_provider import LMStudioProvider

# Legacy compatibility - maintain existing imports
from .ollama_client import OllamaClient, OllamaResponse
from .ollama_provider import OllamaProvider
from .provider_factory import LLMProviderFactory

__all__ = [
    # New provider system
    "LLMProvider",
    "LLMResponse",
    "LLMConfig",
    "ProviderType",
    "OllamaProvider",
    "LMStudioProvider",
    "LLMProviderFactory",
    # Legacy compatibility
    "OllamaClient",
    "OllamaResponse",
]
