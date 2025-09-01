"""
Tests for the robust conversation history system.
"""

import pytest
import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, MagicMock

from xandai.conversation import (
    ConversationHistory, Message, MessageRole, MessageType,
    ToolCall, ToolResult, ConversationSummary,
    TokenBudgetManager, TokenBudgetStrategy, ModelRegistry,
    ConversationSummarizer, HistoryManager
)


class TestConversationHistory:
    """Test the core conversation history functionality."""
    
    def test_message_creation(self):
        """Test creating and manipulating messages."""
        message = Message(
            id="test-1",
            role=MessageRole.USER,
            content="Hello, world!",
            timestamp=datetime.now(),
            tokens=3
        )
        
        assert message.id == "test-1"
        assert message.role == MessageRole.USER
        assert message.content == "Hello, world!"
        assert message.tokens == 3
        assert message.is_conversation_message()
        assert not message.is_system_message()
        assert not message.is_tool_message()
    
    def test_message_serialization(self):
        """Test message serialization and deserialization."""
        original = Message(
            id="test-1",
            role=MessageRole.ASSISTANT,
            content="Hello!",
            timestamp=datetime.now(),
            tokens=2,
            model_used="llama3:8b"
        )
        
        # Serialize
        data = original.to_dict()
        assert isinstance(data, dict)
        assert data["role"] == "assistant"
        assert data["model_used"] == "llama3:8b"
        
        # Deserialize
        reconstructed = Message.from_dict(data)
        assert reconstructed.id == original.id
        assert reconstructed.role == original.role
        assert reconstructed.content == original.content
        assert reconstructed.model_used == original.model_used
    
    def test_tool_calls(self):
        """Test messages with tool calls."""
        tool_call = ToolCall(
            id="call-1",
            name="read_file",
            arguments={"path": "test.py"}
        )
        
        message = Message(
            id="test-1",
            role=MessageRole.ASSISTANT,
            content="I'll read the file",
            timestamp=datetime.now(),
            message_type=MessageType.TOOL_CALL,
            tool_calls=[tool_call]
        )
        
        assert message.is_tool_message()
        assert len(message.tool_calls) == 1
        assert message.tool_calls[0].name == "read_file"
        
        # Test serialization
        data = message.to_dict()
        reconstructed = Message.from_dict(data)
        assert len(reconstructed.tool_calls) == 1
        assert reconstructed.tool_calls[0].name == "read_file"
    
    def test_conversation_creation(self):
        """Test creating and managing conversations."""
        conv = ConversationHistory(
            id="test-conv",
            created_at=datetime.now(),
            last_updated=datetime.now()
        )
        
        assert conv.id == "test-conv"
        assert len(conv.messages) == 0
        assert conv.total_messages == 0
        assert conv.total_tokens == 0
    
    def test_adding_messages(self):
        """Test adding various types of messages to conversation."""
        conv = ConversationHistory(
            id="test-conv",
            created_at=datetime.now(),
            last_updated=datetime.now()
        )
        
        # Add user message
        user_msg = conv.add_user_message("Hello!")
        assert user_msg.role == MessageRole.USER
        assert len(conv.messages) == 1
        
        # Add assistant message
        assistant_msg = conv.add_assistant_message("Hi there!")
        assert assistant_msg.role == MessageRole.ASSISTANT
        assert len(conv.messages) == 2
        
        # Add system message
        system_msg = conv.add_system_message("System ready", MessageType.SYSTEM_PROMPT)
        assert system_msg.role == MessageRole.SYSTEM
        assert system_msg.message_type == MessageType.SYSTEM_PROMPT
        assert len(conv.messages) == 3
        
        # Check conversation messages
        conversation_messages = conv.get_conversation_messages()
        assert len(conversation_messages) == 2  # user + assistant
    
    def test_conversation_serialization(self):
        """Test conversation serialization."""
        conv = ConversationHistory(
            id="test-conv",
            created_at=datetime.now(),
            last_updated=datetime.now()
        )
        
        conv.add_user_message("Test message")
        conv.add_assistant_message("Test response")
        
        # Serialize
        data = conv.to_dict()
        assert isinstance(data, dict)
        assert data["id"] == "test-conv"
        assert len(data["messages"]) == 2
        
        # Deserialize
        reconstructed = ConversationHistory.from_dict(data)
        assert reconstructed.id == conv.id
        assert len(reconstructed.messages) == 2
        assert reconstructed.messages[0].content == "Test message"


