"""
Robust conversation history system for XandAI CLI.

This package provides comprehensive conversation management with:
- Persistent, ordered chat history
- Token budget management with model-specific limits
- Auto-summarization of old conversations
- Support for tool/function call messages
- Clean APIs for integration

Main components:
- HistoryManager: Main interface for all operations
- ConversationHistory: Core data structure for messages
- TokenBudgetManager: Smart token budget management
- ConversationSummarizer: Auto-summarization system
"""

from .conversation_history import (
    ConversationHistory,
    Message,
    MessageRole,
    MessageType,
    ToolCall,
    ToolResult,
    ConversationSummary
)

from .token_budget_manager import (
    TokenBudgetManager,
    TokenBudgetStrategy,
    ModelRegistry,
    ModelInfo,
    ModelFamily
)

from .conversation_summarizer import (
    ConversationSummarizer,
    SummarizationError
)

from .history_manager import (
    HistoryManager,
    HistoryManagerError
)

__all__ = [
    # Core data structures
    "ConversationHistory",
    "Message",
    "MessageRole", 
    "MessageType",
    "ToolCall",
    "ToolResult",
    "ConversationSummary",
    
    # Token management
    "TokenBudgetManager",
    "TokenBudgetStrategy", 
    "ModelRegistry",
    "ModelInfo",
    "ModelFamily",
    
    # Summarization
    "ConversationSummarizer",
    "SummarizationError",
    
    # Main interface
    "HistoryManager",
    "HistoryManagerError"
]

__version__ = "1.0.0"
