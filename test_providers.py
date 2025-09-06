"""
Test script for LLM Provider System

Tests both Ollama and LM Studio providers to ensure proper functionality.
"""

import pytest


def test_provider_functionality():
    """Test provider functionality - temporarily disabled until fixture setup"""
    pytest.skip("Provider test temporarily disabled - needs proper CI setup with running providers")


def test_provider_import():
    """Test that provider modules can be imported successfully"""
    from xandai.integrations.base_provider import LLMProvider, LLMResponse
    from xandai.integrations.provider_factory import LLMProviderFactory

    # Basic import test - this should always pass
    assert LLMProvider is not None
    assert LLMResponse is not None
    assert LLMProviderFactory is not None
