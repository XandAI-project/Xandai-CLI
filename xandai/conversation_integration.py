"""
Integration module for the new robust conversation history system.
This replaces the existing basic history management in XandAI CLI.
"""

from typing import List, Dict, Optional, Any
from rich.console import Console
from datetime import datetime

from .conversation import (
    HistoryManager, HistoryManagerError,
    MessageRole, MessageType, ToolCall, ToolResult
)

console = Console()


class ConversationIntegration:
    """
    Integration layer for the new conversation history system.
    
    This class provides a bridge between the existing CLI code and the new
    robust conversation history system, maintaining backward compatibility
    while adding new capabilities.
    """
    
    def __init__(self, api, storage_dir: Optional[str] = None):
        """Initialize the conversation integration."""
        self.api = api
        self.history_manager = HistoryManager(storage_dir=storage_dir, api=api)
        self.current_model: Optional[str] = None
        
        # Track context for old-style integration
        self.context_history = []  # For backward compatibility
    
    def set_model(self, model_name: str):
        """Set the current model for conversation management."""
        if model_name != self.current_model:
            self.current_model = model_name
            self.history_manager.set_model(model_name)
            console.print(f"[dim]Conversation system configured for: {model_name}[/dim]")
    
    def add_user_message(self, content: str, **kwargs) -> str:
        """
        Add user message and return message ID.
        
        Args:
            content: User message content
            **kwargs: Additional metadata
            
        Returns:
            Message ID for reference
        """
        if not self.current_model:
            raise HistoryManagerError("No model set - call set_model() first")
        
        message = self.history_manager.add_user_message(content, **kwargs)
        
        # Update legacy context for backward compatibility
        self.context_history.append({
            'role': 'user',
            'content': content,
            'tokens': message.tokens,
            'timestamp': message.timestamp.timestamp(),
            'metadata': kwargs
        })
        
        return message.id
    
    def add_assistant_message(self, content: str, tool_calls: Optional[List[Dict]] = None, **kwargs) -> str:
        """
        Add assistant message with optional tool calls.
        
        Args:
            content: Assistant response content
            tool_calls: List of tool calls (old format for compatibility)
            **kwargs: Additional metadata
            
        Returns:
            Message ID for reference
        """
        if not self.current_model:
            raise HistoryManagerError("No model set - call set_model() first")
        
        # Convert old-style tool calls to new format
        converted_tool_calls = []
        if tool_calls:
            for tc in tool_calls:
                converted_tool_calls.append(ToolCall(
                    id=tc.get('id', f"call_{datetime.now().timestamp()}"),
                    name=tc.get('name', tc.get('function', 'unknown')),
                    arguments=tc.get('arguments', tc.get('args', {}))
                ))
        
        message = self.history_manager.add_assistant_message(
            content=content,
            tool_calls=converted_tool_calls or None,
            **kwargs
        )
        
        # Update legacy context for backward compatibility
        self.context_history.append({
            'role': 'assistant',
            'content': content,
            'tokens': message.tokens,
            'timestamp': message.timestamp.timestamp(),
            'metadata': kwargs
        })
        
        return message.id
    
    def add_system_message(self, content: str, message_type: str = "system_prompt", **kwargs) -> str:
        """Add system message with type classification."""
        if not self.current_model:
            raise HistoryManagerError("No model set - call set_model() first")
        
        # Map old string types to new enum types
        type_mapping = {
            "system_prompt": MessageType.SYSTEM_PROMPT,
            "coding_rule": MessageType.CODING_RULE,
            "context_summary": MessageType.CONTEXT_SUMMARY,
            "session_marker": MessageType.SESSION_MARKER
        }
        
        msg_type = type_mapping.get(message_type, MessageType.SYSTEM_PROMPT)
        
        message = self.history_manager.add_system_message(
            content=content,
            message_type=msg_type,
            **kwargs
        )
        
        return message.id
    
    def add_tool_results(self, results: List[Dict], **kwargs) -> str:
        """Add tool execution results."""
        if not self.current_model:
            raise HistoryManagerError("No model set - call set_model() first")
        
        # Convert old-style results to new format
        converted_results = []
        for result in results:
            converted_results.append(ToolResult(
                tool_call_id=result.get('tool_call_id', result.get('id', 'unknown')),
                content=result.get('content', str(result.get('result', ''))),
                success=result.get('success', True),
                error=result.get('error'),
                metadata=result.get('metadata', {})
            ))
        
        message = self.history_manager.add_tool_results(converted_results, **kwargs)
        return message.id
    
    def get_context_for_prompt(self, max_tokens: Optional[int] = None) -> str:
        """
        Get conversation context formatted for LLM prompt.
        
        Args:
            max_tokens: Maximum tokens to include (uses model default if None)
            
        Returns:
            Formatted conversation context
        """
        if not self.current_model:
            return ""
        
        messages = self.history_manager.get_context_for_model(max_tokens)
        
        # Format messages for prompt inclusion
        formatted_parts = []
        for msg in messages:
            if msg.message_type == MessageType.CONTEXT_SUMMARY:
                # Special formatting for summaries
                formatted_parts.append(f"[CONVERSATION SUMMARY]: {msg.content}")
            elif msg.role == MessageRole.USER:
                formatted_parts.append(f"USER: {msg.content}")
            elif msg.role == MessageRole.ASSISTANT:
                content = msg.content
                if msg.tool_calls:
                    tool_info = ", ".join([f"{tc.name}({tc.arguments})" for tc in msg.tool_calls])
                    content += f" [Tools: {tool_info}]"
                formatted_parts.append(f"ASSISTANT: {content}")
            elif msg.role == MessageRole.SYSTEM and msg.message_type == MessageType.CODING_RULE:
                formatted_parts.append(f"[CODING RULE]: {msg.content}")
        
        return "\n".join(formatted_parts) if formatted_parts else ""
    
    def get_context_status(self) -> Dict[str, Any]:
        """Get current context status for display."""
        if not self.current_model:
            return {"error": "No model set"}
        
        status = self.history_manager.get_context_status()
        
        # Add legacy fields for backward compatibility
        status["context_usage_percentage"] = status.get("utilization", 0) * 100
        status["current_context_tokens"] = status.get("total_tokens", 0)
        status["max_context_tokens"] = status.get("available_context", 0)
        
        return status
    
    def get_context_usage_percentage(self) -> float:
        """Get context usage percentage (legacy compatibility)."""
        status = self.get_context_status()
        return status.get("context_usage_percentage", 0.0)
    
    def flush_context(self, preserve_recent: bool = True) -> Dict[str, Any]:
        """
        Flush context using the new optimization system.
        
        Args:
            preserve_recent: Whether to preserve recent messages
            
        Returns:
            Optimization report
        """
        if not self.current_model:
            return {"error": "No model set"}
        
        # Try auto-summarization first
        summary_report = self.history_manager.auto_summarize()
        if summary_report and summary_report.get("summaries_created", 0) > 0:
            console.print(f"[green]✓ Auto-summarization: {summary_report['summaries_created']} summaries created[/green]")
            return summary_report
        
        # Fall back to optimization
        optimization_report = self.history_manager.force_optimization()
        if optimization_report.get("tokens_saved", 0) > 0:
            console.print(f"[green]✓ Context optimized: {optimization_report['tokens_saved']} tokens saved[/green]")
        
        return optimization_report
    
    def add_to_context_history(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Legacy method for backward compatibility."""
        if role == "user":
            self.add_user_message(content, **(metadata or {}))
        elif role == "assistant":
            self.add_assistant_message(content, **(metadata or {}))
        elif role == "system":
            msg_type = metadata.get("type", "system_prompt") if metadata else "system_prompt"
            self.add_system_message(content, message_type=msg_type)
    
    def get_conversation_summary(self) -> str:
        """Get human-readable conversation summary."""
        return self.history_manager.get_conversation_summary()
    
    def clear_conversation(self):
        """Clear the current conversation with backup."""
        self.history_manager.clear_conversation(create_backup=True)
        self.context_history.clear()
    
    def export_conversation(self, format: str = "json") -> str:
        """Export conversation in specified format."""
        return self.history_manager.export_conversation(format)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive conversation statistics."""
        stats = self.history_manager.get_statistics()
        
        # Add legacy fields for compatibility
        if "message_counts" in stats:
            stats["total_interactions"] = stats["message_counts"].get("conversation", 0) // 2
            stats["context_messages"] = stats["message_counts"]["total"]
        
        return stats
    
    # Session management integration
    
    def save_to_session_data(self) -> Dict[str, Any]:
        """
        Export data for session storage (compatible with existing session system).
        
        Returns:
            Dictionary compatible with existing session format
        """
        if not self.history_manager.current_conversation:
            return {"context_history": []}
        
        # Convert new format to old session format
        session_data = {
            "context_history": [],
            "conversation_id": self.history_manager.current_conversation.id,
            "conversation_metadata": self.history_manager.current_conversation.metadata
        }
        
        # Convert messages to old format for session compatibility
        for msg in self.history_manager.current_conversation.messages:
            if msg.is_conversation_message():  # Only include user/assistant messages in session
                session_data["context_history"].append({
                    "role": msg.role.value,
                    "content": msg.content,
                    "tokens": msg.tokens,
                    "timestamp": msg.timestamp.timestamp(),
                    "metadata": msg.metadata
                })
        
        return session_data
    
    def load_from_session_data(self, session_data: Dict[str, Any]):
        """
        Load data from existing session format.
        
        Args:
            session_data: Session data in old format
        """
        if not session_data or "context_history" not in session_data:
            return
        
        # Clear current conversation
        self.history_manager.clear_conversation(create_backup=False)
        
        # Load messages from session
        for msg_data in session_data["context_history"]:
            role = msg_data.get("role", "user")
            content = msg_data.get("content", "")
            metadata = msg_data.get("metadata", {})
            
            if role == "user":
                self.add_user_message(content, **metadata)
            elif role == "assistant":
                self.add_assistant_message(content, **metadata)
        
        console.print(f"[green]✓ Loaded {len(session_data['context_history'])} messages from session[/green]")
    
    def integrate_with_prompt_enhancer(self, prompt_enhancer):
        """
        Integrate with existing PromptEnhancer for seamless transition.
        
        Args:
            prompt_enhancer: Existing PromptEnhancer instance
        """
        # Migrate existing context history
        if hasattr(prompt_enhancer, 'context_history') and prompt_enhancer.context_history:
            console.print("[yellow]🔄 Migrating existing conversation history...[/yellow]")
            
            for msg in prompt_enhancer.context_history:
                try:
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')
                    metadata = msg.get('metadata', {})
                    
                    if role == 'user':
                        self.add_user_message(content, **metadata)
                    elif role == 'assistant':
                        self.add_assistant_message(content, **metadata)
                    elif role == 'system':
                        msg_type = metadata.get('type', 'system_prompt')
                        self.add_system_message(content, message_type=msg_type, **metadata)
                except Exception as e:
                    console.print(f"[yellow]⚠️  Could not migrate message: {e}[/yellow]")
            
            # Replace methods in prompt_enhancer
            prompt_enhancer.add_to_context_history = self.add_to_context_history
            prompt_enhancer.get_context_usage_percentage = self.get_context_usage_percentage
            prompt_enhancer.flush_context = self.flush_context
            
            console.print(f"[green]✓ Migrated {len(prompt_enhancer.context_history)} messages to new system[/green]")


def migrate_existing_session(session_manager, conversation_integration):
    """
    Migrate existing session to new conversation system.
    
    Args:
        session_manager: Existing SessionManager instance
        conversation_integration: ConversationIntegration instance
    """
    session_data = session_manager.load_session()
    if session_data and "context_history" in session_data:
        console.print("[blue]🔄 Migrating session to new conversation system...[/blue]")
        conversation_integration.load_from_session_data(session_data)
        return True
    return False
