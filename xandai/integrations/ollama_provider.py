"""
Ollama Provider Implementation

Wraps existing OllamaClient functionality with standardized interface.
Maintains full backward compatibility while enabling provider abstraction.
"""

import os
from typing import Any, Dict, Generator, List, Optional, Union

from .base_provider import LLMConfig, LLMProvider, LLMResponse, ProviderType
from .ollama_client import OllamaClient, OllamaResponse


class OllamaProvider(LLMProvider):
    """
    Ollama provider implementation using existing OllamaClient

    Acts as an adapter between the new provider interface and existing Ollama code.
    Preserves all existing functionality while adding standardized interface.
    """

    def __init__(self, config: LLMConfig):
        super().__init__(config)

        # Create wrapped Ollama client using existing implementation
        self._ollama_client = OllamaClient(base_url=config.base_url)

        # Sync model configuration - only set if explicitly specified
        if config.model:
            self._ollama_client.current_model = config.model
            self.current_model = config.model
        # Don't auto-select - let main.py handle model selection

        # Update default options from config
        self._ollama_client.default_options.update(
            {
                "temperature": config.temperature,
                "top_p": config.top_p,
                "num_predict": config.max_tokens,
                "num_ctx": config.context_length,
            }
        )

    def is_connected(self) -> bool:
        """Check if Ollama server is available"""
        return self._ollama_client.is_connected()

    def list_models(self) -> List[str]:
        """Get list of available Ollama models"""
        try:
            return self._ollama_client.list_models()
        except Exception:
            return []

    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get Ollama model information"""
        try:
            return self._ollama_client.get_model_info(model_name)
        except Exception:
            return {"name": model_name, "available": False}

    def set_model(self, model_name: str) -> bool:
        """Set current Ollama model"""
        try:
            self._ollama_client.current_model = model_name
            self.current_model = model_name
            return True
        except Exception:
            return False

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        stream: bool = False,
        progress_callback=None,
        **options,
    ):
        """Send chat request to Ollama with full compatibility

        Returns:
            Generator[str, None, None] if stream=True, otherwise LLMResponse
        """

        # Extract progress_callback from options if present (to avoid JSON serialization error)
        if "progress_callback" in options:
            progress_callback = options.pop("progress_callback")

        # Merge config options with provided options
        # Note: progress_callback is intentionally NOT included here
        # as OllamaClient.chat() doesn't support it and it would cause JSON serialization errors
        merged_options = {
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "num_predict": self.config.max_tokens,
            "num_ctx": self.config.context_length,
            **options,
        }

        # Call existing Ollama client (without progress_callback to avoid serialization issues)
        ollama_response = self._ollama_client.chat(
            messages=messages,
            model=model or self.current_model,
            stream=stream,
            **merged_options,
        )

        # If streaming, return the generator directly
        if stream:
            return ollama_response  # This is a Generator[str, None, None]

        # Convert to standardized format for non-streaming
        # Extract token information from ContextUsage
        context_usage = ollama_response.context_usage
        return LLMResponse(
            content=ollama_response.content,
            model=ollama_response.model,
            prompt_tokens=context_usage.prompt_tokens,
            completion_tokens=context_usage.completion_tokens,
            total_tokens=context_usage.total_tokens,
            finish_reason=ollama_response.finish_reason,
            provider="ollama",
            context_length=self.config.context_length,
        )

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        **options,
    ) -> LLMResponse:
        """Generate completion using Ollama"""

        # Use existing generate method if available, otherwise convert to chat
        if hasattr(self._ollama_client, "generate"):
            ollama_response: OllamaResponse = self._ollama_client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                model=model or self.current_model,
                **options,
            )

            # Extract token information from ContextUsage
            context_usage = ollama_response.context_usage
            return LLMResponse(
                content=ollama_response.content,
                model=ollama_response.model,
                prompt_tokens=context_usage.prompt_tokens,
                completion_tokens=context_usage.completion_tokens,
                total_tokens=context_usage.total_tokens,
                finish_reason=ollama_response.finish_reason,
                provider="ollama",
                context_length=self.config.context_length,
            )
        else:
            # Fallback: Convert to messages format
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            return self.chat(messages=messages, model=model, **options)

    def health_check(self) -> Dict[str, Any]:
        """Get Ollama health information with enhanced details"""
        connected = self.is_connected()
        models = []

        if connected:
            try:
                models = self.list_models()
            except:
                models = []

        return {
            "connected": connected,
            "endpoint": self.config.base_url,
            "current_model": self.current_model or "None",
            "available_models": models,
            "models_available": len(models),
            "provider_type": "ollama",
            "api_type": "native",
            "version": "latest",  # Could be enhanced to get actual version
        }

    def _auto_select_first_model(self):
        """Auto-select first available model if none specified"""
        try:
            models = self.list_models()
            if models:
                first_model = models[0]
                self._ollama_client.current_model = first_model
                self.current_model = first_model
        except Exception:
            # If can't get models, leave model as None - will be handled later
            pass

    # Expose underlying client for advanced use cases
    def get_ollama_client(self) -> OllamaClient:
        """Get access to underlying OllamaClient for advanced operations"""
        return self._ollama_client
