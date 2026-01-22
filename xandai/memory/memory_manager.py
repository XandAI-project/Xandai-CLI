"""
Memory Manager

Long-term memory system with semantic search.
"""

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class MemoryType(Enum):
    """Types of memory"""

    FACT = "fact"  # Factual information
    CONVERSATION = "conversation"  # Conversation snippets
    CODE = "code"  # Code snippets
    DOCUMENT = "document"  # Document references
    PREFERENCE = "preference"  # User preferences
    TASK = "task"  # Task history


@dataclass
class Memory:
    """Memory entry"""

    id: str
    content: str
    memory_type: MemoryType
    created_at: str
    accessed_at: str
    access_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    importance: float = 0.5  # 0.0 to 1.0

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        data = asdict(self)
        data["memory_type"] = self.memory_type.value
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Memory":
        """Create from dictionary"""
        data["memory_type"] = MemoryType(data["memory_type"])
        return cls(**data)


class MemoryManager:
    """
    Memory Manager

    Manages long-term memory with semantic search.
    """

    def __init__(self, storage=None):
        """
        Initialize memory manager

        Args:
            storage: Memory storage backend
        """
        from xandai.memory.memory_storage import MemoryStorage

        self.storage = storage or MemoryStorage()
        self._embeddings_available = self._check_embeddings()

    def _check_embeddings(self) -> bool:
        """Check if embeddings are available"""
        try:
            from sentence_transformers import SentenceTransformer

            return True
        except ImportError:
            return False

    def store(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.FACT,
        importance: float = 0.5,
        tags: Optional[List[str]] = None,
        **metadata,
    ) -> Memory:
        """
        Store a memory

        Args:
            content: Memory content
            memory_type: Type of memory
            importance: Importance score (0.0 to 1.0)
            tags: Optional tags
            **metadata: Additional metadata

        Returns:
            Created memory
        """
        memory_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        memory = Memory(
            id=memory_id,
            content=content,
            memory_type=memory_type,
            created_at=now,
            accessed_at=now,
            importance=importance,
            tags=tags or [],
            metadata=metadata,
        )

        # Generate embedding if available
        if self._embeddings_available:
            embedding = self._generate_embedding(content)
            self.storage.save_memory(memory, embedding)
        else:
            self.storage.save_memory(memory, None)

        return memory

    def recall(
        self,
        query: str,
        limit: int = 5,
        memory_type: Optional[MemoryType] = None,
        min_importance: float = 0.0,
    ) -> List[Memory]:
        """
        Recall memories by semantic search

        Args:
            query: Search query
            limit: Maximum memories to return
            memory_type: Filter by type
            min_importance: Minimum importance

        Returns:
            List of relevant memories
        """
        if self._embeddings_available:
            # Semantic search
            query_embedding = self._generate_embedding(query)
            memories = self.storage.search_by_embedding(
                query_embedding, limit=limit, memory_type=memory_type, min_importance=min_importance
            )
        else:
            # Keyword search fallback
            memories = self.storage.search_by_keywords(
                query, limit=limit, memory_type=memory_type, min_importance=min_importance
            )

        # Update access info
        for memory in memories:
            memory.access_count += 1
            memory.accessed_at = datetime.now().isoformat()
            self.storage.update_memory(memory)

        return memories

    def get(self, memory_id: str) -> Optional[Memory]:
        """
        Get a specific memory

        Args:
            memory_id: Memory ID

        Returns:
            Memory or None
        """
        return self.storage.get_memory(memory_id)

    def forget(self, memory_id: str) -> bool:
        """
        Delete a memory

        Args:
            memory_id: Memory ID

        Returns:
            True if deleted
        """
        return self.storage.delete_memory(memory_id)

    def update(
        self,
        memory_id: str,
        content: Optional[str] = None,
        importance: Optional[float] = None,
        tags: Optional[List[str]] = None,
        **metadata,
    ) -> Optional[Memory]:
        """
        Update a memory

        Args:
            memory_id: Memory ID
            content: New content
            importance: New importance
            tags: New tags
            **metadata: New metadata

        Returns:
            Updated memory or None
        """
        memory = self.get(memory_id)
        if not memory:
            return None

        if content:
            memory.content = content
            # Regenerate embedding if content changed
            if self._embeddings_available:
                embedding = self._generate_embedding(content)
                self.storage.save_memory(memory, embedding)

        if importance is not None:
            memory.importance = importance

        if tags is not None:
            memory.tags = tags

        if metadata:
            memory.metadata.update(metadata)

        self.storage.update_memory(memory)
        return memory

    def list_memories(
        self, memory_type: Optional[MemoryType] = None, limit: Optional[int] = None
    ) -> List[Memory]:
        """
        List all memories

        Args:
            memory_type: Filter by type
            limit: Maximum memories

        Returns:
            List of memories
        """
        return self.storage.list_memories(memory_type, limit)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get memory statistics

        Returns:
            Statistics dict
        """
        return self.storage.get_stats()

    def consolidate(self, threshold: float = 0.9):
        """
        Consolidate similar memories

        Args:
            threshold: Similarity threshold
        """
        if not self._embeddings_available:
            return

        # Get all memories
        memories = self.list_memories()

        # Find and merge similar ones
        merged_count = 0
        for i, mem1 in enumerate(memories):
            for mem2 in memories[i + 1 :]:
                if mem1.memory_type == mem2.memory_type:
                    similarity = self._compute_similarity(mem1.content, mem2.content)

                    if similarity > threshold:
                        # Merge memories
                        merged_content = f"{mem1.content}\n{mem2.content}"
                        self.update(
                            mem1.id,
                            content=merged_content,
                            importance=max(mem1.importance, mem2.importance),
                        )
                        self.forget(mem2.id)
                        merged_count += 1

        return merged_count

    def prune(self, max_memories: int = 1000, keep_important: bool = True):
        """
        Prune old/unimportant memories

        Args:
            max_memories: Maximum memories to keep
            keep_important: Always keep important memories
        """
        memories = self.list_memories()

        if len(memories) <= max_memories:
            return 0

        # Sort by importance and access
        memories.sort(key=lambda m: (m.importance, m.access_count), reverse=True)

        # Delete excess memories
        deleted = 0
        for memory in memories[max_memories:]:
            if not keep_important or memory.importance < 0.7:
                self.forget(memory.id)
                deleted += 1

        return deleted

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        try:
            from sentence_transformers import SentenceTransformer

            if not hasattr(self, "_model"):
                self._model = SentenceTransformer("all-MiniLM-L6-v2")

            embedding = self._model.encode(text)
            return embedding.tolist()
        except:
            return []

    def _compute_similarity(self, text1: str, text2: str) -> float:
        """Compute similarity between two texts"""
        try:
            emb1 = self._generate_embedding(text1)
            emb2 = self._generate_embedding(text2)

            # Cosine similarity
            import numpy as np

            emb1 = np.array(emb1)
            emb2 = np.array(emb2)

            similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))

            return float(similarity)
        except:
            return 0.0
