#!/usr/bin/env python3
"""
Exemplo de uso do AgentProcessor

Este script demonstra como o AgentProcessor funciona internamente.
Para uso real, utilize o comando /agent no CLI do XandAI.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from xandai.conversation.conversation_manager import ConversationManager
from xandai.core.app_state import AppState
from xandai.integrations.provider_factory import LLMProviderFactory
from xandai.processors.agent_processor import AgentProcessor


def print_step_info(step):
    """Prints step information"""
    status = "✅" if step.success else "❌"
    print(f"{status} [Step {step.step_number}] {step.step_name}")
    print(f"   Tokens: {step.tokens_used}")
    if step.response:
        summary = step.response[:80] + "..." if len(step.response) > 80 else step.response
        print(f"   Response: {summary}")
    print()


def main():
    """Main example function"""
    print("=" * 60)
    print("XandAI Agent Mode - Example Demonstration")
    print("=" * 60)
    print()

    # Initialize components
    print("🔧 Initializing components...")
    try:
        llm_provider = LLMProviderFactory.create_auto_detect()
        print(f"✓ Connected to: {llm_provider.get_provider_type().value}")
    except Exception as e:
        print(f"❌ Error connecting to LLM provider: {e}")
        print("\nMake sure Ollama or LM Studio is running:")
        print("  - Ollama: ollama serve")
        print("  - LM Studio: Start server on port 1234")
        return

    conversation_manager = ConversationManager()
    app_state = AppState()
    agent_processor = AgentProcessor(llm_provider, conversation_manager)

    print()
    print("=" * 60)
    print("Example 1: Simple Code Explanation")
    print("=" * 60)
    print()

    instruction = "Explain what a list comprehension is in Python with examples"
    print(f"Instruction: {instruction}")
    print()
    print("Processing...")
    print()

    # Process with agent
    result = agent_processor.process(instruction, app_state)

    # Show steps
    print("Agent Execution Steps:")
    print("-" * 60)
    for step in result.steps:
        print_step_info(step)

    # Show result
    print("=" * 60)
    if result.success:
        print("✓ Agent Task Complete")
        print(f"  Reason: {result.stopped_reason}")
        print(f"  Total calls: {result.total_calls}/{agent_processor.max_calls}")
        print(f"  Total tokens: {result.total_tokens}")
        print()
        print("Final Output:")
        print("-" * 60)
        print(result.final_output)
    else:
        print("✗ Agent Task Failed")
        if result.error_message:
            print(f"  Error: {result.error_message}")
    print("=" * 60)
    print()

    # Example 2: Change limit
    print()
    print("=" * 60)
    print("Example 2: Changing Agent Limit")
    print("=" * 60)
    print()

    print(f"Current limit: {agent_processor.max_calls} calls")
    agent_processor.set_max_calls(10)
    print(f"New limit: {agent_processor.max_calls} calls")
    print()

    # Example 3: Show configuration
    print("=" * 60)
    print("Agent Configuration")
    print("=" * 60)
    print()
    print(f"Max calls: {agent_processor.max_calls}")
    print(f"Verbose mode: {agent_processor.verbose}")
    print(f"Provider: {llm_provider.get_provider_type().value}")
    print(f"Model: {llm_provider.get_current_model()}")
    print()

    print("=" * 60)
    print("To use agent mode in XandAI CLI:")
    print("=" * 60)
    print()
    print("  xandai")
    print("  /agent <your instruction>")
    print("  /set-agent-limit 30")
    print()
    print("See example/agent_demo.md for more examples!")
    print()


if __name__ == "__main__":
    main()
