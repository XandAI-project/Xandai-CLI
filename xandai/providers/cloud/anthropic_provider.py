"""
Anthropic Provider

Support for Anthropic's Claude models (Claude 3, Claude 2, etc.)
"""

import os
from typing import Iterator, List, Optional

import requests

from xandai.integrations.base_provider import LLMResponse, ProviderType
from xandai.providers.cloud.base_cloud_provider import BaseCloudProvider


class AnthropicProvider(BaseCloudProvider):
    """
    Anthropic API Provider

    Supports:
    - Claude 3 (Opus, Sonnet, Haiku)
    - Claude 2
    - Streaming output
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = "claude-3-sonnet-20240229",
        **kwargs,
    ):
        """
        Initialize Anthropic provider

        Args:
            api_key: Anthropic API key (or from ANTHROPIC_API_KEY env)
            base_url: Custom API base URL
            model: Default model (claude-3-opus, claude-3-sonnet, etc.)
            **kwargs: Additional options
        """
        super().__init__(api_key, base_url, model, **kwargs)

    def get_provider_type(self) -> ProviderType:
        """Return provider type"""
        return ProviderType.OLLAMA  # Would add ANTHROPIC type

    def _get_api_key_from_env(self) -> Optional[str]:
        """Get API key from environment"""
        return os.getenv("ANTHROPIC_API_KEY")

    def get_default_base_url(self) -> str:
        """Get default Anthropic API URL"""
        return "https://api.anthropic.com/v1"

    def list_models(self) -> List[str]:
        """List available Claude models"""
        # Anthropic doesn't have a models endpoint
        return [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-2.1",
            "claude-2.0",
        ]

    def generate(
        self, prompt: str, temperature: float = 0.7, max_tokens: int = 2048, **kwargs
    ) -> LLMResponse:
        """
        Generate completion from prompt

        Args:
            prompt: Input prompt
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Returns:
            LLMResponse object
        """
        # Convert to messages format
        messages = [{"role": "user", "content": prompt}]
        return self.chat(messages, temperature=temperature, max_tokens=max_tokens, **kwargs)

    def chat(
        self, messages: list, temperature: float = 0.7, max_tokens: int = 2048, **kwargs
    ) -> LLMResponse:
        """
        Generate chat completion

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Returns:
            LLMResponse object
        """
        model = kwargs.get("model") or self.current_model

        # Extract system message if present
        system_message = None
        user_messages = []

        for msg in messages:
            if msg.get("role") == "system":
                system_message = msg.get("content")
            else:
                user_messages.append(msg)

        payload = {
            "model": model,
            "messages": user_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if system_message:
            payload["system"] = system_message

        # Add any additional parameters
        for k, v in kwargs.items():
            if k not in ["model"] and v is not None:
                payload[k] = v

        try:
            response = requests.post(
                f"{self.base_url}/messages",
                headers=self._build_headers(),
                json=payload,
                timeout=self.timeout,
            )

            if response.status_code != 200:
                self._handle_api_error(response.json(), response.status_code)

            data = response.json()
            content = data["content"][0]["text"]

            usage = data.get("usage", {})

            return self._create_llm_response(
                content=content,
                model=data.get("model", model),
                prompt_tokens=usage.get("input_tokens", 0),
                completion_tokens=usage.get("output_tokens", 0),
            )

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Anthropic API request failed: {e}")

    def stream_chat(
        self, messages: list, temperature: float = 0.7, max_tokens: int = 2048, **kwargs
    ) -> Iterator[str]:
        """
        Stream chat completion

        Args:
            messages: List of message dicts
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            **kwargs: Additional parameters

        Yields:
            Token strings
        """
        model = kwargs.get("model") or self.current_model

        # Extract system message
        system_message = None
        user_messages = []

        for msg in messages:
            if msg.get("role") == "system":
                system_message = msg.get("content")
            else:
                user_messages.append(msg)

        payload = {
            "model": model,
            "messages": user_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }

        if system_message:
            payload["system"] = system_message

        try:
            response = requests.post(
                f"{self.base_url}/messages",
                headers=self._build_headers(),
                json=payload,
                stream=True,
                timeout=self.timeout,
            )

            if response.status_code != 200:
                self._handle_api_error(response.json(), response.status_code)

            for line in response.iter_lines():
                if line:
                    line_str = line.decode("utf-8")
                    if line_str.startswith("data: "):
                        data_str = line_str[6:]

                        try:
                            import json

                            data = json.loads(data_str)

                            if data.get("type") == "content_block_delta":
                                delta = data.get("delta", {})
                                if delta.get("type") == "text_delta":
                                    yield delta.get("text", "")
                        except:
                            continue

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Anthropic streaming failed: {e}")

    def _build_headers(self, extra_headers: Optional[dict] = None) -> dict:
        """Build Anthropic-specific headers"""
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

        if extra_headers:
            headers.update(extra_headers)

        return headers
