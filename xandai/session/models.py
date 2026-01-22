"""
Session Data Models

Core data structures for session management.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Message:
    """Chat message"""

    role: str
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    tokens: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        """Create from dictionary"""
        return cls(**data)


@dataclass
class Session:
    """Chat session"""

    id: str
    name: str
    created_at: str
    updated_at: str
    messages: List[Message] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    total_tokens: int = 0
    provider: str = "unknown"
    model: str = "unknown"

    def add_message(self, role: str, content: str, tokens: int = 0, **metadata):
        """Add a message to the session"""
        message = Message(role=role, content=content, tokens=tokens, metadata=metadata)
        self.messages.append(message)
        self.total_tokens += tokens
        self.updated_at = datetime.now().isoformat()

    def get_messages(self, limit: Optional[int] = None) -> List[Message]:
        """Get messages (optionally limited)"""
        if limit:
            return self.messages[-limit:]
        return self.messages

    def clear_messages(self):
        """Clear all messages"""
        self.messages.clear()
        self.total_tokens = 0
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        data = asdict(self)
        data["messages"] = [msg.to_dict() for msg in self.messages]
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        """Create from dictionary"""
        messages_data = data.pop("messages", [])
        messages = [Message.from_dict(msg) for msg in messages_data]
        session = cls(**data)
        session.messages = messages
        return session
