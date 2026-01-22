"""
Context Manager

Smart context window management with multiple strategies.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from xandai.context.token_counter import TokenCounter


class ContextStrategy(Enum):
    """Context management strategies"""

    SLIDING = "sliding"  # Keep recent messages (FIFO)
    SUMMARIZE = "summarize"  # Summarize old messages
    PRIORITY = "priority"  # Keep important messages
    COMPRESS = "compress"  # Compress repetitive content


@dataclass
class ContextWindow:
    """Context window configuration"""

    max_tokens: int = 4096
    reserve_tokens: int = 1000  # Reserve for completion
    strategy: ContextStrategy = ContextStrategy.SLIDING
    system_message: Optional[str] = None


class ContextManager:
    """
    Context Window Manager

    Manages conversation context to fit within token limits.
    """

    def __init__(
        self,
        max_tokens: int = 4096,
        reserve_tokens: int = 1000,
        strategy: ContextStrategy = ContextStrategy.SLIDING,
        model: str = "gpt-3.5-turbo",
    ):
        """
        Initialize context manager

        Args:
            max_tokens: Maximum context window size
            reserve_tokens: Tokens to reserve for completion
            strategy: Context management strategy
            model: Model name for token counting
        """
        self.window = ContextWindow(
            max_tokens=max_tokens, reserve_tokens=reserve_tokens, strategy=strategy
        )
        self.token_counter = TokenCounter(model=model)

    def fit_messages(
        self, messages: List[Dict[str, Any]], system_message: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fit messages within context window

        Args:
            messages: List of chat messages
            system_message: Optional system message

        Returns:
            Fitted messages
        """
        # Calculate available tokens
        available_tokens = self.window.max_tokens - self.window.reserve_tokens

        # Handle system message
        result_messages = []
        if system_message:
            sys_msg = {"role": "system", "content": system_message}
            result_messages.append(sys_msg)
            available_tokens -= self.token_counter.count_messages_tokens([sys_msg])

        # Apply strategy
        if self.window.strategy == ContextStrategy.SLIDING:
            fitted = self._sliding_window(messages, available_tokens)
        elif self.window.strategy == ContextStrategy.PRIORITY:
            fitted = self._priority_window(messages, available_tokens)
        elif self.window.strategy == ContextStrategy.COMPRESS:
            fitted = self._compress_window(messages, available_tokens)
        else:
            fitted = self._sliding_window(messages, available_tokens)

        result_messages.extend(fitted)
        return result_messages

    def _sliding_window(
        self, messages: List[Dict[str, Any]], available_tokens: int
    ) -> List[Dict[str, Any]]:
        """
        Sliding window: Keep most recent messages

        Args:
            messages: All messages
            available_tokens: Available token budget

        Returns:
            Recent messages that fit
        """
        result = []
        current_tokens = 0

        # Start from most recent
        for message in reversed(messages):
            msg_tokens = self.token_counter.count_messages_tokens([message])

            if current_tokens + msg_tokens > available_tokens:
                break

            result.insert(0, message)
            current_tokens += msg_tokens

        return result

    def _priority_window(
        self, messages: List[Dict[str, Any]], available_tokens: int
    ) -> List[Dict[str, Any]]:
        """
        Priority window: Keep important messages

        Args:
            messages: All messages
            available_tokens: Available token budget

        Returns:
            Important messages that fit
        """
        # Score messages by importance
        scored_messages = []
        for i, msg in enumerate(messages):
            score = self._calculate_message_priority(msg, i, len(messages))
            scored_messages.append((score, msg))

        # Sort by priority (high to low)
        scored_messages.sort(reverse=True, key=lambda x: x[0])

        # Select messages that fit
        result = []
        current_tokens = 0

        for score, message in scored_messages:
            msg_tokens = self.token_counter.count_messages_tokens([message])

            if current_tokens + msg_tokens > available_tokens:
                continue

            result.append(message)
            current_tokens += msg_tokens

        # Sort back to original order
        result.sort(key=lambda x: messages.index(x))

        return result

    def _compress_window(
        self, messages: List[Dict[str, Any]], available_tokens: int
    ) -> List[Dict[str, Any]]:
        """
        Compress window: Compress repetitive content

        Args:
            messages: All messages
            available_tokens: Available token budget

        Returns:
            Compressed messages
        """
        # For now, use sliding window
        # TODO: Implement compression algorithm
        return self._sliding_window(messages, available_tokens)

    def _calculate_message_priority(self, message: Dict[str, Any], index: int, total: int) -> float:
        """
        Calculate message priority score

        Args:
            message: Message to score
            index: Message index
            total: Total messages

        Returns:
            Priority score (higher = more important)
        """
        score = 0.0

        # Recent messages are more important
        recency_score = (index / total) * 0.4
        score += recency_score

        # User messages slightly more important
        if message.get("role") == "user":
            score += 0.1

        # Longer messages might be more important
        content_length = len(message.get("content", ""))
        if content_length > 100:
            score += 0.2

        # Code blocks are important
        if "```" in message.get("content", ""):
            score += 0.3

        return score

    def get_usage_stats(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get context window usage statistics

        Args:
            messages: Current messages

        Returns:
            Usage statistics
        """
        total_tokens = self.token_counter.count_messages_tokens(messages)
        available = self.window.max_tokens - self.window.reserve_tokens
        usage_percent = (total_tokens / available * 100) if available > 0 else 0

        return {
            "total_tokens": total_tokens,
            "max_tokens": self.window.max_tokens,
            "available_tokens": available,
            "reserve_tokens": self.window.reserve_tokens,
            "usage_percent": usage_percent,
            "messages_count": len(messages),
            "strategy": self.window.strategy.value,
            "fits": total_tokens <= available,
        }

    def should_truncate(self, messages: List[Dict[str, Any]]) -> bool:
        """
        Check if messages should be truncated

        Args:
            messages: Messages to check

        Returns:
            True if truncation needed
        """
        stats = self.get_usage_stats(messages)
        return not stats["fits"]

    def get_truncation_warning(self, messages: List[Dict[str, Any]]) -> Optional[str]:
        """
        Get warning message if truncation is needed

        Args:
            messages: Messages to check

        Returns:
            Warning message or None
        """
        stats = self.get_usage_stats(messages)

        if stats["usage_percent"] > 90:
            return (
                f"⚠ Context window quase cheio: {stats['usage_percent']:.1f}% "
                f"({stats['total_tokens']}/{stats['available_tokens']} tokens). "
                f"Considere iniciar uma nova sessão."
            )
        elif stats["usage_percent"] > 75:
            return (
                f"ℹ Context window: {stats['usage_percent']:.1f}% "
                f"({stats['total_tokens']}/{stats['available_tokens']} tokens)"
            )

        return None
