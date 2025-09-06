"""
XandAI Processors - Chat Processor
Chat Mode processor with context-aware conversation
"""

from typing import Any, Dict, List, Optional

from xandai.conversation.conversation_manager import ConversationManager
from xandai.core.app_state import AppState
from xandai.integrations.base_provider import LLMProvider, LLMResponse


class ChatProcessor:
    """
    Chat Mode Processor

    Manages context-aware conversations, maintains history
    and applies optimized prompts for conversational experience.
    """

    def __init__(self, llm_provider: LLMProvider, conversation_manager: ConversationManager):
        self.llm_provider = llm_provider
        self.conversation_manager = conversation_manager

        # System prompt for chat mode
        self.system_prompt = """You are XandAI, an intelligent CLI assistant focused on software development.

CHARACTERISTICS:
- Always respond in English
- Be concise but technically precise
- Maintain conversational and professional tone
- Use context from previous conversations when relevant
- Explain reasoning and trade-offs when necessary
- Focus on practical and maintainable solutions

CONTEXT:
- You are in conversation mode (Chat Mode)
- User can switch to Task Mode using /task
- Maintain consistency with previous history
- Avoid repeating information already provided in the session

RESPONSE FORMAT:
- Use markdown for formatting when appropriate
- Highlight code with ```
- Use lists to organize information
- Be direct but educational"""

    def process(self, user_input: str, app_state: AppState) -> str:
        """
        Processes input in Chat Mode

        Args:
            user_input: User input
            app_state: Current application state

        Returns:
            AI processed response
        """
        # Add user message to history
        self.conversation_manager.add_message(
            role="user",
            content=user_input,
            mode="chat",
            metadata={"app_state": app_state.get_context_summary()},
        )

        # Increment interaction counter
        app_state.increment_chat_interaction()

        try:
            # Prepare context
            context = self._prepare_context(user_input, app_state)

            # Generate response
            response = self._generate_response(context, app_state)

            # Add response to history
            self.conversation_manager.add_message(
                role="assistant",
                content=response.content,
                mode="chat",
                metadata={"model": response.model, "tokens": response.total_tokens},
            )

            return response.content

        except Exception as e:
            error_msg = f"Processing error: {str(e)}"
            self.conversation_manager.add_message(
                role="system", content=error_msg, mode="chat", metadata={"error": True}
            )
            return error_msg

    def _prepare_context(self, user_input: str, app_state: AppState) -> List[Dict[str, str]]:
        """
        Prepares context for sending to AI
        """
        # Basic context with system prompt
        context = [{"role": "system", "content": self._get_enhanced_system_prompt(app_state)}]

        # Add relevant history
        history = self.conversation_manager.get_context_for_ai(max_tokens=3000)
        context.extend(history)

        # Add current input
        context.append({"role": "user", "content": user_input})

        return context

    def _get_enhanced_system_prompt(self, app_state: AppState) -> str:
        """
        Builds enhanced system prompt with current context
        """
        context_info = app_state.get_context_summary()

        enhanced_prompt = self.system_prompt

        # Add project context if available
        if context_info.get("project_type") != "unknown":
            enhanced_prompt += f"\n\nPROJECT CONTEXT:\n"
            enhanced_prompt += f"- Type: {context_info.get('project_type')}\n"
            enhanced_prompt += f"- Directory: {context_info.get('root_path')}\n"
            enhanced_prompt += f"- Tracked files: {context_info.get('tracked_files')}\n"

        # Add session information
        session_info = context_info.get("interactions", {})
        if session_info.get("chat", 0) > 0:
            enhanced_prompt += f"\n\nSESSION HISTORY:\n"
            enhanced_prompt += f"- Chat interactions: {session_info.get('chat', 0)}\n"
            enhanced_prompt += f"- Task interactions: {session_info.get('task', 0)}\n"
            enhanced_prompt += f"- Duration: {context_info.get('session_duration')}\n"

        return enhanced_prompt

    def _generate_response(self, context: List[Dict[str, str]], app_state: AppState) -> LLMResponse:
        """
        Generates response using Ollama
        """
        try:
            response = self.llm_provider.chat(messages=context, temperature=0.7, max_tokens=2048)
            return response

        except Exception as e:
            # Fallback to generate if chat fails
            prompt = self._context_to_prompt(context)
            return self.llm_provider.generate(prompt=prompt, temperature=0.7, max_tokens=2048)

    def _context_to_prompt(self, context: List[Dict[str, str]]) -> str:
        """
        Converts chat context to single prompt (fallback)
        """
        prompt_parts = []

        for message in context:
            role = message["role"]
            content = message["content"]

            if role == "system":
                prompt_parts.append(f"SYSTEM: {content}")
            elif role == "user":
                prompt_parts.append(f"USER: {content}")
            elif role == "assistant":
                prompt_parts.append(f"ASSISTANT: {content}")

        prompt_parts.append("ASSISTANT:")
        return "\n\n".join(prompt_parts)

    def get_conversation_summary(self) -> Dict[str, Any]:
        """
        Returns summary of current conversation
        """
        return self.conversation_manager.get_session_summary()

    def clear_conversation(self):
        """
        Clears current conversation
        """
        self.conversation_manager.clear_session()

    def search_conversation(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Searches in current conversation
        """
        messages = self.conversation_manager.search_messages(query, limit)
        return [
            {
                "timestamp": msg.timestamp.isoformat(),
                "role": msg.role,
                "content": msg.content,
                "mode": msg.mode,
            }
            for msg in messages
        ]
