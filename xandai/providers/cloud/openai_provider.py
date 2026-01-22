"""
OpenAI Provider

Support for OpenAI's GPT models (GPT-4, GPT-3.5, etc.)
"""

import os
from typing import Iterator, List, Optional

import requests

from xandai.integrations.base_provider import LLMResponse, ProviderType
from xandai.providers.cloud.base_cloud_provider import BaseCloudProvider


class OpenAIProvider(BaseCloudProvider):
    """
    OpenAI API Provider

    Supports:
    - GPT-4, GPT-4 Turbo
    - GPT-3.5 Turbo
    - Streaming output
    - Chat and completion modes
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = "gpt-3.5-turbo",
        organization: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize OpenAI provider

        Args:
            api_key: OpenAI API key (or from OPENAI_API_KEY env)
            base_url: Custom API base URL
            model: Default model (gpt-3.5-turbo, gpt-4, etc.)
            organization: OpenAI organization ID
            **kwargs: Additional options
        """
        self.organization = organization or os.getenv("OPENAI_ORGANIZATION")
        super().__init__(api_key, base_url, model, **kwargs)

    def get_provider_type(self) -> ProviderType:
        """Return provider type"""
        # Using OLLAMA enum for now (would add OPENAI type)
        return ProviderType.OLLAMA

    def _get_api_key_from_env(self) -> Optional[str]:
        """Get API key from environment"""
        return os.getenv("OPENAI_API_KEY")

    def get_default_base_url(self) -> str:
        """Get default OpenAI API URL"""
        return "https://api.openai.com/v1"

    def list_models(self) -> List[str]:
        """List available OpenAI models"""
        try:
            response = requests.get(
                f"{self.base_url}/models", headers=self._build_headers(), timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                return [model["id"] for model in data.get("data", [])]

            return []
        except Exception:
            # Return common models as fallback
            return ["gpt-4", "gpt-4-turbo-preview", "gpt-3.5-turbo", "gpt-3.5-turbo-16k"]

    def generate(
        self, prompt: str, temperature: float = 0.7, max_tokens: int = 2048, **kwargs
    ) -> LLMResponse:
        """
        Generate completion from prompt

        Args:
            prompt: Input prompt
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Returns:
            LLMResponse object
        """
        # Convert to chat format (OpenAI prefers chat API)
        messages = [{"role": "user", "content": prompt}]
        return self.chat(messages, temperature=temperature, max_tokens=max_tokens, **kwargs)

    def chat(
        self, messages: list, temperature: float = 0.7, max_tokens: int = 2048, **kwargs
    ) -> LLMResponse:
        """
        Generate chat completion

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Returns:
            LLMResponse object
        """
        model = kwargs.get("model") or self.current_model

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **{k: v for k, v in kwargs.items() if k not in ["model"]},
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self._build_headers(),
                json=payload,
                timeout=self.timeout,
            )

            if response.status_code != 200:
                self._handle_api_error(response.json(), response.status_code)

            data = response.json()
            choice = data["choices"][0]
            content = choice["message"]["content"]

            usage = data.get("usage", {})

            return self._create_llm_response(
                content=content,
                model=data.get("model", model),
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
            )

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"OpenAI API request failed: {e}")

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

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
            **{k: v for k, v in kwargs.items() if k not in ["model"]},
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
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
                        if data_str == "[DONE]":
                            break

                        try:
                            import json

                            data = json.loads(data_str)
                            delta = data["choices"][0]["delta"]
                            if "content" in delta:
                                yield delta["content"]
                        except:
                            continue

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"OpenAI streaming failed: {e}")

    def _build_headers(self, extra_headers: Optional[dict] = None) -> dict:
        """Build headers with organization if provided"""
        headers = super()._build_headers(extra_headers)

        if self.organization:
            headers["OpenAI-Organization"] = self.organization

        return headers
