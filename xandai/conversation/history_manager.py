"""
Main history management system for XandAI CLI.
Provides clean APIs for conversation history, token budgeting, and summarization.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from rich.console import Console

from .conversation_history import (
    ConversationHistory, Message, MessageRole, MessageType, 
    ToolCall, ToolResult, ConversationSummary
)
from .token_budget_manager import TokenBudgetManager, TokenBudgetStrategy, ModelRegistry
from .conversation_summarizer import ConversationSummarizer, SummarizationError


console = Console()


class HistoryManagerError(Exception):
    """Exception raised by HistoryManager operations."""
    pass


class HistoryManager:
    """
    Main interface for robust conversation history management.
    
    Provides:
    - Persistent conversation history storage
    - Token budget management with model-specific limits
    - Auto-summarization of old conversations
    - Support for tool/function call messages
    - Clean APIs for integration
    """
    
    def __init__(
        self, 
        storage_dir: Optional[Union[str, Path]] = None,
        api=None,
        default_strategy: Optional[TokenBudgetStrategy] = None
    ):
        """
        Initialize the history manager.
        
        Args:
            storage_dir: Directory for storing conversation history
            api: OLLAMA API instance for summarization
            default_strategy: Default token budget strategy
        """
        # Setup storage
        if storage_dir is None:
            # Use the existing sessions directory
            storage_dir = Path(__file__).parent.parent.parent / "sessions"
        
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True, parents=True)
        
        # Initialize components
        self.api = api
        self.default_strategy = default_strategy or TokenBudgetStrategy()
        
        # Current state
        self.current_conversation: Optional[ConversationHistory] = None
        self.current_token_manager: Optional[TokenBudgetManager] = None
        self.current_summarizer: Optional[ConversationSummarizer] = None
        self.current_model: Optional[str] = None
        
        # Load or create conversation
        self._load_current_conversation()
    
    def _load_current_conversation(self):
        """Load the current conversation from storage."""
        history_file = self.storage_dir / "conversation_history.json"
        
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.current_conversation = ConversationHistory.from_dict(data)
                console.print(f"[dim]Loaded conversation history with {len(self.current_conversation.messages)} messages[/dim]")
            except Exception as e:
                console.print(f"[yellow]⚠️  Could not load conversation history: {e}[/yellow]")
                self._create_new_conversation()
        else:
            self._create_new_conversation()
    
    def _create_new_conversation(self):
        """Create a new conversation."""
        self.current_conversation = ConversationHistory(
            id=f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            created_at=datetime.now(),
            last_updated=datetime.now()
        )
        console.print("[dim]Created new conversation history[/dim]")
    
    def _save_current_conversation(self):
        """Save the current conversation to storage."""
        if not self.current_conversation:
            return
        
        history_file = self.storage_dir / "conversation_history.json"
        backup_file = self.storage_dir / f"conversation_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            # Create backup of existing file
            if history_file.exists():
                # On Windows, need to handle existing target files
                if backup_file.exists():
                    backup_file.unlink()
                history_file.rename(backup_file)
            
            # Save current conversation
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_conversation.to_dict(), f, ensure_ascii=False, indent=2)
            
            # Clean up old backups (keep only last 10)
            backups = sorted(self.storage_dir.glob("conversation_backup_*.json"))
            for old_backup in backups[:-10]:
                old_backup.unlink()
                
        except Exception as e:
            console.print(f"[red]Error saving conversation: {e}[/red]")
            # Restore backup if save failed
            if backup_file.exists() and not history_file.exists():
                backup_file.rename(history_file)
    
    def set_model(self, model_name: str):
        """
        Set the current model and update token management.
        
        Args:
            model_name: Name of the model to use
        """
        if model_name == self.current_model and self.current_token_manager:
            return
        
        self.current_model = model_name
        self.current_token_manager = TokenBudgetManager(model_name, self.default_strategy)
        
        if self.api:
            self.current_summarizer = ConversationSummarizer(self.api, self.current_token_manager)
        
        console.print(f"[dim]History manager configured for model: {model_name}[/dim]")
    
    # Message Management APIs
    
    def add_user_message(self, content: str, **kwargs) -> Message:
        """Add a user message to the conversation."""
        if not self.current_conversation:
            self._create_new_conversation()
        
        # Calculate tokens
        tokens = self.current_token_manager.calculate_tokens(content) if self.current_token_manager else 0
        
        message = self.current_conversation.add_user_message(
            content=content,
            tokens=tokens,
            model_used=self.current_model,
            **kwargs
        )
        
        self._save_current_conversation()
        return message
    
    def add_assistant_message(self, content: str, tool_calls: Optional[List[ToolCall]] = None, **kwargs) -> Message:
        """Add an assistant message to the conversation."""
        if not self.current_conversation:
            self._create_new_conversation()
        
        # Calculate tokens
        tokens = self.current_token_manager.calculate_tokens(content) if self.current_token_manager else 0
        if tool_calls:
            for tc in tool_calls:
                tokens += self.current_token_manager.calculate_tokens(str(tc.arguments)) if self.current_token_manager else 0
        
        if tool_calls:
            message = self.current_conversation.add_tool_call(
                content=content,
                tool_calls=tool_calls,
                tokens=tokens,
                model_used=self.current_model,
                **kwargs
            )
        else:
            message = self.current_conversation.add_assistant_message(
                content=content,
                tokens=tokens,
                model_used=self.current_model,
                **kwargs
            )
        
        self._save_current_conversation()
        return message
    
    def add_tool_results(self, tool_results: List[ToolResult], **kwargs) -> Message:
        """Add tool results to the conversation."""
        if not self.current_conversation:
            self._create_new_conversation()
        
        # Calculate tokens
        tokens = sum(
            self.current_token_manager.calculate_tokens(tr.content) if self.current_token_manager else 0
            for tr in tool_results
        )
        
        message = self.current_conversation.add_tool_result(
            tool_results=tool_results,
            tokens=tokens,
            **kwargs
        )
        
        self._save_current_conversation()
        return message
    
    def add_system_message(self, content: str, message_type: MessageType = MessageType.SYSTEM_PROMPT, **kwargs) -> Message:
        """Add a system message to the conversation."""
        if not self.current_conversation:
            self._create_new_conversation()
        
        tokens = self.current_token_manager.calculate_tokens(content) if self.current_token_manager else 0
        
        message = self.current_conversation.add_system_message(
            content=content,
            message_type=message_type,
            tokens=tokens,
            **kwargs
        )
        
        self._save_current_conversation()
        return message
    
    # Context Management APIs
    
    def get_context_for_model(self, max_tokens: Optional[int] = None) -> List[Message]:
        """
        Get optimized message context for the current model.
        
        Args:
            max_tokens: Override max tokens (uses model default if None)
            
        Returns:
            List of messages that fit within token budget
        """
        if not self.current_conversation or not self.current_token_manager:
            return []
        
        messages = self.current_conversation.messages
        
        if max_tokens:
            # Create temporary token manager with custom limit
            strategy = TokenBudgetStrategy()
            strategy.target_utilization = max_tokens / self.current_token_manager.model_info.context_length
            temp_manager = TokenBudgetManager(self.current_model, strategy)
            optimized_messages, _ = temp_manager.optimize_message_list(messages)
        else:
            optimized_messages, _ = self.current_token_manager.optimize_message_list(messages)
        
        return optimized_messages
    
    def get_context_status(self) -> Dict[str, Any]:
        """
        Get detailed context status and recommendations.
        
        Returns:
            Dictionary with context analysis and recommendations
        """
        if not self.current_conversation or not self.current_token_manager:
            return {"error": "No conversation or token manager"}
        
        messages = self.current_conversation.messages
        analysis = self.current_token_manager.assess_context_fit(messages)
        
        # Add conversation-specific info
        analysis["conversation_info"] = {
            "id": self.current_conversation.id,
            "created_at": self.current_conversation.created_at.isoformat(),
            "total_messages": len(messages),
            "conversation_messages": len(self.current_conversation.get_conversation_messages()),
            "system_messages": len([m for m in messages if m.is_system_message()]),
            "tool_messages": len([m for m in messages if m.is_tool_message()]),
            "summaries": len(self.current_conversation.summaries)
        }
        
        return analysis
    
    def force_optimization(self) -> Dict[str, Any]:
        """
        Force optimization of the conversation history.
        
        Returns:
            Optimization report
        """
        if not self.current_conversation or not self.current_token_manager:
            return {"error": "No conversation or token manager"}
        
        messages = self.current_conversation.messages
        optimized_messages, report = self.current_token_manager.optimize_message_list(messages)
        
        # Update conversation with optimized messages
        if len(optimized_messages) < len(messages):
            self.current_conversation.messages = optimized_messages
            self.current_conversation._update_statistics()
            self._save_current_conversation()
            
            console.print(f"[green]✓ Optimized conversation: {report['tokens_saved']} tokens saved[/green]")
        
        return report
    
    # Summarization APIs
    
    def auto_summarize(self, force: bool = False) -> Optional[Dict[str, Any]]:
        """
        Automatically summarize old conversations if needed.
        
        Args:
            force: Force summarization even if not needed
            
        Returns:
            Summarization report or None if no summarization performed
        """
        if not (self.current_conversation and self.current_summarizer and self.current_token_manager):
            return None
        
        # Get summarization candidates
        candidates = self.current_token_manager.suggest_summarization_candidates(self.current_conversation)
        
        if not candidates and not force:
            return None
        
        try:
            summaries_created = 0
            total_tokens_saved = 0
            
            for start_idx, end_idx in candidates:
                messages_to_summarize = self.current_conversation.messages[start_idx:end_idx]
                
                if not self.current_summarizer.can_summarize(messages_to_summarize):
                    continue
                
                # Create summary
                summary = self.current_summarizer.summarize_conversation_sync(
                    messages_to_summarize,
                    self.current_model,
                    context=f"XandAI CLI session from {messages_to_summarize[0].timestamp}"
                )
                
                # Add summary to conversation
                self.current_conversation.add_summary(summary)
                
                # Remove original messages (replace with summary reference)
                summary_message = self.current_conversation.add_system_message(
                    content=f"[CONVERSATION SUMMARY] {summary.summary_content}",
                    message_type=MessageType.CONTEXT_SUMMARY,
                    metadata={
                        "summary_id": summary.id,
                        "original_message_count": summary.original_message_count,
                        "compression_ratio": summary.metadata.get("compression_ratio", 0)
                    }
                )
                
                # Remove original messages
                self.current_conversation.messages = (
                    self.current_conversation.messages[:start_idx] +
                    [summary_message] +
                    self.current_conversation.messages[end_idx:]
                )
                
                summaries_created += 1
                total_tokens_saved += summary.original_token_count - summary.summary_tokens
            
            if summaries_created > 0:
                self.current_conversation._update_statistics()
                self._save_current_conversation()
                
                report = {
                    "summaries_created": summaries_created,
                    "tokens_saved": total_tokens_saved,
                    "messages_summarized": sum(end - start for start, end in candidates),
                    "timestamp": datetime.now().isoformat()
                }
                
                console.print(f"[green]✓ Auto-summarization complete: {summaries_created} summaries, {total_tokens_saved} tokens saved[/green]")
                return report
            
        except SummarizationError as e:
            console.print(f"[yellow]⚠️  Auto-summarization failed: {e}[/yellow]")
            return {"error": str(e)}
        
        return None
    
    def get_conversation_summary(self) -> str:
        """Get a human-readable summary of the current conversation."""
        if not self.current_conversation:
            return "No active conversation"
        
        messages = self.current_conversation.messages
        conversation_messages = self.current_conversation.get_conversation_messages()
        
        summary_parts = [
            f"**Conversation {self.current_conversation.id}**",
            f"Created: {self.current_conversation.created_at.strftime('%Y-%m-%d %H:%M')}",
            f"Last updated: {self.current_conversation.last_updated.strftime('%Y-%m-%d %H:%M')}",
            f"Total messages: {len(messages)}",
            f"Conversation messages: {len(conversation_messages)}",
            f"System messages: {len([m for m in messages if m.is_system_message()])}",
            f"Tool messages: {len([m for m in messages if m.is_tool_message()])}",
            f"Summaries: {len(self.current_conversation.summaries)}",
            f"Total tokens: {self.current_conversation.total_tokens:,}",
        ]
        
        if self.current_token_manager:
            status = self.current_token_manager.get_context_status(messages)
            summary_parts.append(f"Context status: {status}")
        
        return "\n".join(summary_parts)
    
    # Utility APIs
    
    def clear_conversation(self, create_backup: bool = True):
        """
        Clear the current conversation.
        
        Args:
            create_backup: Whether to create a backup before clearing
        """
        if self.current_conversation and create_backup:
            # Save backup
            backup_file = self.storage_dir / f"conversation_cleared_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_conversation.to_dict(), f, ensure_ascii=False, indent=2)
            console.print(f"[dim]Conversation backed up to: {backup_file.name}[/dim]")
        
        self._create_new_conversation()
        self._save_current_conversation()
        console.print("[green]✓ Conversation cleared[/green]")
    
    def export_conversation(self, format: str = "json", include_summaries: bool = True) -> str:
        """
        Export conversation in various formats.
        
        Args:
            format: Export format ('json', 'markdown', 'txt')
            include_summaries: Whether to include summaries
            
        Returns:
            Exported conversation as string
        """
        if not self.current_conversation:
            return ""
        
        if format == "json":
            data = self.current_conversation.to_dict()
            if not include_summaries:
                data.pop("summaries", None)
            return json.dumps(data, ensure_ascii=False, indent=2)
        
        elif format == "markdown":
            lines = [f"# Conversation {self.current_conversation.id}"]
            lines.append(f"*Created: {self.current_conversation.created_at}*")
            lines.append("")
            
            for msg in self.current_conversation.messages:
                role_emoji = {"user": "🧑", "assistant": "🤖", "system": "⚙️", "tool": "🔧"}.get(msg.role.value, "❓")
                lines.append(f"## {role_emoji} {msg.role.value.title()} ({msg.timestamp.strftime('%H:%M')})")
                lines.append(msg.content)
                lines.append("")
            
            return "\n".join(lines)
        
        elif format == "txt":
            lines = []
            for msg in self.current_conversation.messages:
                timestamp = msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                lines.append(f"[{timestamp}] {msg.role.value.upper()}: {msg.content}")
                lines.append("")
            
            return "\n".join(lines)
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive conversation statistics."""
        if not self.current_conversation:
            return {}
        
        messages = self.current_conversation.messages
        conversation_messages = self.current_conversation.get_conversation_messages()
        
        stats = {
            "conversation_id": self.current_conversation.id,
            "created_at": self.current_conversation.created_at.isoformat(),
            "last_updated": self.current_conversation.last_updated.isoformat(),
            "duration_hours": (self.current_conversation.last_updated - self.current_conversation.created_at).total_seconds() / 3600,
            "message_counts": {
                "total": len(messages),
                "conversation": len(conversation_messages),
                "system": len([m for m in messages if m.is_system_message()]),
                "tool": len([m for m in messages if m.is_tool_message()]),
                "user": len([m for m in messages if m.role == MessageRole.USER]),
                "assistant": len([m for m in messages if m.role == MessageRole.ASSISTANT])
            },
            "token_counts": {
                "total": self.current_conversation.total_tokens,
                "conversation_only": sum(m.tokens for m in conversation_messages)
            },
            "summaries": len(self.current_conversation.summaries),
            "model_info": None
        }
        
        if self.current_token_manager:
            stats["model_info"] = {
                "name": self.current_token_manager.model_info.name,
                "family": self.current_token_manager.model_info.family.value,
                "context_length": self.current_token_manager.model_info.context_length,
                "available_context": self.current_token_manager.model_info.get_available_context()
            }
        
        if self.current_conversation.summaries:
            summary_stats = {
                "total_summaries": len(self.current_conversation.summaries),
                "total_summarized_messages": sum(s.original_message_count for s in self.current_conversation.summaries),
                "total_tokens_saved": sum(s.original_token_count - s.summary_tokens for s in self.current_conversation.summaries)
            }
            stats["summarization"] = summary_stats
        
        return stats
