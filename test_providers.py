"""
Test script for LLM Provider System

Tests both Ollama and LM Studio providers to ensure proper functionality.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from xandai.integrations.provider_factory import LLMProviderFactory
from xandai.integrations.base_provider import LLMProvider, LLMResponse

def test_provider(provider: LLMProvider, provider_name: str):
    """Test a provider with basic functionality"""
    print(f"\n Testing {provider_name} Provider")
    print("=" * 50)
    
    # Test connection
    print(" Testing connection...")
    connected = provider.is_connected()
    print(f"   Connected: {' YES' if connected else ' NO'}")
    
    if not connected:
        print(f"   Skipping {provider_name} tests - server not available")
        return False
    
    # Test models list
    print(" Getting models...")
    try:
        models = provider.list_models()
        print(f"   Found {len(models)} models: {models[:3]}{'...' if len(models) > 3 else ''}")
        
        if not models:
            print(f"     No models available in {provider_name}")
            return False
            
    except Exception as e:
        print(f"    Error getting models: {e}")
        return False
    
    # Test health check
    print(" Health check...")
    try:
        health = provider.health_check()
        print(f"   Endpoint: {health.get('endpoint', 'unknown')}")
        print(f"   Current model: {health.get('current_model', 'None')}")
        print(f"   Provider type: {health.get('provider_type', 'unknown')}")
        
    except Exception as e:
        print(f"    Error in health check: {e}")
        return False
    
    # Test simple chat
    print(" Testing simple chat...")
    try:
        messages = [{"role": "user", "content": "Hello! Just say 'Hi' back."}]
        response: LLMResponse = provider.chat(messages=messages)
        
        print(f"   Response: {response.content[:50]}{'...' if len(response.content) > 50 else ''}")
        print(f"   Model used: {response.model}")
        print(f"   Tokens: {response.prompt_tokens}  {response.completion_tokens} ({response.total_tokens} total)")
        print(f"   Provider: {response.provider}")
        
    except Exception as e:
        print(f"    Error in chat test: {e}")
        return False
    
    print(f" {provider_name} provider tests completed successfully!")
    return True

def main():
    """Run all provider tests"""
    print(" XandAI LLM Provider System Test")
    print("Testing multi-provider architecture...")
    print()
    
    results = {}
    
    # Test Ollama
    print(" Testing Ollama Provider")
    try:
        ollama_provider = LLMProviderFactory.create_provider("ollama")
        results["ollama"] = test_provider(ollama_provider, "Ollama")
    except Exception as e:
        print(f" Failed to create Ollama provider: {e}")
        results["ollama"] = False
    
    # Test LM Studio
    print("\n Testing LM Studio Provider")
    try:
        lm_studio_provider = LLMProviderFactory.create_provider("lm_studio")
        results["lm_studio"] = test_provider(lm_studio_provider, "LM Studio")
    except Exception as e:
        print(f" Failed to create LM Studio provider: {e}")
        results["lm_studio"] = False
    
    # Test Auto-detection
    print("\n Testing Auto-Detection")
    try:
        auto_provider = LLMProviderFactory.create_auto_detect()
        detected_type = auto_provider.get_provider_type().value
        print(f" Auto-detected provider: {detected_type.upper()}")
        
        if auto_provider.is_connected():
            print(" Auto-detected provider is working!")
            results["auto_detect"] = True
        else:
            print(" Auto-detected provider is not connected")
            results["auto_detect"] = False
            
    except Exception as e:
        print(f" Auto-detection failed: {e}")
        results["auto_detect"] = False
    
    # Test Environment Variables
    print("\n Testing Environment Variables")
    try:
        # Test with env vars
        os.environ["XANDAI_PROVIDER"] = "ollama"
        os.environ["XANDAI_TEMPERATURE"] = "0.8"
        
        env_provider = LLMProviderFactory.create_from_env()
        print(f" Environment provider type: {env_provider.get_provider_type().value}")
        print(f" Temperature from env: {env_provider.config.temperature}")
        
        results["env_config"] = True
        
    except Exception as e:
        print(f" Environment configuration failed: {e}")
        results["env_config"] = False
    
    # Summary
    print("\n" + "=" * 60)
    print(" TEST SUMMARY")
    print("=" * 60)
    
    for test, passed in results.items():
        status = " PASS" if passed else " FAIL" 
        print(f"  {test.replace('_', ' ').title():<20} {status}")
    
    passed_tests = sum(results.values())
    total_tests = len(results)
    
    print(f"\nResults: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print(" ALL TESTS PASSED! LLM Provider system is working correctly!")
        return 0
    elif passed_tests > 0:
        print("  PARTIAL SUCCESS - Some providers are working")
        return 1  
    else:
        print(" ALL TESTS FAILED - Check your provider installations")
        return 2

if __name__ == "__main__":
    sys.exit(main())
