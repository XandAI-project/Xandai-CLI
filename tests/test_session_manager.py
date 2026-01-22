"""
Tests for Session Management System
"""

import tempfile
from pathlib import Path

import pytest

from xandai.session.models import Message, Session
from xandai.session.session_manager import SessionManager
from xandai.session.session_storage import SessionStorage


class TestMessage:
    """Test Message class"""

    def test_create_message(self):
        """Test creating a message"""
        msg = Message(role="user", content="Hello", tokens=5)
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.tokens == 5

    def test_message_to_dict(self):
        """Test converting message to dict"""
        msg = Message(role="assistant", content="Hi", tokens=3)
        d = msg.to_dict()
        assert d["role"] == "assistant"
        assert d["content"] == "Hi"

    def test_message_from_dict(self):
        """Test creating message from dict"""
        d = {
            "role": "system",
            "content": "You are helpful",
            "timestamp": "2024-01-01T00:00:00",
            "tokens": 10,
            "metadata": {},
        }
        msg = Message.from_dict(d)
        assert msg.role == "system"
        assert msg.content == "You are helpful"


class TestSession:
    """Test Session class"""

    def test_create_session(self):
        """Test creating a session"""
        session = Session(
            id="test-id",
            name="test",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )
        assert session.id == "test-id"
        assert session.name == "test"
        assert len(session.messages) == 0

    def test_add_message(self):
        """Test adding message to session"""
        session = Session(
            id="test",
            name="test",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )
        session.add_message("user", "Hello", tokens=5)

        assert len(session.messages) == 1
        assert session.messages[0].role == "user"
        assert session.total_tokens == 5

    def test_get_messages(self):
        """Test getting messages"""
        session = Session(
            id="test",
            name="test",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )
        session.add_message("user", "1")
        session.add_message("assistant", "2")
        session.add_message("user", "3")

        all_msgs = session.get_messages()
        assert len(all_msgs) == 3

        limited = session.get_messages(limit=2)
        assert len(limited) == 2
        assert limited[0].content == "2"

    def test_clear_messages(self):
        """Test clearing messages"""
        session = Session(
            id="test",
            name="test",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )
        session.add_message("user", "Hello", tokens=10)
        session.clear_messages()

        assert len(session.messages) == 0
        assert session.total_tokens == 0


class TestSessionStorage:
    """Test Session Storage"""

    def setup_method(self):
        """Setup for each test"""
        # Use temporary database
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        self.storage = SessionStorage(str(self.db_path))

    def test_save_and_load_session(self):
        """Test saving and loading a session"""
        session = Session(
            id="test-123",
            name="test-session",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
            provider="test",
            model="test-model",
        )
        session.add_message("user", "Hello", tokens=5)

        self.storage.save_session(session)
        loaded = self.storage.load_session("test-123")

        assert loaded is not None
        assert loaded.id == "test-123"
        assert loaded.name == "test-session"
        assert len(loaded.messages) == 1
        assert loaded.total_tokens == 5

    def test_load_nonexistent_session(self):
        """Test loading nonexistent session"""
        loaded = self.storage.load_session("nonexistent")
        assert loaded is None

    def test_delete_session(self):
        """Test deleting a session"""
        session = Session(
            id="delete-me",
            name="test",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )
        self.storage.save_session(session)

        deleted = self.storage.delete_session("delete-me")
        assert deleted is True

        loaded = self.storage.load_session("delete-me")
        assert loaded is None

    def test_list_sessions(self):
        """Test listing sessions"""
        for i in range(3):
            session = Session(
                id=f"session-{i}",
                name=f"test-{i}",
                created_at="2024-01-01T00:00:00",
                updated_at=f"2024-01-01T00:00:0{i}",
            )
            self.storage.save_session(session)

        sessions = self.storage.list_sessions()
        assert len(sessions) == 3

        limited = self.storage.list_sessions(limit=2)
        assert len(limited) == 2

    def test_search_sessions(self):
        """Test searching sessions"""
        session1 = Session(
            id="search-1",
            name="python-session",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )
        session1.add_message("user", "Write Python code")

        session2 = Session(
            id="search-2",
            name="javascript-session",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )
        session2.add_message("user", "Write JavaScript code")

        self.storage.save_session(session1)
        self.storage.save_session(session2)

        results = self.storage.search_sessions("python")
        assert len(results) >= 1
        assert any(s["id"] == "search-1" for s in results)


class TestSessionManager:
    """Test Session Manager"""

    def setup_method(self):
        """Setup for each test"""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "test.db"
        storage = SessionStorage(str(db_path))
        self.manager = SessionManager(storage=storage)

    def test_create_session(self):
        """Test creating a session"""
        session = self.manager.create_session(name="test", provider="ollama", model="llama2")

        assert session is not None
        assert session.name == "test"
        assert session.provider == "ollama"
        assert session.model == "llama2"

    def test_load_session(self):
        """Test loading a session"""
        created = self.manager.create_session(name="load-test")
        loaded = self.manager.load_session(created.id)

        assert loaded is not None
        assert loaded.id == created.id

    def test_set_current_session(self):
        """Test setting current session"""
        session = self.manager.create_session(name="current")
        self.manager.set_current_session(session)

        current = self.manager.get_current_session()
        assert current is not None
        assert current.id == session.id

    def test_add_message(self):
        """Test adding message to session"""
        session = self.manager.create_session(name="msg-test")
        self.manager.set_current_session(session)

        self.manager.add_message("user", "Hello", tokens=5, auto_save=False)

        assert len(session.messages) == 1
        assert session.total_tokens == 5

    def test_get_session_stats(self):
        """Test getting session statistics"""
        session = self.manager.create_session(name="stats-test")
        session.add_message("user", "Hello", tokens=5)
        session.add_message("assistant", "Hi", tokens=3)
        self.manager.save_session(session)

        stats = self.manager.get_session_stats(session.id)

        assert stats["total_messages"] == 2
        assert stats["user_messages"] == 1
        assert stats["assistant_messages"] == 1
        assert stats["total_tokens"] == 8
