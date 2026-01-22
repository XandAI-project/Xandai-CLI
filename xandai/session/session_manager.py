"""
Session Manager

Manages persistent chat sessions with context preservation.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from xandai.session.models import Message, Session
from xandai.session.session_storage import SessionStorage


class SessionManager:
    """
    Session Manager

    Manages chat sessions with persistence.
    """

    def __init__(self, storage: Optional[SessionStorage] = None):
        """
        Initialize session manager

        Args:
            storage: Session storage backend
        """
        self.storage = storage or SessionStorage()
        self.current_session: Optional[Session] = None

    def create_session(
        self,
        name: Optional[str] = None,
        provider: str = "unknown",
        model: str = "unknown",
        **metadata,
    ) -> Session:
        """
        Create a new session

        Args:
            name: Session name
            provider: LLM provider
            model: Model name
            **metadata: Additional metadata

        Returns:
            Created session
        """
        session_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        if not name:
            name = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        session = Session(
            id=session_id,
            name=name,
            created_at=now,
            updated_at=now,
            provider=provider,
            model=model,
            metadata=metadata,
        )

        self.storage.save_session(session)
        return session

    def load_session(self, session_id: str) -> Optional[Session]:
        """
        Load a session by ID

        Args:
            session_id: Session ID

        Returns:
            Session or None if not found
        """
        return self.storage.load_session(session_id)

    def load_session_by_name(self, name: str) -> Optional[Session]:
        """
        Load a session by name

        Args:
            name: Session name

        Returns:
            Session or None if not found
        """
        return self.storage.load_session_by_name(name)

    def save_session(self, session: Session):
        """
        Save session to storage

        Args:
            session: Session to save
        """
        self.storage.save_session(session)

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session

        Args:
            session_id: Session ID

        Returns:
            True if deleted, False otherwise
        """
        return self.storage.delete_session(session_id)

    def list_sessions(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        List all sessions

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List of session metadata
        """
        return self.storage.list_sessions(limit)

    def search_sessions(self, query: str) -> List[Dict[str, Any]]:
        """
        Search sessions by name or content

        Args:
            query: Search query

        Returns:
            List of matching sessions
        """
        return self.storage.search_sessions(query)

    def set_current_session(self, session: Session):
        """Set the current active session"""
        self.current_session = session

    def get_current_session(self) -> Optional[Session]:
        """Get the current active session"""
        return self.current_session

    def add_message(
        self,
        role: str,
        content: str,
        tokens: int = 0,
        session: Optional[Session] = None,
        auto_save: bool = True,
        **metadata,
    ):
        """
        Add a message to a session

        Args:
            role: Message role (user, assistant, system)
            content: Message content
            tokens: Token count
            session: Session to add to (current if None)
            auto_save: Auto-save to storage
            **metadata: Additional metadata
        """
        target_session = session or self.current_session

        if not target_session:
            raise ValueError("No active session. Create or load a session first.")

        target_session.add_message(role, content, tokens, **metadata)

        if auto_save:
            self.save_session(target_session)

    def export_session(self, session_id: str, filepath: str, format: str = "json"):
        """
        Export session to file

        Args:
            session_id: Session ID
            filepath: Output file path
            format: Export format (json, markdown)
        """
        session = self.load_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        if format == "json":
            import json

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(session.to_dict(), f, indent=2, ensure_ascii=False)

        elif format == "markdown":
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"# {session.name}\n\n")
                f.write(f"**Created**: {session.created_at}\n")
                f.write(f"**Updated**: {session.updated_at}\n")
                f.write(f"**Provider**: {session.provider}\n")
                f.write(f"**Model**: {session.model}\n")
                f.write(f"**Total Tokens**: {session.total_tokens}\n\n")
                f.write("---\n\n")

                for msg in session.messages:
                    f.write(f"## {msg.role.upper()}\n\n")
                    f.write(f"{msg.content}\n\n")
                    f.write(f"*{msg.timestamp} - {msg.tokens} tokens*\n\n")
                    f.write("---\n\n")

        else:
            raise ValueError(f"Unsupported format: {format}")

    def import_session(self, filepath: str) -> Session:
        """
        Import session from file

        Args:
            filepath: Input file path

        Returns:
            Imported session
        """
        import json

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        session = Session.from_dict(data)
        self.save_session(session)

        return session

    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """
        Get statistics for a session

        Args:
            session_id: Session ID

        Returns:
            Session statistics
        """
        session = self.load_session(session_id)
        if not session:
            return {}

        user_messages = [m for m in session.messages if m.role == "user"]
        assistant_messages = [m for m in session.messages if m.role == "assistant"]

        return {
            "id": session.id,
            "name": session.name,
            "total_messages": len(session.messages),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "total_tokens": session.total_tokens,
            "avg_tokens_per_message": (
                session.total_tokens / len(session.messages) if session.messages else 0
            ),
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "duration": self._calculate_duration(session.created_at, session.updated_at),
            "provider": session.provider,
            "model": session.model,
        }

    def _calculate_duration(self, start: str, end: str) -> str:
        """Calculate duration between two timestamps"""
        try:
            start_dt = datetime.fromisoformat(start)
            end_dt = datetime.fromisoformat(end)
            delta = end_dt - start_dt

            hours = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60

            if delta.days > 0:
                return f"{delta.days}d {hours}h"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
        except:
            return "unknown"
