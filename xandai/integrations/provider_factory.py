"""
LLM Provider Factory

Dynamic provider creation based on configuration.
Supports environment-based configuration and CLI arguments.
"""

import os
from typing import List, Optional

from .base_provider import LLMConfig, LLMProvider, ProviderType
from .lm_studio_provider import LMStudioProvider
from .ollama_provider import OllamaProvider


class LLMProviderFactory:
    """
    Factory for creating LLM providers

    Handles provider instantiation, configuration, and environment variable support.
    Designed for flexibility and ease of use.
    """

    @staticmethod
    def create_provider(
        provider_type: str,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        **config_options,
    ) -> LLMProvider:
        """
        Create an LLM provider based on type and configuration

        Args:
            provider_type: "ollama", "lm_studio", etc.
            base_url: Provider endpoint URL
            model: Initial model to use
            **config_options: Additional configuration options

        Returns:
            Configured LLM provider instance

        Raises:
            ValueError: If provider_type is not supported
        """

        # Normalize and validate provider type
        provider_type = provider_type.lower().strip()

        if provider_type in ["ollama", "ol"]:
            return LLMProviderFactory._create_ollama_provider(base_url, model, **config_options)
        elif provider_type in ["lm_studio", "lms", "lm-studio", "lmstudio"]:
            return LLMProviderFactory._create_lm_studio_provider(base_url, model, **config_options)
        else:
            raise ValueError(
                f"Unsupported provider type: '{provider_type}'. "
                f"Supported providers: ollama, lm_studio"
            )

    @staticmethod
    def _create_ollama_provider(
        base_url: Optional[str] = None, model: Optional[str] = None, **config_options
    ) -> OllamaProvider:
        """Create Ollama provider with environment variable support"""

        # Use defaults from environment or sensible defaults
        if base_url is None:
            base_url = os.getenv("OLLAMA_HOST", "http://localhost:11434")

        if model is None:
            model = os.getenv("XANDAI_MODEL", None)  # Don't assume a default model

        # Create configuration with defaults and overrides
        config = LLMConfig(
            provider_type=ProviderType.OLLAMA,
            base_url=base_url,
            model=model,
            temperature=config_options.get("temperature", 0.7),
            top_p=config_options.get("top_p", 0.9),
            max_tokens=config_options.get("max_tokens", 2048),
            context_length=config_options.get("context_length", 4096),
            timeout=config_options.get("timeout", 120),
            extra_options=config_options.get("extra_options", {}),
        )

        return OllamaProvider(config)

    @staticmethod
    def _create_lm_studio_provider(
        base_url: Optional[str] = None, model: Optional[str] = None, **config_options
    ) -> LMStudioProvider:
        """Create LM Studio provider with environment variable support"""

        # Use defaults from environment or sensible defaults
        if base_url is None:
            base_url = os.getenv("LM_STUDIO_HOST", "http://localhost:1234")

        if model is None:
            model = os.getenv("LM_STUDIO_MODEL", None)  # Auto-detect from server

        # LM Studio may require different defaults
        config = LLMConfig(
            provider_type=ProviderType.LM_STUDIO,
            base_url=base_url,
            model=model,
            temperature=config_options.get("temperature", 0.7),
            top_p=config_options.get("top_p", 0.9),
            max_tokens=config_options.get("max_tokens", 2048),
            context_length=config_options.get("context_length", 4096),
            timeout=config_options.get("timeout", 180),  # Longer timeout for LM Studio
            headers=config_options.get("headers", {}),
            extra_options=config_options.get("extra_options", {}),
        )

        return LMStudioProvider(config)

    @staticmethod
    def create_from_env() -> LLMProvider:
        """Create provider based on environment variables only"""

        provider_type = os.getenv("XANDAI_PROVIDER", "ollama").lower()
        base_url = os.getenv("XANDAI_BASE_URL", None)
        model = os.getenv("XANDAI_MODEL", None)

        # Additional environment-based configuration
        config_options = {}

        # Parse temperature from env
        temp_str = os.getenv("XANDAI_TEMPERATURE", "0.7")
        try:
            config_options["temperature"] = float(temp_str)
        except ValueError:
            config_options["temperature"] = 0.7

        # Parse max tokens from env
        max_tokens_str = os.getenv("XANDAI_MAX_TOKENS", "2048")
        try:
            config_options["max_tokens"] = int(max_tokens_str)
        except ValueError:
            config_options["max_tokens"] = 2048

        return LLMProviderFactory.create_provider(
            provider_type=provider_type,
            base_url=base_url,
            model=model,
            **config_options,
        )

    @staticmethod
    def get_supported_providers() -> List[str]:
        """Get list of supported provider types"""
        return ["ollama", "lm_studio"]

    @staticmethod
    def create_auto_detect(
        preferred_provider: Optional[str] = None, fallback_provider: str = "ollama"
    ) -> LLMProvider:
        """
        Auto-detect and create the best available provider

        Args:
            preferred_provider: Try this provider first
            fallback_provider: Use this if preferred fails

        Returns:
            Working LLM provider instance
        """

        providers_to_try = []

        if preferred_provider:
            providers_to_try.append(preferred_provider.lower())

        # Add all supported providers (except the preferred one)
        for provider in LLMProviderFactory.get_supported_providers():
            if provider != preferred_provider:
                providers_to_try.append(provider)

        # Ensure fallback is at the end
        if fallback_provider not in providers_to_try:
            providers_to_try.append(fallback_provider)

        for provider_type in providers_to_try:
            try:
                provider = LLMProviderFactory.create_provider(provider_type)
                if provider.is_connected():
                    return provider
            except Exception:
                continue

        # If all fails, return the fallback provider anyway
        return LLMProviderFactory.create_provider(fallback_provider)
