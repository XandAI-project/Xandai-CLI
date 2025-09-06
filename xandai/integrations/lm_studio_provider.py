"""
LM Studio Provider Implementation

OpenAI-compatible API implementation for LM Studio.
Supports the LM Studio server endpoints as documented.
"""

import json
from typing import Any, Dict, List, Optional

import requests

from .base_provider import LLMConfig, LLMProvider, LLMResponse, ProviderType


class LMStudioProvider(LLMProvider):
    """
    LM Studio provider using OpenAI-compatible API

    Implements the LM Studio REST API endpoints:
    - GET  /v1/models
    - POST /v1/chat/completions
    - POST /v1/completions
    - POST /v1/embeddings
    """

    def __init__(self, config: LLMConfig):
        super().__init__(config)

        # Ensure base_url includes /v1 for OpenAI compatibility
        if not config.base_url.endswith("/v1"):
            self.api_base = f"{config.base_url.rstrip('/')}/v1"
        else:
            self.api_base = config.base_url.rstrip("/")

        # Setup session with headers for efficient connection reuse
        self.session = requests.Session()
        default_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "XandAI-CLI/2.1.0",
        }

        if config.headers:
            default_headers.update(config.headers)

        self.session.headers.update(default_headers)

        # Don't auto-select - let main.py handle model selection

    def _auto_select_model(self):
        """Auto-select first available model if none specified"""
        try:
            models = self.list_models()
            if models:
                self.current_model = models[0]
                self.config.model = models[0]
        except:
            pass  # Will be handled when actually making requests

    def is_connected(self) -> bool:
        """Check if LM Studio server is available"""
        try:
            response = self.session.get(f"{self.api_base}/models", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def list_models(self) -> List[str]:
        """Get list of available LM Studio models"""
        try:
            response = self.session.get(f"{self.api_base}/models", timeout=10)
            response.raise_for_status()

            data = response.json()
            models = data.get("data", [])

            # Extract model IDs, handling both string and object formats
            model_names = []
            for model in models:
                if isinstance(model, dict):
                    model_names.append(model.get("id", "unknown"))
                else:
                    model_names.append(str(model))

            return model_names

        except Exception as e:
            # If models endpoint fails, return empty list
            return []

    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get LM Studio model information"""
        try:
            models = self.list_models()
            if model_name in models:
                return {
                    "name": model_name,
                    "provider": "lm_studio",
                    "api_type": "openai_compatible",
                    "available": True,
                    "context_length": self.config.context_length,
                }
        except Exception:
            pass

        return {"name": model_name, "provider": "lm_studio", "available": False}

    def set_model(self, model_name: str) -> bool:
        """Set current LM Studio model"""
        try:
            available_models = self.list_models()
            if not available_models:  # If cant get models, assume model exists
                self.current_model = model_name
                return True

            if model_name in available_models:
                self.current_model = model_name
                return True
            return False
        except Exception:
            # If theres an error, assume model might work
            self.current_model = model_name
            return True

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        stream: bool = False,
        progress_callback=None,  # For API compatibility, but not used
        **options,
    ) -> LLMResponse:
        """Send chat completion request to LM Studio"""

        if not self.is_connected():
            raise ConnectionError(
                f"LM Studio server is not available at {self.config.base_url}. "
                f"Make sure LM Studio is running with a model loaded."
            )

        model_to_use = model or self.current_model

        # Auto-select model if none specified
        if not model_to_use:
            available_models = self.list_models()
            if available_models:
                model_to_use = available_models[0]
                self.current_model = model_to_use
            else:
                raise ValueError(
                    "No model available in LM Studio. Please load a model in LM Studio first."
                )

        # Prepare OpenAI-compatible payload
        payload = {
            "model": model_to_use,
            "messages": messages,
            "temperature": options.get("temperature", self.config.temperature),
            "top_p": options.get("top_p", self.config.top_p),
            "max_tokens": options.get("max_tokens", self.config.max_tokens),
            "stream": False,  # Force non-streaming for now to avoid parsing issues
        }

        # Add extra options from config
        if self.config.extra_options:
            payload.update(self.config.extra_options)

        # Add any additional options passed
        for key, value in options.items():
            if key not in ["temperature", "top_p", "max_tokens"]:
                payload[key] = value

        try:
            response = self.session.post(
                f"{self.api_base}/chat/completions",
                json=payload,
                timeout=self.config.timeout,
            )
            response.raise_for_status()

            # Debug: Check response content
            response_text = response.text.strip()
            if not response_text:
                raise ConnectionError(
                    f"LM Studio returned empty response (status: {response.status_code})"
                )

            try:
                data = response.json()
            except ValueError as json_error:
                # Enhanced error reporting for JSON parsing issues
                raise ConnectionError(
                    f"LM Studio returned invalid JSON response: {json_error}\n"
                    f"Response status: {response.status_code}\n"
                    f"Response headers: {dict(response.headers)}\n"
                    f"Response content (first 200 chars): {response_text[:200]}"
                )

            # Parse OpenAI-compatible response
            if "choices" in data and data["choices"]:
                choice = data["choices"][0]
                message = choice.get("message", {})
                content = message.get("content", "")
                finish_reason = choice.get("finish_reason", "stop")
            else:
                content = ""
                finish_reason = "error"

            # Parse usage statistics
            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)

            return LLMResponse(
                content=content,
                model=model_to_use,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                finish_reason=finish_reason,
                provider="lm_studio",
                context_length=self.config.context_length,
            )

        except requests.exceptions.Timeout:
            raise ConnectionError(f"LM Studio request timed out after {self.config.timeout}s")
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Could not connect to LM Studio at {self.api_base}")
        except requests.exceptions.HTTPError as e:
            raise ConnectionError(f"LM Studio HTTP error {response.status_code}: {e}")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"LM Studio request failed: {e}")

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        **options,
    ) -> LLMResponse:
        """Generate completion using LM Studio"""

        # Convert to messages format for chat completions
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        return self.chat(messages=messages, model=model, **options)

    def health_check(self) -> Dict[str, Any]:
        """Get LM Studio health information"""
        connected = self.is_connected()
        models = []

        if connected:
            try:
                models = self.list_models()
            except:
                models = []

        return {
            "connected": connected,
            "endpoint": self.api_base,
            "current_model": self.current_model or "None",
            "available_models": models,
            "models_available": len(models),
            "provider_type": "lm_studio",
            "api_type": "openai_compatible",
            "supports_streaming": True,
            "supports_embeddings": True,
        }
