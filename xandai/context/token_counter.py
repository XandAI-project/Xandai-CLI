"""
Token Counter

Accurate token counting for different models.
"""

import re
from typing import Optional


class TokenCounter:
    """
    Token Counter

    Provides token counting for text, supporting different models.
    Uses approximation when tiktoken is not available.
    """

    def __init__(self, model: str = "gpt-3.5-turbo"):
        """
        Initialize token counter

        Args:
            model: Model name for encoding
        """
        self.model = model
        self._encoding = None
        self._init_encoding()

    def _init_encoding(self):
        """Initialize tiktoken encoding if available"""
        try:
            import tiktoken

            try:
                self._encoding = tiktoken.encoding_for_model(self.model)
            except KeyError:
                # Fallback to cl100k_base for unknown models
                self._encoding = tiktoken.get_encoding("cl100k_base")
        except ImportError:
            # tiktoken not available, will use approximation
            self._encoding = None

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text

        Args:
            text: Text to count

        Returns:
            Token count
        """
        if self._encoding:
            return len(self._encoding.encode(text))
        else:
            return self._approximate_tokens(text)

    def count_messages_tokens(self, messages: list) -> int:
        """
        Count tokens in chat messages

        Args:
            messages: List of message dicts

        Returns:
            Total token count
        """
        total = 0

        for message in messages:
            # Message overhead (role, formatting, etc.)
            total += 4  # Approximate overhead per message

            # Role
            total += self.count_tokens(message.get("role", ""))

            # Content
            total += self.count_tokens(message.get("content", ""))

            # Name (if present)
            if "name" in message:
                total += self.count_tokens(message["name"])
                total += 1  # Name overhead

        total += 2  # Reply priming

        return total

    def _approximate_tokens(self, text: str) -> int:
        """
        Approximate token count

        Uses heuristics when tiktoken is unavailable.
        Generally: 1 token ≈ 4 characters in English

        Args:
            text: Text to count

        Returns:
            Approximate token count
        """
        # Split by whitespace
        words = text.split()

        # Count words
        word_count = len(words)

        # Count special characters (often separate tokens)
        special_chars = len(re.findall(r"[^\w\s]", text))

        # Approximate: words + half of special chars
        return word_count + (special_chars // 2)

    def estimate_completion_tokens(self, prompt: str, ratio: float = 0.5) -> int:
        """
        Estimate completion tokens based on prompt

        Args:
            prompt: Input prompt
            ratio: Completion/prompt ratio (default 0.5)

        Returns:
            Estimated completion tokens
        """
        prompt_tokens = self.count_tokens(prompt)
        return int(prompt_tokens * ratio)

    def fits_in_context(
        self, text: str, max_tokens: int, reserve_for_completion: int = 1000
    ) -> bool:
        """
        Check if text fits in context window

        Args:
            text: Text to check
            max_tokens: Maximum context tokens
            reserve_for_completion: Tokens to reserve for response

        Returns:
            True if fits, False otherwise
        """
        tokens = self.count_tokens(text)
        return tokens + reserve_for_completion <= max_tokens
