"""
Tool Manager for XandAI CLI

Manages dynamic tool loading and execution.
Converts natural language to tool calls using LLM.
"""

import importlib.util
import inspect
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


class ToolManager:
    """Manages tools and converts natural language to tool calls."""

    def __init__(self, tools_dir: str = "tools", llm_provider=None, verbose: bool = False):
        """
        Initialize the ToolManager.

        Args:
            tools_dir: Directory containing tool modules
            llm_provider: LLM provider instance for NL to tool call conversion
            verbose: Enable verbose logging for debugging
        """
        self.tools_dir = Path(tools_dir)
        self.llm_provider = llm_provider
        self.verbose = verbose
        self.tools: Dict[str, Any] = {}
        self._load_tools()

    def _load_tools(self):
        """Scan tools directory and load all available tools."""
        if not self.tools_dir.exists():
            return

        # Find all Python files in tools directory
        tool_files = list(self.tools_dir.glob("*.py"))

        for tool_file in tool_files:
            if tool_file.name.startswith("_"):
                continue  # Skip __init__.py and private modules

            try:
                # Load module dynamically
                module_name = tool_file.stem
                spec = importlib.util.spec_from_file_location(module_name, tool_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)

                    # Find tool class in module
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if hasattr(obj, "get_name") and hasattr(obj, "execute"):
                            tool_instance = obj()
                            tool_name = tool_instance.get_name()
                            self.tools[tool_name] = tool_instance
                            print(f"✓ Loaded tool: {tool_name}")

            except Exception as e:
                print(f"⚠️  Failed to load tool {tool_file.name}: {e}")

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """
        Get list of available tools with their metadata.

        Returns:
            List of tool information dictionaries
        """
        tools_info = []
        for tool_name, tool_instance in self.tools.items():
            info = {
                "name": tool_name,
                "description": tool_instance.get_description(),
                "parameters": tool_instance.get_parameters(),
            }
            tools_info.append(info)
        return tools_info

    def convert_to_tool_call(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        Convert natural language input to tool call using LLM.

        Args:
            user_input: Natural language input from user

        Returns:
            Tool call dictionary if match found, None otherwise
        """
        if not self.tools:
            return None  # No tools available

        if not self.llm_provider:
            return None  # No LLM to convert

        # Build prompt with available tools
        tools_info = self.get_available_tools()
        tools_desc = "\n".join(
            [
                f"- {tool['name']}: {tool['description']}\n  Parameters: {tool['parameters']}"
                for tool in tools_info
            ]
        )

        prompt = f"""<|system|>
You are a function dispatcher AI. Your ONLY job is to return a JSON object. Do NOT add any explanations, greetings, or extra text.
</|system|>

<|user|>
AVAILABLE TOOLS:
{tools_desc}

USER REQUEST: "{user_input}"

RULES:
- If the request matches a tool, return: {{"tool": "tool_name", "args": {{"param": "value"}}}}
- If no tool matches, return: {{"tool": null}}
- Return ONLY the JSON object, nothing else
- Do NOT include markdown code blocks
- Do NOT add explanations

EXAMPLES:
Request: "what's the weather in Paris?"
Output: {{"tool": "weather_tool", "args": {{"location": "Paris", "date": "now"}}}}

Request: "tell me a joke"
Output: {{"tool": null}}

Now analyze this request and return ONLY the JSON:
</|user|>

<|assistant|>"""

        try:
            # Ask LLM to convert
            if self.verbose:
                print(f"🔍 [Tool Manager] Checking if input matches any tool...")

            response = self.llm_provider.generate(prompt, max_tokens=500)

            # Extract content from LLMResponse object
            response_text = response.content if hasattr(response, "content") else str(response)

            if self.verbose:
                print(f"🔍 [Tool Manager] LLM response: {response_text[:200]}...")

            # Parse JSON response - be aggressive about finding JSON
            response_text = response_text.strip()

            if self.verbose:
                print(f"🔍 [Tool Manager] Raw response length: {len(response_text)} chars")

            # Remove common prefixes/suffixes that LLMs add
            response_text = response_text.replace("Here's the JSON:", "")
            response_text = response_text.replace("Here is the JSON:", "")
            response_text = response_text.replace("Output:", "")
            response_text = response_text.replace("Response:", "")

            # Extract JSON from code blocks if present
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
                if self.verbose:
                    print(f"🔍 [Tool Manager] Extracted from ```json block")
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
                if self.verbose:
                    print(f"🔍 [Tool Manager] Extracted from ``` block")

            # Try to find JSON object if mixed with other text
            if "{" in response_text and "}" in response_text:
                # Find the first { and last }
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                json_candidate = response_text[start:end]

                # Try to parse this candidate
                try:
                    test_parse = json.loads(json_candidate)
                    response_text = json_candidate
                    if self.verbose:
                        print(f"🔍 [Tool Manager] Extracted JSON from position {start}:{end}")
                except:
                    # If that doesn't work, try to find complete JSON objects
                    import re

                    json_pattern = r'\{[^{}]*"tool"[^{}]*\}'
                    matches = re.findall(json_pattern, response_text)
                    if matches:
                        response_text = matches[0]
                        if self.verbose:
                            print(f"🔍 [Tool Manager] Found JSON via regex")

            if self.verbose:
                print(f"🔍 [Tool Manager] Final JSON text: {response_text}")

            tool_call = json.loads(response_text)

            # Validate tool exists
            if tool_call.get("tool") and tool_call["tool"] in self.tools:
                if self.verbose:
                    print(f"✅ [Tool Manager] Matched tool: {tool_call['tool']}")
                return tool_call
            else:
                if self.verbose:
                    print(f"ℹ️  [Tool Manager] No tool match or tool not found")

        except Exception as e:
            # If conversion fails, return None (pass to LLM normally)
            if self.verbose:
                print(f"⚠️  [Tool Manager] Error during tool detection: {e}")
            pass

        return None

    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """
        Execute a tool with given arguments.

        Args:
            tool_name: Name of the tool to execute
            args: Arguments to pass to the tool

        Returns:
            Tool execution result
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found")

        tool_instance = self.tools[tool_name]
        return tool_instance.execute(**args)

    def handle_user_input(self, user_input: str) -> tuple[bool, str]:
        """
        Main handler: detect tool, execute if needed, and prepare context for LLM.

        Flow:
        1. Detect if user input requires a tool
        2. If yes: execute tool and combine result with original message
        3. If no: return original message unchanged
        4. Return (tool_was_used, prepared_context_for_llm)

        Args:
            user_input: User's natural language input

        Returns:
            Tuple of (was_tool_used, context_for_llm)
            - If tool was used: context includes original message + tool result
            - If no tool: context is the original message
        """
        if self.verbose:
            print(f"\n[Tool Manager] Starting tool detection for: '{user_input[:50]}...'")
            print(f"[Tool Manager] Available tools: {list(self.tools.keys())}")

        # Try to convert to tool call
        tool_call = self.convert_to_tool_call(user_input)

        if not tool_call:
            # No tool match - return original message for direct LLM processing
            if self.verbose:
                print(f"[Tool Manager] No tool detected, passing original message to LLM")
            return (False, user_input)

        try:
            # Execute tool
            tool_name = tool_call["tool"]
            args = tool_call.get("args", {})

            print(f"\n🔧 Calling tool: {tool_name}")
            print(f"📝 Arguments: {json.dumps(args, indent=2)}")

            tool_result = self.execute_tool(tool_name, args)

            print(f"✓ Tool executed successfully")
            if self.verbose:
                print(f"[Tool Manager] Tool result: {str(tool_result)[:200]}...")

            # Combine user input with tool result for LLM
            combined_context = f"""User question: "{user_input}"

Data obtained from tool:
{json.dumps(tool_result, indent=2)}

Please interpret this data and provide a natural, helpful response to the user's question."""

            if self.verbose:
                print(f"[Tool Manager] Prepared combined context for LLM")

            return (True, combined_context)

        except Exception as e:
            error_msg = f"❌ Tool execution failed: {e}"
            print(error_msg)
            if self.verbose:
                import traceback

                print(f"[Tool Manager] Full error: {traceback.format_exc()}")

            # In case of error, return error context for LLM to handle
            error_context = f"""User question: "{user_input}"

Error executing tool: {str(e)}

Please inform the user about the error in a friendly way."""

            return (True, error_context)
