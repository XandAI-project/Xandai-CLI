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

    def __init__(self, tools_dir: str = "tools", llm_provider=None):
        """
        Initialize the ToolManager.

        Args:
            tools_dir: Directory containing tool modules
            llm_provider: LLM provider instance for NL to tool call conversion
        """
        self.tools_dir = Path(tools_dir)
        self.llm_provider = llm_provider
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

        prompt = f"""You are a tool dispatcher. Given user input, determine if it matches any available tool.

Available Tools:
{tools_desc}

User Input: "{user_input}"

If the input matches a tool, respond ONLY with a JSON object in this format:
{{
  "tool": "tool_name",
  "args": {{
    "param1": "value1",
    "param2": "value2"
  }}
}}

If NO tool matches, respond with:
{{"tool": null}}

Respond only with valid JSON, no other text."""

        try:
            # Ask LLM to convert
            response = self.llm_provider.generate(prompt, max_tokens=500)

            # Parse JSON response
            response_text = response.strip()

            # Extract JSON from code blocks if present
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()

            tool_call = json.loads(response_text)

            # Validate tool exists
            if tool_call.get("tool") and tool_call["tool"] in self.tools:
                return tool_call

        except Exception as e:
            # If conversion fails, return None (pass to LLM normally)
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

    def process_with_llm_interpretation(self, user_input: str, tool_result: Any) -> str:
        """
        Send both user question and tool result to LLM for interpretation.

        Args:
            user_input: Original user question
            tool_result: Result from tool execution

        Returns:
            LLM's interpreted response
        """
        if not self.llm_provider:
            return str(tool_result)

        prompt = f"""User asked: "{user_input}"

Tool returned this data:
{json.dumps(tool_result, indent=2)}

Please interpret this data and provide a natural, helpful response to the user's question."""

        try:
            response = self.llm_provider.generate(prompt, max_tokens=1000)
            return response
        except Exception as e:
            return f"Tool result: {tool_result}\n(Error interpreting: {e})"

    def handle_user_input(self, user_input: str) -> tuple[bool, str]:
        """
        Main handler: detect tool, execute, and get LLM interpretation.

        Args:
            user_input: User's natural language input

        Returns:
            Tuple of (was_tool_used, response)
        """
        # Try to convert to tool call
        tool_call = self.convert_to_tool_call(user_input)

        if not tool_call:
            # No tool match - let normal LLM flow handle it
            return (False, "")

        try:
            # Execute tool
            tool_name = tool_call["tool"]
            args = tool_call.get("args", {})

            print(f"\n🔧 Calling tool: {tool_name}")
            print(f"📝 Arguments: {json.dumps(args, indent=2)}")

            tool_result = self.execute_tool(tool_name, args)

            print(f"✓ Tool executed successfully")

            # Get LLM interpretation
            interpreted_response = self.process_with_llm_interpretation(user_input, tool_result)

            return (True, interpreted_response)

        except Exception as e:
            error_msg = f"❌ Tool execution failed: {e}"
            print(error_msg)
            return (True, error_msg)