class TestTokenBudgetManager:
    """Test token budget management."""
    
    def test_model_registry(self):
        """Test model information registry."""
        # Test known model
        llama3_info = ModelRegistry.get_model_info("llama3:8b")
        assert llama3_info.name == "llama3:8b"
        assert llama3_info.context_length == 8192
        
        # Test unknown model
        unknown_info = ModelRegistry.get_model_info("unknown-model:7b")
        assert unknown_info.name == "unknown-model:7b"
        assert unknown_info.context_length == 4096  # Default
    
    def test_token_calculation(self):
        """Test token calculation methods."""
        manager = TokenBudgetManager("llama3:8b")
        
        # Test simple text
        tokens = manager.calculate_tokens("Hello world")
        assert tokens > 0
        assert tokens < 10  # Should be reasonable
        
        # Test longer text
        long_text = "This is a longer piece of text that should have more tokens " * 10
        long_tokens = manager.calculate_tokens(long_text)
        assert long_tokens > tokens
        
        # Test caching
        cached_tokens = manager.calculate_tokens("Hello world")
        assert cached_tokens == tokens
    
    def test_context_assessment(self):
        """Test context assessment functionality."""
        manager = TokenBudgetManager("llama3:8b")
        
        # Create test messages
        messages = [
            Message(
                id=f"msg-{i}",
                role=MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT,
                content=f"Test message {i} with some content",
                timestamp=datetime.now(),
                tokens=10
            )
            for i in range(20)
        ]
        
        analysis = manager.assess_context_fit(messages)
        
        assert "total_tokens" in analysis
        assert "available_context" in analysis
        assert "utilization" in analysis
        assert "fits" in analysis
        assert "recommendations" in analysis
        assert analysis["total_tokens"] > 0
    
    def test_message_optimization(self):
        """Test message list optimization."""
        manager = TokenBudgetManager("llama3:8b")
        
        # Create many messages to trigger optimization
        messages = []
        for i in range(100):
            msg = Message(
                id=f"msg-{i}",
                role=MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT,
                content=f"Message {i}: " + "content " * 50,  # Make it token-heavy
                timestamp=datetime.now() - timedelta(hours=100-i),
                tokens=200
            )
            messages.append(msg)
        
        optimized, report = manager.optimize_message_list(messages)
        
        assert len(optimized) <= len(messages)
        assert report["tokens_saved"] >= 0
        assert "action" in report
        
        # Should preserve recent messages
        assert optimized[-1].id == messages[-1].id  # Most recent preserved


