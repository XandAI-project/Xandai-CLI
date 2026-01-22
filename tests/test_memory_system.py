"""
Tests for Memory System
"""

import tempfile
from pathlib import Path

import pytest

from xandai.memory import Memory, MemoryManager, MemoryType
from xandai.memory.memory_storage import MemoryStorage


class TestMemory:
    """Test Memory class"""

    def test_create_memory(self):
        """Test creating a memory"""
        memory = Memory(
            id="test-id",
            content="Test memory",
            memory_type=MemoryType.FACT,
            created_at="2024-01-01T00:00:00",
            accessed_at="2024-01-01T00:00:00",
        )
        assert memory.id == "test-id"
        assert memory.content == "Test memory"
        assert memory.memory_type == MemoryType.FACT

    def test_memory_to_dict(self):
        """Test converting memory to dict"""
        memory = Memory(
            id="test",
            content="Test",
            memory_type=MemoryType.CODE,
            created_at="2024-01-01T00:00:00",
            accessed_at="2024-01-01T00:00:00",
        )
        d = memory.to_dict()
        assert d["memory_type"] == "code"

    def test_memory_from_dict(self):
        """Test creating memory from dict"""
        d = {
            "id": "test",
            "content": "Test content",
            "memory_type": "fact",
            "created_at": "2024-01-01T00:00:00",
            "accessed_at": "2024-01-01T00:00:00",
            "access_count": 0,
            "importance": 0.5,
            "tags": [],
            "metadata": {},
        }
        memory = Memory.from_dict(d)
        assert memory.memory_type == MemoryType.FACT


class TestMemoryStorage:
    """Test Memory Storage"""

    def setup_method(self):
        """Setup for each test"""
        temp_dir = tempfile.mkdtemp()
        self.db_path = Path(temp_dir) / "test_memory.db"
        self.storage = MemoryStorage(str(self.db_path))

    def test_save_and_get_memory(self):
        """Test saving and retrieving memory"""
        memory = Memory(
            id="test-123",
            content="Python is a programming language",
            memory_type=MemoryType.FACT,
            created_at="2024-01-01T00:00:00",
            accessed_at="2024-01-01T00:00:00",
            importance=0.8,
            tags=["python", "programming"],
        )

        self.storage.save_memory(memory)
        retrieved = self.storage.get_memory("test-123")

        assert retrieved is not None
        assert retrieved.content == "Python is a programming language"
        assert retrieved.importance == 0.8
        assert "python" in retrieved.tags

    def test_delete_memory(self):
        """Test deleting a memory"""
        memory = Memory(
            id="delete-me",
            content="Test",
            memory_type=MemoryType.FACT,
            created_at="2024-01-01T00:00:00",
            accessed_at="2024-01-01T00:00:00",
        )

        self.storage.save_memory(memory)
        deleted = self.storage.delete_memory("delete-me")

        assert deleted is True
        assert self.storage.get_memory("delete-me") is None

    def test_list_memories(self):
        """Test listing memories"""
        for i in range(3):
            memory = Memory(
                id=f"mem-{i}",
                content=f"Memory {i}",
                memory_type=MemoryType.FACT,
                created_at="2024-01-01T00:00:00",
                accessed_at="2024-01-01T00:00:00",
                importance=0.5 + i * 0.1,
            )
            self.storage.save_memory(memory)

        memories = self.storage.list_memories()
        assert len(memories) == 3

        # Should be sorted by importance
        assert memories[0].importance >= memories[1].importance

    def test_search_by_keywords(self):
        """Test keyword search"""
        memory1 = Memory(
            id="search-1",
            content="Python programming language",
            memory_type=MemoryType.FACT,
            created_at="2024-01-01T00:00:00",
            accessed_at="2024-01-01T00:00:00",
        )

        memory2 = Memory(
            id="search-2",
            content="JavaScript web development",
            memory_type=MemoryType.FACT,
            created_at="2024-01-01T00:00:00",
            accessed_at="2024-01-01T00:00:00",
        )

        self.storage.save_memory(memory1)
        self.storage.save_memory(memory2)

        results = self.storage.search_by_keywords("Python")
        assert len(results) >= 1
        assert any("Python" in m.content for m in results)

    def test_get_stats(self):
        """Test getting statistics"""
        memory = Memory(
            id="stats-test",
            content="Test",
            memory_type=MemoryType.FACT,
            created_at="2024-01-01T00:00:00",
            accessed_at="2024-01-01T00:00:00",
        )

        self.storage.save_memory(memory)
        stats = self.storage.get_stats()

        assert "total_memories" in stats
        assert stats["total_memories"] >= 1


class TestMemoryManager:
    """Test Memory Manager"""

    def setup_method(self):
        """Setup for each test"""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "test_memory.db"
        storage = MemoryStorage(str(db_path))
        self.manager = MemoryManager(storage=storage)

    def test_store_memory(self):
        """Test storing a memory"""
        memory = self.manager.store(
            "Python is great for AI",
            memory_type=MemoryType.FACT,
            importance=0.9,
            tags=["python", "ai"],
        )

        assert memory is not None
        assert memory.content == "Python is great for AI"
        assert memory.importance == 0.9

    def test_recall_memory(self):
        """Test recalling memories"""
        # Store some memories
        self.manager.store("Python programming", MemoryType.FACT, tags=["python"])
        self.manager.store("JavaScript coding", MemoryType.FACT, tags=["javascript"])

        # Recall
        memories = self.manager.recall("Python", limit=5)

        assert len(memories) > 0

    def test_get_memory(self):
        """Test getting specific memory"""
        stored = self.manager.store("Test memory", MemoryType.FACT)
        retrieved = self.manager.get(stored.id)

        assert retrieved is not None
        assert retrieved.id == stored.id

    def test_forget_memory(self):
        """Test forgetting a memory"""
        memory = self.manager.store("Forget me", MemoryType.FACT)
        deleted = self.manager.forget(memory.id)

        assert deleted is True
        assert self.manager.get(memory.id) is None

    def test_update_memory(self):
        """Test updating a memory"""
        memory = self.manager.store("Original content", MemoryType.FACT, importance=0.5)

        updated = self.manager.update(memory.id, content="Updated content", importance=0.9)

        assert updated is not None
        assert updated.content == "Updated content"
        assert updated.importance == 0.9

    def test_list_memories(self):
        """Test listing memories"""
        self.manager.store("Fact 1", MemoryType.FACT)
        self.manager.store("Code 1", MemoryType.CODE)

        all_memories = self.manager.list_memories()
        assert len(all_memories) >= 2

        facts_only = self.manager.list_memories(memory_type=MemoryType.FACT)
        assert all(m.memory_type == MemoryType.FACT for m in facts_only)

    def test_get_stats(self):
        """Test getting statistics"""
        self.manager.store("Test", MemoryType.FACT)
        stats = self.manager.get_stats()

        assert "total_memories" in stats
        assert stats["total_memories"] >= 1

    def test_prune_memories(self):
        """Test pruning old memories"""
        # Store many memories
        for i in range(15):
            self.manager.store(f"Memory {i}", MemoryType.FACT, importance=0.1 if i < 10 else 0.9)

        # Prune keeping only 10
        deleted = self.manager.prune(max_memories=10, keep_important=True)

        assert deleted > 0
        remaining = self.manager.list_memories()
        assert len(remaining) <= 10
