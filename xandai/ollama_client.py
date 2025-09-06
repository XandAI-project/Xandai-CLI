"""
XandAI - Ollama Client
Enhanced Ollama client with context usage tracking and native API support
"""

import json
import re
from dataclasses import dataclass
from typing import Dict, List, NamedTuple, Optional

import requests


@dataclass
class ContextUsage:
    """Context usage information"""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    context_length: int = 0

    @property
    def usage_percentage(self) -> float:
        """Calculate context usage percentage"""
        if self.context_length > 0:
            return (self.total_tokens / self.context_length) * 100
        return 0.0

    def __str__(self) -> str:
        """Human readable context usage"""
        return f"Context usage: {self.usage_percentage:.1f}% ({self.total_tokens}/{self.context_length})"


@dataclass
class OllamaResponse:
    """Enhanced Ollama response with context tracking"""

    content: str
    model: str
    context_usage: ContextUsage
    finish_reason: str = "stop"

    def print_with_context(self) -> str:
        """Return content with context usage appended"""
        return f"{self.content}\\n\\n{self.context_usage}"


class OllamaClient:
    """
    Production-ready Ollama client with context usage tracking

    Features:
    - Native Ollama API support
    - Context usage calculation and display
    - Model management
    - Connection health monitoring
    - Error handling and recovery
    """

    def __init__(self, base_url: str = "http://127.0.0.1:11434"):
        """Initialize Ollama client"""
        self.base_url = base_url.rstrip("/")
        self.current_model: Optional[str] = None
        self.default_options = {
            "temperature": 0.7,
            "top_p": 0.9,
            "num_predict": 2048,
            "num_ctx": 4096,  # Context length
        }

        # Session for connection reuse
        self.session = requests.Session()
        self.session.headers.update(
            {"Content-Type": "application/json", "Accept": "application/json"}
        )

    def is_connected(self) -> bool:
        """Check if Ollama server is available"""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def list_models(self) -> List[str]:
        """Get list of available models"""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except requests.RequestException as e:
            raise ConnectionError(f"Failed to list models: {e}")

    def get_model_info(self, model_name: str) -> Dict:
        """Get detailed model information"""
        try:
            payload = {"name": model_name}
            response = self.session.post(f"{self.base_url}/api/show", json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return {}

    def set_model(self, model_name: str):
        """Set the current model"""
        models = self.list_models()
        if model_name not in models:
            raise ValueError(f"Model '{model_name}' not available. Available: {models}")
        self.current_model = model_name

    def get_current_model(self) -> str:
        """Get current model name"""
        return self.current_model or "No model selected"

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        stream: bool = False,
        progress_callback=None,
        **options,
    ) -> OllamaResponse:
        """
        Send chat request to Ollama

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (defaults to current_model)
            stream: Whether to stream response
            progress_callback: Function to call for progress updates
            **options: Additional Ollama options

        Returns:
            OllamaResponse with content and context usage
        """
        if not self.is_connected():
            raise ConnectionError("Ollama server is not available")

        model = model or self.current_model
        if not model:
            raise ValueError("No model specified")

        # Prepare request payload
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {**self.default_options, **options},
        }

        try:
            if stream and progress_callback:
                return self._chat_with_streaming_progress(payload, progress_callback)
            else:
                response = self.session.post(
                    f"{self.base_url}/api/chat", json=payload, timeout=600  # 10 minutes
                )
                response.raise_for_status()

                # Parse response
                data = response.json()
                return self._parse_response(data, payload)

        except requests.RequestException as e:
            raise ConnectionError(f"Chat request failed: {e}")

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        **options,
    ) -> OllamaResponse:
        """
        Generate response from prompt (convenience method)

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            model: Model to use
            **options: Additional options

        Returns:
            OllamaResponse with content and context usage
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        return self.chat(messages, model, **options)

    def _chat_with_streaming_progress(self, payload: Dict, progress_callback) -> OllamaResponse:
        """Handle streaming chat with progress updates"""
        payload["stream"] = True

        response = self.session.post(
            f"{self.base_url}/api/chat",
            json=payload,
            stream=True,
            timeout=600,  # 10 minutes
        )
        response.raise_for_status()

        content_chunks = []
        chunk_count = 0
        final_data = {}

        try:
            for line in response.iter_lines():
                if line:
                    try:
                        # Decode and clean the line
                        line_text = line.decode("utf-8").strip()

                        # Skip empty lines
                        if not line_text:
                            continue

                        # Handle multiple JSON objects in one line (split by newlines)
                        json_parts = line_text.split("\n")

                        for json_part in json_parts:
                            json_part = json_part.strip()
                            if not json_part:
                                continue

                            try:
                                # Try to parse this JSON part
                                chunk_data = json.loads(json_part)
                                chunk_count += 1

                                # Progress callback every 10 chunks
                                if chunk_count % 10 == 0 and progress_callback:
                                    progress_callback(f"📦 {chunk_count} chunks received...")

                                # Extract content from chunk
                                if "message" in chunk_data:
                                    chunk_content = chunk_data["message"].get("content", "")
                                    if chunk_content:
                                        content_chunks.append(chunk_content)

                                # Check if done
                                if chunk_data.get("done", False):
                                    final_data = chunk_data
                                    break

                            except json.JSONDecodeError as json_err:
                                # Try to extract JSON from partial data by finding valid JSON boundaries
                                try:
                                    # Look for complete JSON objects using bracket/brace counting
                                    valid_json = self._extract_valid_json(json_part)
                                    if valid_json:
                                        chunk_data = json.loads(valid_json)
                                        chunk_count += 1

                                        if "message" in chunk_data:
                                            chunk_content = chunk_data["message"].get("content", "")
                                            if chunk_content:
                                                content_chunks.append(chunk_content)

                                        if chunk_data.get("done", False):
                                            final_data = chunk_data
                                            break
                                except:
                                    # Skip this malformed chunk completely
                                    continue

                        # If we found the final chunk, break out of main loop too
                        if final_data.get("done", False):
                            break

                    except (UnicodeDecodeError, AttributeError):
                        continue  # Skip malformed lines

            # Combine all content
            full_content = "".join(content_chunks)

            # Create final response data structure
            final_response_data = {
                "message": {"content": full_content},
                "model": payload["model"],
                "prompt_eval_count": final_data.get("prompt_eval_count", 0),
                "eval_count": final_data.get("eval_count", 0),
                "done": True,
            }

            if progress_callback:
                progress_callback(f"✅ Complete! ({chunk_count} chunks total)")

            return self._parse_response(final_response_data, payload)

        except Exception:
            # Fallback to non-streaming if streaming fails
            if progress_callback:
                progress_callback("⚠️ Streaming failed, falling back...")
            payload["stream"] = False
            response = self.session.post(
                f"{self.base_url}/api/chat", json=payload, timeout=600  # 10 minutes
            )
            response.raise_for_status()
            data = response.json()
            return self._parse_response(data, payload)

    def _extract_valid_json(self, text: str) -> Optional[str]:
        """Extract the first valid JSON object from text with potential extra data"""
        try:
            # Look for JSON object boundaries
            brace_count = 0
            start_found = False
            json_end = -1

            for i, char in enumerate(text):
                if char == "{":
                    if not start_found:
                        start_found = True
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    if start_found and brace_count == 0:
                        json_end = i + 1
                        break

            if json_end > 0:
                potential_json = text[:json_end]
                # Validate that this is actually valid JSON
                json.loads(potential_json)
                return potential_json

        except (json.JSONDecodeError, IndexError):
            pass

        return None

    def _parse_response(self, data: Dict, payload: Dict) -> OllamaResponse:
        """Parse Ollama API response into OllamaResponse object"""
        # Extract message content
        message = data.get("message", {})
        content = message.get("content", "")

        # Extract context usage information
        context_usage = ContextUsage(
            prompt_tokens=data.get("prompt_eval_count", 0),
            completion_tokens=data.get("eval_count", 0),
            total_tokens=data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
            context_length=payload.get("options", {}).get(
                "num_ctx", self.default_options["num_ctx"]
            ),
        )

        return OllamaResponse(
            content=content,
            model=data.get("model", payload["model"]),
            context_usage=context_usage,
            finish_reason="stop" if data.get("done", False) else "length",
        )

    def health_check(self) -> Dict[str, any]:
        """Perform comprehensive health check"""
        health_info = {
            "connected": False,
            "models_available": 0,
            "current_model": self.current_model,
            "endpoint": self.base_url,
        }

        try:
            # Test connection
            health_info["connected"] = self.is_connected()

            if health_info["connected"]:
                # Get model count
                models = self.list_models()
                health_info["models_available"] = len(models)
                health_info["models"] = models[:5]  # First 5 models

                # Test current model if set
                if self.current_model:
                    model_info = self.get_model_info(self.current_model)
                    health_info["current_model_info"] = {
                        "name": model_info.get("modelfile", {}).get("name", "Unknown"),
                        "size": model_info.get("details", {}).get("parameter_size", "Unknown"),
                    }
        except Exception as e:
            health_info["error"] = str(e)

        return health_info

    def close(self):
        """Close the session"""
        self.session.close()
