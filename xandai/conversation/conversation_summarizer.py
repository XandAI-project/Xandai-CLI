"""
Conversation summarization system for XandAI CLI.
Automatically compresses old conversation history into compact summaries.
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import uuid
import json
import re
from .conversation_history import (
    Message, MessageRole, MessageType, ConversationHistory, ConversationSummary
)
from .token_budget_manager import TokenBudgetManager


class SummarizationError(Exception):
    """Exception raised during summarization process."""
    pass


class ConversationSummarizer:
    """
    Intelligent conversation summarization using the LLM itself.
    """
    
    def __init__(self, api, token_budget_manager: TokenBudgetManager):
        self.api = api
        self.token_manager = token_budget_manager
        
        # Summarization templates
        self.summary_prompts = {
            "conversation": self._get_conversation_summary_prompt(),
            "tool_usage": self._get_tool_usage_summary_prompt(),
            "code_session": self._get_code_session_summary_prompt()
        }
    
    def _get_conversation_summary_prompt(self) -> str:
        """Get prompt template for general conversation summarization."""
        return """You are tasked with creating a concise but comprehensive summary of a conversation between a user and an AI assistant. 

The conversation involves a user working with XandAI CLI, which helps with coding tasks, file operations, and project management.

**Instructions:**
1. Summarize the key topics discussed, decisions made, and outcomes achieved
2. Preserve important technical details, file names, commands, and configurations
3. Note any ongoing context that might be relevant for future conversations
4. Keep the summary concise but informative (aim for 200-400 tokens)
5. Use clear, structured format with bullet points where appropriate

**Conversation to Summarize:**
{conversation_text}

**Summary:**"""
    
    def _get_tool_usage_summary_prompt(self) -> str:
        """Get prompt template for tool usage summarization."""
        return """Summarize this conversation session that involved significant tool usage and file operations.

Focus on:
- Files created, modified, or read
- Commands executed
- Project structure changes
- Technical configurations
- Any errors encountered and solutions

**Session to Summarize:**
{conversation_text}

**Technical Summary:**"""
    
    def _get_code_session_summary_prompt(self) -> str:
        """Get prompt template for coding session summarization."""
        return """Summarize this coding session, focusing on the development work accomplished.

Highlight:
- Programming languages and frameworks used
- Features implemented or bugs fixed
- Architecture decisions made
- Testing or debugging activities
- Next steps or TODOs mentioned

**Coding Session:**
{conversation_text}