class TestConversationSummarizer:
    """Test conversation summarization."""
    
    def setup_method(self):
        """Set up test dependencies."""
        self.mock_api = Mock()
        self.token_manager = TokenBudgetManager("llama3:8b")
        self.summarizer = ConversationSummarizer(self.mock_api, self.token_manager)
    
    def test_summarization_eligibility(self):
        """Test whether messages are eligible for summarization."""
        # Too few messages
        few_messages = [
            Message(
                id="msg-1",
                role=MessageRole.USER,
                content="Hello",
                timestamp=datetime.now() - timedelta(hours=2)
            )
        ]
        assert not self.summarizer.can_summarize(few_messages)
        
        # Enough old messages
        old_messages = [
            Message(
                id=f"msg-{i}",
                role=MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT,
                content=f"Message {i} with meaningful content here",
                timestamp=datetime.now() - timedelta(hours=2)
            )
            for i in range(5)
        ]
        assert self.summarizer.can_summarize(old_messages)
        
        # Recent messages (should not summarize)
        recent_messages = [
            Message(
                id=f"msg-{i}",
                role=MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT,
                content=f"Recent message {i}",
                timestamp=datetime.now() - timedelta(minutes=30)
            )
            for i in range(5)
        ]
        assert not self.summarizer.can_summarize(recent_messages)
    
    def test_conversation_classification(self):
        """Test conversation type classification."""
        # Regular conversation
        regular_messages = [
            Message("1", MessageRole.USER, "How are you?", datetime.now()),
            Message("2", MessageRole.ASSISTANT, "I'm doing well!", datetime.now())
        ]
        conv_type = self.summarizer._classify_conversation_type(regular_messages)
        assert conv_type == "conversation"
        
        # Code-heavy conversation
        code_messages = [
            Message("1", MessageRole.USER, "Write a function to sort arrays", datetime.now()),
            Message("2", MessageRole.ASSISTANT, "def sort_array(arr): return sorted(arr)", datetime.now()),
            Message("3", MessageRole.USER, "Add error handling with try/except", datetime.now())
        ]
        conv_type = self.summarizer._classify_conversation_type(code_messages)
        assert conv_type == "code_session"
    
    def test_conversation_text_preparation(self):
        """Test preparing conversation text for summarization."""
        messages = [
            Message(
                id="1", 
                role=MessageRole.USER, 
                content="Hello AI",
                timestamp=datetime(2024, 1, 1, 10, 0)
            ),
            Message(
                id="2",
                role=MessageRole.ASSISTANT,
                content="Hello! How can I help?",
                timestamp=datetime(2024, 1, 1, 10, 1)
            )
        ]
        
        text = self.summarizer._prepare_conversation_text(messages)
        
        assert "2024-01-01 10:00" in text
        assert "USER: Hello AI" in text
        assert "ASSISTANT: Hello! How can I help?" in text


class TestHistoryManager:
    """Test the main history manager interface."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.mock_api = Mock()
        self.history_manager = HistoryManager(
            storage_dir=self.temp_dir,
            api=self.mock_api
        )
        
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test history manager initialization."""
        assert self.history_manager.storage_dir == Path(self.temp_dir)
        assert self.history_manager.current_conversation is not None
        assert self.history_manager.api == self.mock_api
    
    def test_model_setting(self):
        """Test setting and changing models."""
        self.history_manager.set_model("llama3:8b")
        
        assert self.history_manager.current_model == "llama3:8b"
        assert self.history_manager.current_token_manager is not None
        assert self.history_manager.current_summarizer is not None
    
    def test_message_addition(self):
        """Test adding different types of messages."""
        self.history_manager.set_model("llama3:8b")
        
        # Add user message
        user_msg = self.history_manager.add_user_message("Hello!")
        assert user_msg.role == MessageRole.USER
        assert user_msg.content == "Hello!"
        assert user_msg.tokens > 0
        
        # Add assistant message
        assistant_msg = self.history_manager.add_assistant_message("Hi there!")
        assert assistant_msg.role == MessageRole.ASSISTANT
        
        # Add system message
        system_msg = self.history_manager.add_system_message("System ready")
        assert system_msg.role == MessageRole.SYSTEM
        
        # Check conversation state
        assert len(self.history_manager.current_conversation.messages) == 3
    
    def test_context_management(self):
        """Test context management features."""
        self.history_manager.set_model("llama3:8b")
        
        # Add many messages
        for i in range(50):
            if i % 2 == 0:
                self.history_manager.add_user_message(f"User message {i}")
            else:
                self.history_manager.add_assistant_message(f"Assistant response {i}")
        
        # Get optimized context
        context_messages = self.history_manager.get_context_for_model()
        assert len(context_messages) <= 50
        
        # Get status
        status = self.history_manager.get_context_status()
        assert "conversation_info" in status
        assert "utilization" in status
    
    def test_conversation_persistence(self):
        """Test that conversations are saved and loaded properly."""
        self.history_manager.set_model("llama3:8b")
        
        # Add some messages
        self.history_manager.add_user_message("Test message")
        self.history_manager.add_assistant_message("Test response")
        
        conv_id = self.history_manager.current_conversation.id
        
        # Create new manager with same storage
        new_manager = HistoryManager(storage_dir=self.temp_dir, api=self.mock_api)
        
        # Should load the previous conversation
        assert new_manager.current_conversation is not None
        assert len(new_manager.current_conversation.messages) == 2
        assert new_manager.current_conversation.messages[0].content == "Test message"
    
    def test_conversation_export(self):
        """Test conversation export functionality."""
        self.history_manager.set_model("llama3:8b")
        
        self.history_manager.add_user_message("Hello")
        self.history_manager.add_assistant_message("Hi there")
        
        # Test JSON export
        json_export = self.history_manager.export_conversation("json")
        assert json_export
        data = json.loads(json_export)
        assert len(data["messages"]) == 2
        
        # Test Markdown export
        md_export = self.history_manager.export_conversation("markdown")
        assert "# Conversation" in md_export
        assert "Hello" in md_export
        
        # Test Text export
        txt_export = self.history_manager.export_conversation("txt")
        assert "USER: Hello" in txt_export
    
    def test_statistics(self):
        """Test statistics generation."""
        self.history_manager.set_model("llama3:8b")
        
        self.history_manager.add_user_message("Test")
        self.history_manager.add_assistant_message("Response")
        
        stats = self.history_manager.get_statistics()
        
        assert "conversation_id" in stats
        assert "message_counts" in stats
        assert "token_counts" in stats
        assert stats["message_counts"]["total"] == 2
        assert stats["message_counts"]["user"] == 1
        assert stats["message_counts"]["assistant"] == 1


