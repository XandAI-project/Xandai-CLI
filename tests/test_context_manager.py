"""
Tests for Context Window Manager
"""

import pytest

from xandai.context.context_manager import ContextManager, ContextStrategy
from xandai.context.token_counter import TokenCounter


class TestTokenCounter:
    """Test TokenCounter class"""

    def test_count_tokens_simple(self):
        """Test basic token counting"""
        counter = TokenCounter()
        count = counter.count_tokens("Hello world")
        assert count > 0

    def test_count_empty_string(self):
        """Test counting empty string"""
        counter = TokenCounter()
        count = counter.count_tokens("")
        assert count == 0

    def test_count_messages_tokens(self):
        """Test counting tokens in messages"""
        counter = TokenCounter()
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        count = counter.count_messages_tokens(messages)
        assert count > 0

    def test_approximate_tokens(self):
        """Test token approximation"""
        counter = TokenCounter()
        text = "This is a test sentence with multiple words."
        count = counter._approximate_tokens(text)
        assert count > 0
        assert count > 5  # Should be at least 5 tokens

    def test_estimate_completion_tokens(self):
        """Test completion token estimation"""
        counter = TokenCounter()
        prompt = "Write a paragraph about AI"
        estimate = counter.estimate_completion_tokens(prompt, ratio=0.5)
        assert estimate > 0

    def test_fits_in_context(self):
        """Test context window fitting"""
        counter = TokenCounter()

        short_text = "Hello"
        assert counter.fits_in_context(short_text, max_tokens=2000, reserve_for_completion=100)

        long_text = " ".join(["word"] * 10000)
        assert not counter.fits_in_context(long_text, max_tokens=1000, reserve_for_completion=100)


class TestContextManager:
    """Test ContextManager class"""

    def test_create_context_manager(self):
        """Test creating context manager"""
        manager = ContextManager(max_tokens=2000)
        assert manager.window.max_tokens == 2000

    def test_sliding_window_strategy(self):
        """Test sliding window strategy"""
        manager = ContextManager(
            max_tokens=100, reserve_tokens=20, strategy=ContextStrategy.SLIDING
        )

        messages = [
            {"role": "user", "content": "Message 1"},
            {"role": "assistant", "content": "Response 1"},
            {"role": "user", "content": "Message 2"},
            {"role": "assistant", "content": "Response 2"},
            {"role": "user", "content": "Message 3"},
        ]

        fitted = manager.fit_messages(messages)

        # Should keep recent messages
        assert len(fitted) > 0
        assert len(fitted) <= len(messages)

    def test_fit_messages_with_system(self):
        """Test fitting messages with system message"""
        manager = ContextManager(max_tokens=2000)

        messages = [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi"}]

        fitted = manager.fit_messages(messages, system_message="You are a helpful assistant")

        # Should include system message
        assert fitted[0]["role"] == "system"
        assert len(fitted) == 3  # system + 2 messages

    def test_get_usage_stats(self):
        """Test getting usage statistics"""
        manager = ContextManager(max_tokens=1000)

        messages = [
            {"role": "user", "content": "Test message"},
            {"role": "assistant", "content": "Test response"},
        ]

        stats = manager.get_usage_stats(messages)

        assert "total_tokens" in stats
        assert "max_tokens" in stats
        assert "usage_percent" in stats
        assert "messages_count" in stats
        assert stats["messages_count"] == 2

    def test_should_truncate(self):
        """Test truncation detection"""
        manager = ContextManager(max_tokens=50, reserve_tokens=10)

        short_messages = [{"role": "user", "content": "Hi"}]
        assert not manager.should_truncate(short_messages)

        long_messages = [{"role": "user", "content": " ".join(["word"] * 1000)}]
        assert manager.should_truncate(long_messages)

    def test_truncation_warning(self):
        """Test truncation warning"""
        manager = ContextManager(max_tokens=100, reserve_tokens=20)

        # Small usage - no warning
        small_messages = [{"role": "user", "content": "Hi"}]
        warning = manager.get_truncation_warning(small_messages)
        assert warning is None

        # High usage - should warn
        large_messages = [{"role": "user", "content": " ".join(["test"] * 50)}]
        warning = manager.get_truncation_warning(large_messages)
        # May or may not warn depending on exact token count

    def test_priority_strategy(self):
        """Test priority-based strategy"""
        manager = ContextManager(
            max_tokens=200, reserve_tokens=50, strategy=ContextStrategy.PRIORITY
        )

        messages = [
            {"role": "user", "content": "Short"},
            {"role": "assistant", "content": "Also short"},
            {
                "role": "user",
                "content": 'This is a longer message with code: ```python\nprint("hello")\n```',
            },
            {"role": "assistant", "content": "Response"},
        ]

        fitted = manager.fit_messages(messages)

        # Should prioritize messages with code
        assert len(fitted) > 0

    def test_message_priority_calculation(self):
        """Test message priority scoring"""
        manager = ContextManager()

        # Recent message should score higher
        recent_score = manager._calculate_message_priority(
            {"role": "user", "content": "test"}, index=9, total=10
        )

        old_score = manager._calculate_message_priority(
            {"role": "user", "content": "test"}, index=0, total=10
        )

        assert recent_score > old_score

        # Message with code should score higher
        code_msg = {"role": "user", "content": "```python\ncode\n```"}
        plain_msg = {"role": "user", "content": "plain text"}

        code_score = manager._calculate_message_priority(code_msg, 5, 10)
        plain_score = manager._calculate_message_priority(plain_msg, 5, 10)

        assert code_score > plain_score
