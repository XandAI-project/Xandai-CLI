"""
Session Storage

SQLite-based persistent storage for sessions.
"""

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

from xandai.session.models import Message, Session


class SessionStorage:
    """
    Session Storage Backend

    Uses SQLite for lightweight, serverless persistence.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize session storage

        Args:
            db_path: Database file path (default: ~/.xandai/sessions.db)
        """
        if db_path:
            self.db_path = Path(db_path)
        else:
            # Default location
            home = Path.home()
            xandai_dir = home / ".xandai"
            xandai_dir.mkdir(exist_ok=True)
            self.db_path = xandai_dir / "sessions.db"

        self._init_database()

    def _init_database(self):
        """Initialize database schema"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Sessions table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    total_tokens INTEGER DEFAULT 0,
                    provider TEXT,
                    model TEXT,
                    metadata TEXT
                )
            """
            )

            # Messages table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    tokens INTEGER DEFAULT 0,
                    metadata TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                )
            """
            )

            # Indexes for performance
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_sessions_name
                ON sessions(name)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_sessions_updated
                ON sessions(updated_at DESC)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_messages_session
                ON messages(session_id)
            """
            )

            conn.commit()

    @contextmanager
    def _get_connection(self):
        """Get database connection context manager"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def save_session(self, session: Session):
        """
        Save or update a session

        Args:
            session: Session to save
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Check if session exists
            cursor.execute("SELECT id FROM sessions WHERE id = ?", (session.id,))
            exists = cursor.fetchone() is not None

            if exists:
                # Update existing session
                cursor.execute(
                    """
                    UPDATE sessions
                    SET name = ?, updated_at = ?, total_tokens = ?,
                        provider = ?, model = ?, metadata = ?
                    WHERE id = ?
                """,
                    (
                        session.name,
                        session.updated_at,
                        session.total_tokens,
                        session.provider,
                        session.model,
                        json.dumps(session.metadata),
                        session.id,
                    ),
                )

                # Delete old messages
                cursor.execute("DELETE FROM messages WHERE session_id = ?", (session.id,))
            else:
                # Insert new session
                cursor.execute(
                    """
                    INSERT INTO sessions (id, name, created_at, updated_at,
                                        total_tokens, provider, model, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        session.id,
                        session.name,
                        session.created_at,
                        session.updated_at,
                        session.total_tokens,
                        session.provider,
                        session.model,
                        json.dumps(session.metadata),
                    ),
                )

            # Insert messages
            for message in session.messages:
                cursor.execute(
                    """
                    INSERT INTO messages (session_id, role, content, timestamp,
                                        tokens, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        session.id,
                        message.role,
                        message.content,
                        message.timestamp,
                        message.tokens,
                        json.dumps(message.metadata),
                    ),
                )

            conn.commit()

    def load_session(self, session_id: str) -> Optional[Session]:
        """
        Load a session by ID

        Args:
            session_id: Session ID

        Returns:
            Session or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Load session
            cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
            row = cursor.fetchone()

            if not row:
                return None

            # Load messages
            cursor.execute(
                """
                SELECT * FROM messages
                WHERE session_id = ?
                ORDER BY id ASC
            """,
                (session_id,),
            )

            messages = []
            for msg_row in cursor.fetchall():
                messages.append(
                    Message(
                        role=msg_row["role"],
                        content=msg_row["content"],
                        timestamp=msg_row["timestamp"],
                        tokens=msg_row["tokens"],
                        metadata=json.loads(msg_row["metadata"]) if msg_row["metadata"] else {},
                    )
                )

            # Create session
            session = Session(
                id=row["id"],
                name=row["name"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                messages=messages,
                total_tokens=row["total_tokens"],
                provider=row["provider"],
                model=row["model"],
                metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            )

            return session

    def load_session_by_name(self, name: str) -> Optional[Session]:
        """
        Load most recent session with given name

        Args:
            name: Session name

        Returns:
            Session or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id FROM sessions
                WHERE name = ?
                ORDER BY updated_at DESC
                LIMIT 1
            """,
                (name,),
            )

            row = cursor.fetchone()

            if not row:
                return None

            return self.load_session(row["id"])

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session

        Args:
            session_id: Session ID

        Returns:
            True if deleted, False if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            deleted = cursor.rowcount > 0

            conn.commit()

            return deleted

    def list_sessions(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        List all sessions

        Args:
            limit: Maximum number of sessions

        Returns:
            List of session metadata
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT id, name, created_at, updated_at, total_tokens,
                       provider, model
                FROM sessions
                ORDER BY updated_at DESC
            """

            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query)

            sessions = []
            for row in cursor.fetchall():
                sessions.append(
                    {
                        "id": row["id"],
                        "name": row["name"],
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                        "total_tokens": row["total_tokens"],
                        "provider": row["provider"],
                        "model": row["model"],
                    }
                )

            return sessions

    def search_sessions(self, query: str) -> List[Dict[str, Any]]:
        """
        Search sessions by name or content

        Args:
            query: Search query

        Returns:
            Matching sessions
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            search_pattern = f"%{query}%"

            cursor.execute(
                """
                SELECT DISTINCT s.id, s.name, s.created_at, s.updated_at,
                                s.total_tokens, s.provider, s.model
                FROM sessions s
                LEFT JOIN messages m ON s.id = m.session_id
                WHERE s.name LIKE ? OR m.content LIKE ?
                ORDER BY s.updated_at DESC
            """,
                (search_pattern, search_pattern),
            )

            sessions = []
            for row in cursor.fetchall():
                sessions.append(
                    {
                        "id": row["id"],
                        "name": row["name"],
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                        "total_tokens": row["total_tokens"],
                        "provider": row["provider"],
                        "model": row["model"],
                    }
                )

            return sessions

    def get_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics

        Returns:
            Storage stats
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Total sessions
            cursor.execute("SELECT COUNT(*) as count FROM sessions")
            total_sessions = cursor.fetchone()["count"]

            # Total messages
            cursor.execute("SELECT COUNT(*) as count FROM messages")
            total_messages = cursor.fetchone()["count"]

            # Total tokens
            cursor.execute("SELECT SUM(total_tokens) as total FROM sessions")
            total_tokens = cursor.fetchone()["total"] or 0

            # Database size
            db_size = self.db_path.stat().st_size if self.db_path.exists() else 0

            return {
                "total_sessions": total_sessions,
                "total_messages": total_messages,
                "total_tokens": total_tokens,
                "database_size": db_size,
                "database_path": str(self.db_path),
            }

    def cleanup_old_sessions(self, days: int = 30) -> int:
        """
        Delete sessions older than specified days

        Args:
            days: Age threshold in days

        Returns:
            Number of deleted sessions
        """
        from datetime import datetime, timedelta

        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                DELETE FROM sessions
                WHERE updated_at < ?
            """,
                (cutoff,),
            )

            deleted = cursor.rowcount
            conn.commit()

            return deleted
