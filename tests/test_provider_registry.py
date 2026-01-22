"""
Tests for Provider Registry System
"""

import pytest

from xandai.integrations.base_provider import LLMProvider, LLMResponse, ProviderType
from xandai.providers.provider_registry import ProviderRegistry, get_provider, register_provider


class MockProvider(LLMProvider):
    """Mock provider for testing"""

    def __init__(self, **kwargs):
        self.config = kwargs

    def get_provider_type(self) -> ProviderType:
        return ProviderType.OLLAMA

    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        return LLMResponse(
            content="Mock response",
            model="mock-model",
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
        )

    def chat(self, messages: list, **kwargs) -> LLMResponse:
        return self.generate("", **kwargs)

    def list_models(self):
        return ["model1", "model2"]

    def is_connected(self) -> bool:
        return True

    def get_model_info(self, model_name: str):
        return {"name": model_name}

    def set_model(self, model_name: str) -> bool:
        return True

    def health_check(self) -> bool:
        return True


class TestProviderRegistry:
    """Test provider registry functionality"""

    def setup_method(self):
        """Setup for each test"""
        self.registry = ProviderRegistry()
        self.registry._providers.clear()
        self.registry._provider_instances.clear()

    def test_register_provider(self):
        """Test registering a provider"""
        self.registry.register(MockProvider, "mock")
        assert "mock" in self.registry.list_providers()

    def test_get_provider(self):
        """Test getting a provider instance"""
        self.registry.register(MockProvider, "mock")
        provider = self.registry.get_provider("mock", test_param="value")

        assert isinstance(provider, MockProvider)
        assert provider.config.get("test_param") == "value"

    def test_provider_not_found(self):
        """Test error when provider not found"""
        with pytest.raises(ValueError, match="Provider 'nonexistent' not found"):
            self.registry.get_provider("nonexistent")

    def test_list_providers(self):
        """Test listing providers"""
        self.registry.register(MockProvider, "mock1")
        self.registry.register(MockProvider, "mock2")

        providers = self.registry.list_providers()
        assert "mock1" in providers
        assert "mock2" in providers

    def test_get_provider_info(self):
        """Test getting provider information"""
        self.registry.register(MockProvider, "mock")
        info = self.registry.get_provider_info("mock")

        assert info["name"] == "mock"
        assert info["class"] == "MockProvider"
        assert "type" in info

    def test_list_by_type(self):
        """Test filtering providers by type"""
        self.registry.register(MockProvider, "mock")
        providers = self.registry.list_by_type(ProviderType.OLLAMA)

        assert "mock" in providers

    def test_caching(self):
        """Test that providers are cached"""
        self.registry.register(MockProvider, "mock")

        provider1 = self.registry.get_provider("mock", param="value")
        provider2 = self.registry.get_provider("mock", param="value")

        assert provider1 is provider2

    def test_clear_cache(self):
        """Test clearing provider cache"""
        self.registry.register(MockProvider, "mock")
        provider1 = self.registry.get_provider("mock")

        self.registry.clear_cache()
        provider2 = self.registry.get_provider("mock")

        assert provider1 is not provider2


def test_convenience_functions():
    """Test convenience functions"""
    register_provider(MockProvider, "test_mock")

    providers = get_provider("test_mock")
    assert isinstance(providers, MockProvider)
