"""
Test script for XandAI CLI Tools System

This script tests the tool manager and tool calling functionality.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from xandai.utils.tool_manager import ToolManager


class MockLLMProvider:
    """Mock LLM provider for testing"""

    def generate(self, prompt, max_tokens=500):
        """Simulate LLM response for tool detection"""
        # Check if prompt asks about weather
        if "weather" in prompt.lower():
            # Simulate LLM recognizing the weather tool
            if "los angeles" in prompt.lower():
                return """{"tool": "weather_tool", "args": {"location": "los angeles", "date": "now"}}"""
            elif "new york" in prompt.lower():
                return (
                    """{"tool": "weather_tool", "args": {"location": "new york", "date": "now"}}"""
                )

        # No tool match
        return '{"tool": null}'


def test_tool_loading():
    """Test if tools are loaded correctly"""
    print("🧪 Test 1: Tool Loading")
    print("-" * 50)

    tool_manager = ToolManager(tools_dir="tools")

    if not tool_manager.tools:
        print("❌ No tools loaded!")
        return False

    print(f"✅ Loaded {len(tool_manager.tools)} tool(s):")
    for tool_name in tool_manager.tools.keys():
        print(f"   • {tool_name}")

    return True


def test_tool_metadata():
    """Test if tool metadata is accessible"""
    print("\n🧪 Test 2: Tool Metadata")
    print("-" * 50)

    tool_manager = ToolManager(tools_dir="tools")
    tools_info = tool_manager.get_available_tools()

    if not tools_info:
        print("❌ No tool metadata available!")
        return False

    for tool in tools_info:
        print(f"\n✅ Tool: {tool['name']}")
        print(f"   Description: {tool['description']}")
        print(f"   Parameters: {tool['parameters']}")

    return True


def test_tool_execution():
    """Test direct tool execution"""
    print("\n🧪 Test 3: Direct Tool Execution")
    print("-" * 50)

    tool_manager = ToolManager(tools_dir="tools")

    if "weather_tool" not in tool_manager.tools:
        print("❌ weather_tool not available!")
        return False

    try:
        result = tool_manager.execute_tool(
            "weather_tool", {"location": "Los Angeles", "date": "now"}
        )

        print(f"✅ Tool executed successfully!")
        print(f"   Result: {result}")
        return True

    except Exception as e:
        print(f"❌ Tool execution failed: {e}")
        return False


def test_nl_to_tool_call():
    """Test natural language to tool call conversion"""
    print("\n🧪 Test 4: Natural Language to Tool Call")
    print("-" * 50)

    mock_llm = MockLLMProvider()
    tool_manager = ToolManager(tools_dir="tools", llm_provider=mock_llm)

    test_queries = [
        "what is the weather in los angeles now?",
        "tell me about the weather in new york",
        "what is the capital of France?",  # Should not match any tool
    ]

    for query in test_queries:
        print(f"\n📝 Query: '{query}'")
        tool_call = tool_manager.convert_to_tool_call(query)

        if tool_call:
            print(f"   ✅ Matched tool: {tool_call['tool']}")
            print(f"   📦 Arguments: {tool_call['args']}")
        else:
            print("   ℹ️  No tool match (will use regular LLM)")

    return True


def test_full_workflow():
    """Test complete workflow: NL → Tool Call → Execution → Interpretation"""
    print("\n🧪 Test 5: Full Workflow")
    print("-" * 50)

    mock_llm = MockLLMProvider()
    tool_manager = ToolManager(tools_dir="tools", llm_provider=mock_llm)

    query = "what is the weather in los angeles now?"
    print(f"📝 User query: '{query}'")

    # This would be called automatically in ChatREPL
    was_tool_used, response = tool_manager.handle_user_input(query)

    if was_tool_used:
        print(f"\n✅ Tool workflow completed!")
        print(f"📄 Response preview: {response[:200]}...")
        return True
    else:
        print("❌ Tool was not used!")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 50)
    print("XandAI CLI Tools System - Test Suite")
    print("=" * 50 + "\n")

    tests = [
        test_tool_loading,
        test_tool_metadata,
        test_tool_execution,
        test_nl_to_tool_call,
        test_full_workflow,
    ]

    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"\n❌ Test failed with exception: {e}")
            results.append(False)

    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")

    if all(results):
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed!")

    return all(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
