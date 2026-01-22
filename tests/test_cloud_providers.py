"""
Tests for Cloud Providers
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from xandai.integrations.base_provider import ProviderType
from xandai.providers.cloud.anthropic_provider import AnthropicProvider
from xandai.providers.cloud.openai_provider import OpenAIProvider


class TestOpenAIProvider:
    """Test OpenAI provider"""

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_initialization(self):
        """Test provider initialization"""
        provider = OpenAIProvider()
        assert provider.api_key == "test-key"
        assert provider.current_model == "gpt-3.5-turbo"

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    @patch("requests.post")
    def test_chat(self, mock_post):
        """Test chat generation"""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello!"}}],
            "model": "gpt-3.5-turbo",
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }
        mock_post.return_value = mock_response

        provider = OpenAIProvider()
        result = provider.chat([{"role": "user", "content": "Hi"}])

        assert result.content == "Hello!"
        assert result.model == "gpt-3.5-turbo"
        assert result.prompt_tokens == 10
        assert result.completion_tokens == 5

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    @patch("requests.post")
    def test_generate(self, mock_post):
        """Test text generation"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Generated text"}}],
            "model": "gpt-3.5-turbo",
            "usage": {"prompt_tokens": 15, "completion_tokens": 10},
        }
        mock_post.return_value = mock_response

        provider = OpenAIProvider()
        result = provider.generate("Test prompt")

        assert result.content == "Generated text"

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    @patch("requests.get")
    def test_list_models(self, mock_get):
        """Test listing models"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"id": "gpt-4"}, {"id": "gpt-3.5-turbo"}]}
        mock_get.return_value = mock_response

        provider = OpenAIProvider()
        models = provider.list_models()

        assert "gpt-4" in models
        assert "gpt-3.5-turbo" in models

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    @patch("requests.post")
    def test_api_error_handling(self, mock_post):
        """Test API error handling"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": {"message": "Bad request"}}
        mock_post.return_value = mock_response

        provider = OpenAIProvider()

        with pytest.raises(RuntimeError, match="API Error"):
            provider.chat([{"role": "user", "content": "Test"}])

    def test_missing_api_key(self):
        """Test error when API key is missing"""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="requires an API key"):
                OpenAIProvider()


class TestAnthropicProvider:
    """Test Anthropic provider"""

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_initialization(self):
        """Test provider initialization"""
        provider = AnthropicProvider()
        assert provider.api_key == "test-key"
        assert "claude" in provider.current_model

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    @patch("requests.post")
    def test_chat(self, mock_post):
        """Test chat generation"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [{"text": "Hello from Claude!"}],
            "model": "claude-3-sonnet-20240229",
            "usage": {"input_tokens": 12, "output_tokens": 8},
        }
        mock_post.return_value = mock_response

        provider = AnthropicProvider()
        result = provider.chat([{"role": "user", "content": "Hi"}])

        assert result.content == "Hello from Claude!"
        assert result.prompt_tokens == 12
        assert result.completion_tokens == 8

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    @patch("requests.post")
    def test_generate(self, mock_post):
        """Test text generation"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [{"text": "Generated response"}],
            "model": "claude-3-sonnet-20240229",
            "usage": {"input_tokens": 10, "output_tokens": 5},
        }
        mock_post.return_value = mock_response

        provider = AnthropicProvider()
        result = provider.generate("Test prompt")

        assert result.content == "Generated response"

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_list_models(self):
        """Test listing models"""
        provider = AnthropicProvider()
        models = provider.list_models()

        assert any("claude-3" in model for model in models)

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    @patch("requests.post")
    def test_system_message_handling(self, mock_post):
        """Test system message extraction"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [{"text": "Response"}],
            "model": "claude-3-sonnet-20240229",
            "usage": {"input_tokens": 10, "output_tokens": 5},
        }
        mock_post.return_value = mock_response

        provider = AnthropicProvider()
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hi"},
        ]

        provider.chat(messages)

        # Check that system message was extracted
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert "system" in payload
        assert payload["system"] == "You are helpful"

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    @patch("requests.post")
    def test_api_error_handling(self, mock_post):
        """Test API error handling"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": {"message": "Unauthorized"}}
        mock_post.return_value = mock_response

        provider = AnthropicProvider()

        with pytest.raises(RuntimeError, match="API Error"):
            provider.chat([{"role": "user", "content": "Test"}])

    def test_missing_api_key(self):
        """Test error when API key is missing"""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="requires an API key"):
                AnthropicProvider()
