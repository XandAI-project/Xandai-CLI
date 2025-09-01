"""
Robust conversation history system for XandAI CLI.
Handles complete, ordered chat history with support for all message types.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union, Literal
from datetime import datetime
from enum import Enum
import json
import uuid


class MessageRole(Enum):
    """Standard message roles for conversation history."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"
    FUNCTION = "function"


class MessageType(Enum):
    """Types of messages for better organization."""
    CONVERSATION = "conversation"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    SYSTEM_PROMPT = "system_prompt"
    CODING_RULE = "coding_rule"
    CONTEXT_SUMMARY = "context_summary"
    SESSION_MARKER = "session_marker"


@dataclass
class ToolCall:
    """Represents a tool/function call."""
    id: str
    name: str
    arguments: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "arguments": self.arguments
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolCall":
        return cls(
            id=data["id"],
            name=data["name"],
            arguments=data.get("arguments", {})
        )


@dataclass
class ToolResult:
    """Represents the result of a tool/function call."""
    tool_call_id: str
    content: str
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_call_id": self.tool_call_id,
            "content": self.content,
            "success": self.success,
            "error": self.error,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolResult":
        return cls(
            tool_call_id=data["tool_call_id"],
            content=data["content"],
            success=data.get("success", True),
            error=data.get("error"),
            metadata=data.get("metadata", {})
        )


