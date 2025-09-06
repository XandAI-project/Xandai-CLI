"""
XandAI Integrations - Ollama Client
Integration with Ollama models using native API endpoints
"""

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Generator, List, Optional

import requests


@dataclass
class OllamaResponse:
    """Structured Ollama response"""

    content: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    finish_reason: str = "stop"


class OllamaClient:
    """
    Client for Ollama integration using native API

    Provides clean interface for communication with Ollama models
    using the official native API endpoints documented at:
    https://github.com/ollama/ollama/blob/main/docs/api.md
    """

    def __init__(self, base_url: str = None):
        # Allow override via environment variable
        if base_url is None:
            base_url = os.getenv("OLLAMA_HOST", "http://localhost:11434")

        # Use Ollama's native API (no /v1 needed)
        self.base_url = base_url.rstrip("/")
        self.current_model = os.getenv("XANDAI_MODEL", "llama3.2")
        self.default_options = {
            "temperature": 0.7,
            "top_p": 0.9,
            "num_predict": 2048,
            "stream": False,
        }

        # Check connectivity (but don't fail during initialization)
        self._initial_connection_check()

    def _check_connection(self) -> bool:
        """Checks if Ollama is available using native API"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

    def _initial_connection_check(self):
        """Initial connection check during initialization (silent)"""
        # This is called during init to test connection but doesn't raise errors
        # Errors will be raised later when actually trying to use the client
        self._check_connection()

    def is_connected(self) -> bool:
        """Returns connection status"""
        return self._check_connection()

    def _raise_connection_error(self):
        """Raises a user-friendly connection error with helpful guidance"""
        error_msg = f"""
Ollama is not available at {self.base_url}

Please check:
1. Is Ollama installed? Visit: https://ollama.com/download
2. Is Ollama running? Try: 'ollama serve'
3. Is it running on a different port/host?

To use a different server, set the OLLAMA_HOST environment variable:
  export OLLAMA_HOST=http://your-server:11434

Or use XandAI commands:
  /server http://your-server:11434

Note: XandAI uses Ollama's native API endpoints
"""
        raise ConnectionError(error_msg)

    def list_models(self) -> List[str]:
        """Lists available models using native /api/tags endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
        except:
            pass
        return []

    def get_models_detailed(self) -> List[Dict[str, Any]]:
        """Gets detailed model information"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                return data.get("models", [])
        except:
            pass
        return []

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        stream: bool = False,
        **options,
    ) -> OllamaResponse:
        """
        Generates response using Ollama's native /api/generate endpoint

        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            model: Model to use (default: current_model)
            stream: Whether to use streaming
            **options: Additional options for the model
        """
        if not self.is_connected():
            self._raise_connection_error()

        # Convert single prompt to messages format for chat API
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Use chat method internally for better conversation handling
        return self.chat(messages, model, stream, **options)

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        stream: bool = False,
        **options,
    ) -> OllamaResponse:
        """
        Chat interface using Ollama's native /api/chat endpoint

        Args:
            messages: List of messages [{"role": "user", "content": "..."}, ...]
            model: Model to use
            stream: Whether to use streaming
            **options: Additional options
        """
        if not self.is_connected():
            self._raise_connection_error()

        model = model or self.current_model

        # Prepare Ollama native API payload
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {**self.default_options, **options},
        }

        try:
            if stream:
                return self._chat_stream(payload)
            else:
                return self._chat_single(payload)

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error communicating with Ollama: {e}")

    def _chat_single(self, payload: Dict[str, Any]) -> OllamaResponse:
        """Chat single response using Ollama's native /api/chat endpoint"""
        response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=120)
        response.raise_for_status()

        data = response.json()

        # Parse Ollama's native response format
        message = data.get("message", {})

        return OllamaResponse(
            content=message.get("content", ""),
            model=data.get("model", payload["model"]),
            prompt_tokens=data.get("prompt_eval_count", 0),
            completion_tokens=data.get("eval_count", 0),
            total_tokens=data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
            finish_reason="stop" if data.get("done", False) else "length",
        )

    def _chat_stream(self, payload: Dict[str, Any]) -> Generator[str, None, None]:
        """Chat streaming response using Ollama's native /api/chat endpoint"""
        response = requests.post(
            f"{self.base_url}/api/chat", json=payload, stream=True, timeout=120
        )
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode("utf-8"))
                    message = data.get("message", {})
                    if "content" in message:
                        yield message["content"]
                    if data.get("done", False):
                        break
                except json.JSONDecodeError:
                    continue

    def get_current_model(self) -> str:
        """Returns current model"""
        return self.current_model

    def set_model(self, model: str):
        """Sets current model with validation"""
        if not self.is_connected():
            # Store the model without validation if Ollama is not available
            self.current_model = model
            return

        available_models = self.list_models()
        if available_models and model not in available_models:
            raise ValueError(f"Model '{model}' not available. Available models: {available_models}")
        self.current_model = model

    def set_base_url(self, base_url: str):
        """Updates the Ollama server URL"""
        self.base_url = base_url.rstrip("/")

        # Test new connection
        if not self.is_connected():
            print(f"Warning: Cannot connect to Ollama at {self.base_url}")

    def get_model_info(self, model: Optional[str] = None) -> Dict[str, Any]:
        """Gets model information using Ollama's /api/show endpoint"""
        model = model or self.current_model
        try:
            response = requests.post(f"{self.base_url}/api/show", json={"name": model})
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return {}

    def pull_model(self, model: str) -> bool:
        """Downloads a model using Ollama's /api/pull endpoint"""
        try:
            response = requests.post(f"{self.base_url}/api/pull", json={"name": model}, timeout=300)
            return response.status_code == 200
        except:
            print(f"Note: Model pulling failed. Try 'ollama pull {model}' in your terminal")
            return False

    def update_options(self, **options):
        """Updates default options"""
        self.default_options.update(options)

    def get_connection_status(self) -> Dict[str, Any]:
        """Returns detailed connection status information"""
        is_connected = self.is_connected()
        status = {
            "connected": is_connected,
            "base_url": self.base_url,
            "current_model": self.current_model,
        }

        if is_connected:
            try:
                available_models = self.list_models()
                status["available_models"] = available_models
                status["model_count"] = len(available_models)
            except:
                status["available_models"] = []
                status["model_count"] = 0
        else:
            status["available_models"] = []
            status["model_count"] = 0
            status["error_help"] = [
                "1. Install Ollama: https://ollama.com/download",
                "2. Start Ollama: 'ollama serve'",
                f"3. Check if server is running at {self.base_url}",
            ]

        return status