**Development Summary:**"""
    
    def can_summarize(self, messages: List[Message], min_age_hours: int = 1) -> bool:
        """
        Check if messages are eligible for summarization.
        
        Args:
            messages: List of messages to check
            min_age_hours: Minimum age in hours before summarizing
            
        Returns:
            True if messages can be summarized
        """
        if not messages:
            return False
        
        # Check if messages are old enough
        cutoff_time = datetime.now() - timedelta(hours=min_age_hours)
        if any(msg.timestamp > cutoff_time for msg in messages):
            return False
        
        # Must have meaningful conversation content
        conversation_messages = [
            msg for msg in messages 
            if msg.is_conversation_message() and len(msg.content.strip()) > 10
        ]
        
        return len(conversation_messages) >= 3  # At least 3 meaningful messages
    
    def _classify_conversation_type(self, messages: List[Message]) -> str:
        """Classify the type of conversation to choose appropriate summarization."""
        tool_messages = sum(1 for msg in messages if msg.is_tool_message())
        total_messages = len(messages)
        
        # Count code-related content
        code_indicators = 0
        for msg in messages:
            content_lower = msg.content.lower()
            if any(indicator in content_lower for indicator in [
                'function', 'class', 'import', 'def ', 'const ', 'var ', 
                'let ', 'if (', 'for (', 'while (', '<code', 'git ', 'npm ', 'pip '
            ]):
                code_indicators += 1
        
        # Classify based on content
        if tool_messages / max(total_messages, 1) > 0.3:
            return "tool_usage"
        elif code_indicators / max(total_messages, 1) > 0.4:
            return "code_session"
        else:
            return "conversation"
    
    def _prepare_conversation_text(self, messages: List[Message]) -> str:
        """Prepare conversation text for summarization."""
        formatted_messages = []
        
        for msg in messages:
            timestamp_str = msg.timestamp.strftime("%Y-%m-%d %H:%M")
            
            if msg.role == MessageRole.USER:
                role_prefix = "USER"
            elif msg.role == MessageRole.ASSISTANT:
                role_prefix = "ASSISTANT"
            elif msg.role == MessageRole.SYSTEM:
                role_prefix = "SYSTEM"
            elif msg.role == MessageRole.TOOL:
                role_prefix = "TOOL"
            else:
                role_prefix = msg.role.value.upper()
            
            content = msg.content.strip()
            
            # Add tool call information if present
            if msg.tool_calls:
                tool_info = []
                for tc in msg.tool_calls:
                    tool_info.append(f"Tool: {tc.name}({tc.arguments})")
                content += f"\n[Tools used: {'; '.join(tool_info)}]"
            
            # Add tool results if present
            if msg.tool_results:
                result_info = []
                for tr in msg.tool_results:
                    status = "✓" if tr.success else "✗"
                    result_info.append(f"{status} {tr.content[:100]}...")
                content += f"\n[Results: {'; '.join(result_info)}]"
            
            # Truncate very long messages but preserve structure
            if len(content) > 1000:
                lines = content.split('\n')
                if len(lines) > 20:
                    content = '\n'.join(lines[:10]) + "\n[... truncated ...]\n" + '\n'.join(lines[-5:])
                else:
                    content = content[:800] + "\n[... truncated ...]"
            
            formatted_messages.append(f"[{timestamp_str}] {role_prefix}: {content}")
        
        return "\n\n".join(formatted_messages)
    
    async def summarize_conversation(
        self, 
        messages: List[Message],
        model_name: str,
        context: Optional[str] = None
    ) -> ConversationSummary:
        """
        Summarize a conversation using the LLM.
        
        Args:
            messages: Messages to summarize
            model_name: Model to use for summarization
            context: Additional context about the conversation
            
        Returns:
            ConversationSummary object
            
        Raises:
            SummarizationError: If summarization fails
        """
        if not messages:
            raise SummarizationError("No messages to summarize")
        
        if not self.can_summarize(messages):
            raise SummarizationError("Messages are not eligible for summarization")
        
        try:
            # Classify conversation type and get appropriate prompt
            conversation_type = self._classify_conversation_type(messages)
            prompt_template = self.summary_prompts[conversation_type]
            
            # Prepare conversation text
            conversation_text = self._prepare_conversation_text(messages)
            
            # Add context if provided
            if context:
                conversation_text = f"Context: {context}\n\n{conversation_text}"
            
            # Generate summary
            summary_prompt = prompt_template.format(conversation_text=conversation_text)
            
            summary_content = ""
            try:
                for chunk in self.api.generate(model_name, summary_prompt, stream=True):
                    summary_content += chunk
            except Exception as e:
                raise SummarizationError(f"Failed to generate summary: {e}")
            
            if not summary_content.strip():
                raise SummarizationError("Empty summary generated")
            
            # Calculate token counts
            original_tokens = sum(self.token_manager.calculate_tokens(msg.content) for msg in messages)
            summary_tokens = self.token_manager.calculate_tokens(summary_content)
            
            # Create summary object
            time_range_start = min(msg.timestamp for msg in messages)
            time_range_end = max(msg.timestamp for msg in messages)
            
            summary = ConversationSummary(
                id=str(uuid.uuid4()),
                original_message_count=len(messages),
                original_token_count=original_tokens,
                summary_content=summary_content.strip(),
                summary_tokens=summary_tokens,
                time_range_start=time_range_start,
                time_range_end=time_range_end,
                created_at=datetime.now(),
                metadata={
                    "conversation_type": conversation_type,
                    "model_used": model_name,
                    "compression_ratio": summary_tokens / max(original_tokens, 1),
                    "context_provided": context is not None
                }
            )
            
            return summary
            
        except Exception as e:
            raise SummarizationError(f"Summarization failed: {e}")
    
    def summarize_conversation_sync(
        self,
        messages: List[Message],
        model_name: str,
        context: Optional[str] = None
    ) -> ConversationSummary:
        """
        Synchronous version of summarize_conversation.
        """
        if not messages:
            raise SummarizationError("No messages to summarize")
        
        if not self.can_summarize(messages):
            raise SummarizationError("Messages are not eligible for summarization")
        
        try:
            # Classify conversation type and get appropriate prompt
            conversation_type = self._classify_conversation_type(messages)
            prompt_template = self.summary_prompts[conversation_type]
            
            # Prepare conversation text
            conversation_text = self._prepare_conversation_text(messages)
            
            # Add context if provided
            if context:
                conversation_text = f"Context: {context}\n\n{conversation_text}"
            
            # Generate summary
            summary_prompt = prompt_template.format(conversation_text=conversation_text)
            
            summary_content = ""
            for chunk in self.api.generate(model_name, summary_prompt, stream=True):
                summary_content += chunk
            
            if not summary_content.strip():
                raise SummarizationError("Empty summary generated")
            
            # Calculate token counts
            original_tokens = sum(self.token_manager.calculate_tokens(msg.content) for msg in messages)
            summary_tokens = self.token_manager.calculate_tokens(summary_content)
            
            # Create summary object
            time_range_start = min(msg.timestamp for msg in messages)
            time_range_end = max(msg.timestamp for msg in messages)
            
            summary = ConversationSummary(
                id=str(uuid.uuid4()),
                original_message_count=len(messages),
                original_token_count=original_tokens,
                summary_content=summary_content.strip(),
                summary_tokens=summary_tokens,
                time_range_start=time_range_start,
                time_range_end=time_range_end,
                created_at=datetime.now(),
                metadata={
                    "conversation_type": conversation_type,
                    "model_used": model_name,
                    "compression_ratio": summary_tokens / max(original_tokens, 1),
                    "context_provided": context is not None
                }
            )
            
            return summary
            
        except Exception as e:
            raise SummarizationError(f"Summarization failed: {e}")
    
    def create_combined_summary(self, summaries: List[ConversationSummary]) -> str:
        """
        Create a combined summary from multiple individual summaries.
        
        Args:
            summaries: List of summaries to combine
            
        Returns:
            Combined summary text
        """
        if not summaries:
            return ""
        
        if len(summaries) == 1:
            return summaries[0].summary_content
        
        # Sort summaries by time
        sorted_summaries = sorted(summaries, key=lambda s: s.time_range_start)
        
        combined_parts = []
        for i, summary in enumerate(sorted_summaries):
            time_info = summary.time_range_start.strftime("%Y-%m-%d %H:%M")
            conv_type = summary.metadata.get("conversation_type", "conversation")
            
            combined_parts.append(
                f"Session {i+1} ({time_info}, {conv_type}):\n{summary.summary_content}"
            )
        
        return "\n\n".join(combined_parts)
    
    def get_summarization_stats(self, summaries: List[ConversationSummary]) -> Dict[str, Any]:
        """
        Get statistics about summarization efficiency.
        
        Args:
            summaries: List of summaries to analyze
            
        Returns:
            Dictionary with statistics
        """
        if not summaries:
            return {}
        
        total_original_messages = sum(s.original_message_count for s in summaries)
        total_original_tokens = sum(s.original_token_count for s in summaries)
        total_summary_tokens = sum(s.summary_tokens for s in summaries)
        
        compression_ratios = [s.summary_tokens / max(s.original_token_count, 1) for s in summaries]
        avg_compression = sum(compression_ratios) / len(compression_ratios)
        
        return {
            "total_summaries": len(summaries),
            "total_original_messages": total_original_messages,
            "total_original_tokens": total_original_tokens,
            "total_summary_tokens": total_summary_tokens,
            "tokens_saved": total_original_tokens - total_summary_tokens,
            "average_compression_ratio": avg_compression,
            "best_compression_ratio": min(compression_ratios),
            "worst_compression_ratio": max(compression_ratios),
            "total_time_span": (
                max(s.time_range_end for s in summaries) - 
                min(s.time_range_start for s in summaries)
            ).days
        }