@dataclass
class Message:
    """
    Robust message representation supporting all conversation types.
    """
    id: str
    role: MessageRole
    content: str
    timestamp: datetime
    tokens: int = 0
    message_type: MessageType = MessageType.CONVERSATION
    
    # Optional fields for different message types
    tool_calls: List[ToolCall] = field(default_factory=list)
    tool_results: List[ToolResult] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Context tracking
    model_used: Optional[str] = None
    working_directory: Optional[str] = None
    session_id: Optional[str] = None
    
    def __post_init__(self):
        """Ensure proper types and generate ID if needed."""
        if not self.id:
            self.id = str(uuid.uuid4())
        
        if isinstance(self.role, str):
            self.role = MessageRole(self.role)
            
        if isinstance(self.message_type, str):
            self.message_type = MessageType(self.message_type)
            
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization."""
        return {
            "id": self.id,
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "tokens": self.tokens,
            "message_type": self.message_type.value,
            "tool_calls": [tc.to_dict() for tc in self.tool_calls],
            "tool_results": [tr.to_dict() for tr in self.tool_results],
            "metadata": self.metadata,
            "model_used": self.model_used,
            "working_directory": self.working_directory,
            "session_id": self.session_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create message from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            role=MessageRole(data["role"]),
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            tokens=data.get("tokens", 0),
            message_type=MessageType(data.get("message_type", MessageType.CONVERSATION.value)),
            tool_calls=[ToolCall.from_dict(tc) for tc in data.get("tool_calls", [])],
            tool_results=[ToolResult.from_dict(tr) for tr in data.get("tool_results", [])],
            metadata=data.get("metadata", {}),
            model_used=data.get("model_used"),
            working_directory=data.get("working_directory"),
            session_id=data.get("session_id")
        )
    
    def is_conversation_message(self) -> bool:
        """Check if this is a conversational message (user/assistant)."""
        return (
            self.role in [MessageRole.USER, MessageRole.ASSISTANT] and
            self.message_type == MessageType.CONVERSATION
        )
    
    def is_system_message(self) -> bool:
        """Check if this is a system message."""
        return self.role == MessageRole.SYSTEM
    
    def is_tool_message(self) -> bool:
        """Check if this is a tool-related message."""
        return self.message_type in [MessageType.TOOL_CALL, MessageType.TOOL_RESULT]
    
    def estimate_tokens(self) -> int:
        """Rough token estimation if not set."""
        if self.tokens > 0:
            return self.tokens
        
        # Simple estimation: ~4 characters per token
        base_tokens = len(self.content) // 4
        
        # Add tokens for tool calls
        for tool_call in self.tool_calls:
            base_tokens += len(str(tool_call.arguments)) // 4 + 10  # Extra for structure
        
        # Add tokens for tool results
        for tool_result in self.tool_results:
            base_tokens += len(tool_result.content) // 4 + 5
        
        return max(base_tokens, 1)


@dataclass
class ConversationSummary:
    """Represents a summarized portion of conversation history."""
    id: str
    original_message_count: int
    original_token_count: int
    summary_content: str
    summary_tokens: int
    time_range_start: datetime
    time_range_end: datetime
    created_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "original_message_count": self.original_message_count,
            "original_token_count": self.original_token_count,
            "summary_content": self.summary_content,
            "summary_tokens": self.summary_tokens,
            "time_range_start": self.time_range_start.isoformat(),
            "time_range_end": self.time_range_end.isoformat(),
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationSummary":
        return cls(
            id=data["id"],
            original_message_count=data["original_message_count"],
            original_token_count=data["original_token_count"],
            summary_content=data["summary_content"],
            summary_tokens=data["summary_tokens"],
            time_range_start=datetime.fromisoformat(data["time_range_start"]),
            time_range_end=datetime.fromisoformat(data["time_range_end"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            metadata=data.get("metadata", {})
        )


@dataclass
class ConversationHistory:
    """
    Complete conversation history with robust message management.
    """
    id: str
    created_at: datetime
    last_updated: datetime
    messages: List[Message] = field(default_factory=list)
    summaries: List[ConversationSummary] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Statistics
    total_tokens: int = 0
    total_messages: int = 0
    
    def __post_init__(self):
        """Initialize conversation history."""
        if not self.id:
            self.id = str(uuid.uuid4())
        
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)
            
        if isinstance(self.last_updated, str):
            self.last_updated = datetime.fromisoformat(self.last_updated)
        
        self._update_statistics()
    
    def add_message(self, message: Message) -> None:
        """Add a message to the conversation."""
        message.session_id = self.id
        self.messages.append(message)
        self.last_updated = datetime.now()
        self._update_statistics()
    
    def add_user_message(self, content: str, **kwargs) -> Message:
        """Convenience method to add user message."""
        message = Message(
            id=str(uuid.uuid4()),
            role=MessageRole.USER,
            content=content,
            timestamp=datetime.now(),
            **kwargs
        )
        self.add_message(message)
        return message
    
    def add_assistant_message(self, content: str, **kwargs) -> Message:
        """Convenience method to add assistant message."""
        message = Message(
            id=str(uuid.uuid4()),
            role=MessageRole.ASSISTANT,
            content=content,
            timestamp=datetime.now(),
            **kwargs
        )
        self.add_message(message)
        return message
    
    def add_system_message(self, content: str, message_type: MessageType = MessageType.SYSTEM_PROMPT, **kwargs) -> Message:
        """Convenience method to add system message."""
        message = Message(
            id=str(uuid.uuid4()),
            role=MessageRole.SYSTEM,
            content=content,
            timestamp=datetime.now(),
            message_type=message_type,
            **kwargs
        )
        self.add_message(message)
        return message
    
    def add_tool_call(self, content: str, tool_calls: List[ToolCall], **kwargs) -> Message:
        """Add a message with tool calls."""
        message = Message(
            id=str(uuid.uuid4()),
            role=MessageRole.ASSISTANT,
            content=content,
            timestamp=datetime.now(),
            message_type=MessageType.TOOL_CALL,
            tool_calls=tool_calls,
            **kwargs
        )
        self.add_message(message)
        return message
    
    def add_tool_result(self, tool_results: List[ToolResult], **kwargs) -> Message:
        """Add tool results."""
        content = f"Tool results: {len(tool_results)} result(s)"
        message = Message(
            id=str(uuid.uuid4()),
            role=MessageRole.TOOL,
            content=content,
            timestamp=datetime.now(),
            message_type=MessageType.TOOL_RESULT,
            tool_results=tool_results,
            **kwargs
        )
        self.add_message(message)
        return message
    
    def get_conversation_messages(self) -> List[Message]:
        """Get only conversation messages (user/assistant)."""
        return [msg for msg in self.messages if msg.is_conversation_message()]
    
    def get_recent_messages(self, count: int) -> List[Message]:
        """Get the most recent messages."""
        return self.messages[-count:] if count > 0 else []
    
    def get_messages_by_type(self, message_type: MessageType) -> List[Message]:
        """Get messages of a specific type."""
        return [msg for msg in self.messages if msg.message_type == message_type]
    
    def get_messages_in_range(self, start_time: datetime, end_time: datetime) -> List[Message]:
        """Get messages within a time range."""
        return [
            msg for msg in self.messages 
            if start_time <= msg.timestamp <= end_time
        ]
    
    def calculate_token_count(self, messages: Optional[List[Message]] = None) -> int:
        """Calculate total token count for given messages."""
        if messages is None:
            messages = self.messages
        return sum(msg.estimate_tokens() for msg in messages)
    
    def add_summary(self, summary: ConversationSummary) -> None:
        """Add a conversation summary."""
        self.summaries.append(summary)
        self.last_updated = datetime.now()
    
    def _update_statistics(self):
        """Update internal statistics."""
        self.total_messages = len(self.messages)
        self.total_tokens = self.calculate_token_count()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "messages": [msg.to_dict() for msg in self.messages],
            "summaries": [summary.to_dict() for summary in self.summaries],
            "metadata": self.metadata,
            "total_tokens": self.total_tokens,
            "total_messages": self.total_messages
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationHistory":
        """Create from dictionary."""
        history = cls(
            id=data["id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            last_updated=datetime.fromisoformat(data["last_updated"]),
            messages=[Message.from_dict(msg) for msg in data.get("messages", [])],
            summaries=[ConversationSummary.from_dict(s) for s in data.get("summaries", [])],
            metadata=data.get("metadata", {}),
            total_tokens=data.get("total_tokens", 0),
            total_messages=data.get("total_messages", 0)
        )
        return history