class TestLoadTesting:
    """Load tests to validate token budgeting under stress."""
    
    def test_large_conversation_load(self):
        """Test handling of very large conversations."""
        manager = TokenBudgetManager("llama3:8b")  # 8K context
        
        # Create a conversation with way too many tokens
        messages = []
        for i in range(1000):
            content = f"Message {i}: " + "token-heavy content " * 20
            msg = Message(
                id=f"msg-{i}",
                role=MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT,
                content=content,
                timestamp=datetime.now() - timedelta(minutes=1000-i),
                tokens=manager.calculate_tokens(content)
            )
            messages.append(msg)
        
        # This should trigger optimization
        optimized, report = manager.optimize_message_list(messages)
        
        # Verify optimization worked
        assert len(optimized) < len(messages)
        assert report["tokens_saved"] > 0
        
        # Context should now fit
        analysis = manager.assess_context_fit(optimized)
        assert analysis["fits"]
        
        print(f"Load test results:")
        print(f"Original messages: {len(messages)}")
        print(f"Optimized messages: {len(optimized)}")
        print(f"Tokens saved: {report['tokens_saved']:,}")
        print(f"Final utilization: {analysis['utilization']:.1%}")
    
    def test_token_budget_accuracy(self):
        """Test accuracy of token budget calculations."""
        models_to_test = ["llama3:8b", "qwen2.5-coder", "mistral:7b", "unknown-model"]
        
        for model_name in models_to_test:
            manager = TokenBudgetManager(model_name)
            
            # Test various text lengths
            test_texts = [
                "Short",
                "Medium length text with some words",
                "Much longer text that contains multiple sentences and should have significantly more tokens. " * 10,
                "Code-like content: def function(arg): return arg.process() if arg else None",
                "Mixed content with punctuation!!! And... various? Symbols & numbers: 123, 456."
            ]
            
            for text in test_texts:
                tokens = manager.calculate_tokens(text)
                # Token count should be reasonable (not zero, not crazy high)
                assert 1 <= tokens <= len(text), f"Unreasonable token count for '{text[:50]}...': {tokens}"
            
            print(f"Model {model_name}: Context={manager.model_info.context_length}, Available={manager.model_info.get_available_context()}")


if __name__ == "__main__":
    # Run basic tests
    pytest.main([__file__, "-v"])
