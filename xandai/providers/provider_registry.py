"""
Provider Registry

Dynamic provider registration and discovery system.
Supports local and cloud LLM providers with automatic detection.
"""

import importlib
import inspect
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from xandai.integrations.base_provider import LLMProvider, ProviderType


class ProviderRegistry:
    """
    Central registry for all LLM providers.

    Supports:
    - Dynamic provider registration
    - Auto-discovery of providers
    - Provider instantiation with config
    - Capability detection
    """

    _instance = None
    _providers: Dict[str, Type[LLMProvider]] = {}
    _provider_instances: Dict[str, LLMProvider] = {}

    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize registry"""
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self._auto_discover_providers()

    def register(self, provider_class: Type[LLMProvider], name: Optional[str] = None):
        """
        Register a provider class

        Args:
            provider_class: Provider class to register
            name: Optional name (defaults to class name)
        """
        if not issubclass(provider_class, LLMProvider):
            raise TypeError(f"{provider_class} must be a subclass of LLMProvider")

        provider_name = name or provider_class.__name__.lower().replace("provider", "")
        self._providers[provider_name] = provider_class

    def get_provider(self, name: str, **config) -> LLMProvider:
        """
        Get or create a provider instance

        Args:
            name: Provider name
            **config: Configuration options for provider

        Returns:
            Provider instance
        """
        # Check if instance already exists with same config
        cache_key = f"{name}:{hash(frozenset(config.items()))}"

        if cache_key in self._provider_instances:
            return self._provider_instances[cache_key]

        # Get provider class
        provider_class = self._providers.get(name)
        if not provider_class:
            raise ValueError(f"Provider '{name}' not found. Available: {self.list_providers()}")

        # Create instance
        instance = provider_class(**config)
        self._provider_instances[cache_key] = instance

        return instance

    def list_providers(self) -> List[str]:
        """List all registered provider names"""
        return sorted(self._providers.keys())

    def get_provider_info(self, name: str) -> Dict[str, Any]:
        """
        Get information about a provider

        Args:
            name: Provider name

        Returns:
            Provider metadata
        """
        provider_class = self._providers.get(name)
        if not provider_class:
            return {}

        # Try to instantiate for info (without config)
        try:
            temp_instance = provider_class()
            return {
                "name": name,
                "class": provider_class.__name__,
                "type": (
                    temp_instance.get_provider_type().value
                    if hasattr(temp_instance, "get_provider_type")
                    else "unknown"
                ),
                "description": provider_class.__doc__ or "",
                "requires_api_key": self._requires_api_key(provider_class),
                "supports_streaming": self._supports_streaming(provider_class),
            }
        except:
            return {
                "name": name,
                "class": provider_class.__name__,
                "description": provider_class.__doc__ or "",
            }

    def list_by_type(self, provider_type: ProviderType) -> List[str]:
        """
        List providers by type

        Args:
            provider_type: Type to filter by

        Returns:
            List of provider names
        """
        matching = []
        for name, provider_class in self._providers.items():
            try:
                instance = provider_class()
                if hasattr(instance, "get_provider_type"):
                    if instance.get_provider_type() == provider_type:
                        matching.append(name)
            except:
                pass

        return sorted(matching)

    def auto_detect(self) -> Optional[LLMProvider]:
        """
        Auto-detect and return best available provider

        Priority:
        1. Local providers (Ollama, LM Studio)
        2. Cloud providers with API keys

        Returns:
            Best available provider or None
        """
        # Try local providers first (offline-first)
        local_providers = ["ollama", "lmstudio", "lm_studio"]

        for provider_name in local_providers:
            if provider_name in self._providers:
                try:
                    provider = self.get_provider(provider_name)
                    if hasattr(provider, "is_connected") and provider.is_connected():
                        return provider
                except:
                    continue

        # Try cloud providers if local not available
        # (Would check for API keys here)

        return None

    def _auto_discover_providers(self):
        """Automatically discover and register providers"""
        # Discover from xandai.integrations (existing providers)
        self._discover_from_module("xandai.integrations")

        # Discover from xandai.providers.local
        self._discover_from_module("xandai.providers.local")

        # Discover from xandai.providers.cloud
        self._discover_from_module("xandai.providers.cloud")

    def _discover_from_module(self, module_path: str):
        """Discover providers from a module"""
        try:
            # Try to import module
            module = importlib.import_module(module_path)
            module_dir = Path(module.__file__).parent

            # Scan for Python files
            for file_path in module_dir.glob("*.py"):
                if file_path.name.startswith("_"):
                    continue

                # Import module
                module_name = f"{module_path}.{file_path.stem}"
                try:
                    mod = importlib.import_module(module_name)

                    # Find provider classes
                    for name, obj in inspect.getmembers(mod, inspect.isclass):
                        if issubclass(obj, LLMProvider) and obj != LLMProvider:
                            provider_name = name.lower().replace("provider", "")
                            if provider_name not in self._providers:
                                self._providers[provider_name] = obj
                except Exception:
                    continue

        except (ImportError, AttributeError):
            pass

    def _requires_api_key(self, provider_class: Type[LLMProvider]) -> bool:
        """Check if provider requires API key"""
        # Check constructor signature
        sig = inspect.signature(provider_class.__init__)
        params = sig.parameters

        return "api_key" in params or "token" in params

    def _supports_streaming(self, provider_class: Type[LLMProvider]) -> bool:
        """Check if provider supports streaming"""
        return hasattr(provider_class, "stream") or hasattr(provider_class, "stream_generate")

    def clear_cache(self):
        """Clear cached provider instances"""
        self._provider_instances.clear()


# Global registry instance
registry = ProviderRegistry()


def register_provider(provider_class: Type[LLMProvider], name: Optional[str] = None):
    """Convenience function to register a provider"""
    registry.register(provider_class, name)


def get_provider(name: str, **config) -> LLMProvider:
    """Convenience function to get a provider"""
    return registry.get_provider(name, **config)


def list_providers() -> List[str]:
    """Convenience function to list providers"""
    return registry.list_providers()
