"""
XandAI Integrations - External service integrations (Ollama, LM Studio, etc.)

Provides unified interface for different LLM providers through standardized abstractions.
"""

from .base_provider import LLMProvider, LLMResponse, LLMConfig, ProviderType
from .ollama_provider import OllamaProvider  
from .lm_studio_provider import LMStudioProvider
from .provider_factory import LLMProviderFactory

# Legacy compatibility - maintain existing imports
from .ollama_client import OllamaClient, OllamaResponse

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
    "OllamaResponse"
]
