"""
Memory Storage

SQLite + Vector storage for memories.
"""

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

from xandai.memory.memory_manager import Memory, MemoryType


class MemoryStorage:
    """
    Memory Storage Backend

    Uses SQLite for metadata and optional vector storage.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize memory storage

        Args:
            db_path: Database path (default: ~/.xandai/memory.db)
        """
        if db_path:
            self.db_path = Path(db_path)
        else:
            home = Path.home()
            xandai_dir = home / ".xandai"
            xandai_dir.mkdir(exist_ok=True)
            self.db_path = xandai_dir / "memory.db"

        self._init_database()

    def _init_database(self):
        """Initialize database schema"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Memories table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    accessed_at TEXT NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    importance REAL DEFAULT 0.5,
                    tags TEXT,
                    metadata TEXT,
                    embedding BLOB
                )
            """
            )

            # Indexes
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_memory_type
                ON memories(memory_type)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_importance
                ON memories(importance DESC)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_accessed
                ON memories(accessed_at DESC)
            """
            )

            # Full-text search
            cursor.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts
                USING fts5(content, tags)
            """
            )

            conn.commit()

    @contextmanager
    def _get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def save_memory(self, memory: Memory, embedding: Optional[List[float]] = None):
        """Save or update a memory"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Serialize embedding
            embedding_blob = None
            if embedding:
                import struct

                embedding_blob = struct.pack(f"{len(embedding)}f", *embedding)

            cursor.execute(
                """
                INSERT OR REPLACE INTO memories
                (id, content, memory_type, created_at, accessed_at,
                 access_count, importance, tags, metadata, embedding)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    memory.id,
                    memory.content,
                    memory.memory_type.value,
                    memory.created_at,
                    memory.accessed_at,
                    memory.access_count,
                    memory.importance,
                    json.dumps(memory.tags),
                    json.dumps(memory.metadata),
                    embedding_blob,
                ),
            )

            # Update FTS
            cursor.execute(
                """
                INSERT OR REPLACE INTO memories_fts (rowid, content, tags)
                VALUES (
                    (SELECT rowid FROM memories WHERE id = ?),
                    ?, ?
                )
            """,
                (memory.id, memory.content, " ".join(memory.tags)),
            )

            conn.commit()

    def get_memory(self, memory_id: str) -> Optional[Memory]:
        """Get a memory by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
            row = cursor.fetchone()

            if not row:
                return None

            return Memory(
                id=row["id"],
                content=row["content"],
                memory_type=MemoryType(row["memory_type"]),
                created_at=row["created_at"],
                accessed_at=row["accessed_at"],
                access_count=row["access_count"],
                importance=row["importance"],
                tags=json.loads(row["tags"]) if row["tags"] else [],
                metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            )

    def update_memory(self, memory: Memory):
        """Update memory metadata"""
        self.save_memory(memory, None)  # Don't update embedding

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            deleted = cursor.rowcount > 0

            conn.commit()
            return deleted

    def search_by_keywords(
        self,
        query: str,
        limit: int = 5,
        memory_type: Optional[MemoryType] = None,
        min_importance: float = 0.0,
    ) -> List[Memory]:
        """Search memories by keywords"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Build query
            sql = """
                SELECT m.* FROM memories m
                JOIN memories_fts fts ON m.rowid = fts.rowid
                WHERE memories_fts MATCH ?
                AND m.importance >= ?
            """

            params = [query, min_importance]

            if memory_type:
                sql += " AND m.memory_type = ?"
                params.append(memory_type.value)

            sql += " ORDER BY m.importance DESC, m.accessed_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(sql, params)

            memories = []
            for row in cursor.fetchall():
                memories.append(
                    Memory(
                        id=row["id"],
                        content=row["content"],
                        memory_type=MemoryType(row["memory_type"]),
                        created_at=row["created_at"],
                        accessed_at=row["accessed_at"],
                        access_count=row["access_count"],
                        importance=row["importance"],
                        tags=json.loads(row["tags"]) if row["tags"] else [],
                        metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                    )
                )

            return memories

    def search_by_embedding(
        self,
        query_embedding: List[float],
        limit: int = 5,
        memory_type: Optional[MemoryType] = None,
        min_importance: float = 0.0,
    ) -> List[Memory]:
        """Search memories by semantic similarity"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get all memories with embeddings
            sql = """
                SELECT * FROM memories
                WHERE embedding IS NOT NULL
                AND importance >= ?
            """

            params = [min_importance]

            if memory_type:
                sql += " AND memory_type = ?"
                params.append(memory_type.value)

            cursor.execute(sql, params)

            # Compute similarities
            import struct

            import numpy as np

            query_vec = np.array(query_embedding)
            scored_memories = []

            for row in cursor.fetchall():
                # Deserialize embedding
                embedding_blob = row["embedding"]
                embedding_size = len(embedding_blob) // 4
                embedding = struct.unpack(f"{embedding_size}f", embedding_blob)
                embedding_vec = np.array(embedding)

                # Cosine similarity
                similarity = np.dot(query_vec, embedding_vec) / (
                    np.linalg.norm(query_vec) * np.linalg.norm(embedding_vec)
                )

                memory = Memory(
                    id=row["id"],
                    content=row["content"],
                    memory_type=MemoryType(row["memory_type"]),
                    created_at=row["created_at"],
                    accessed_at=row["accessed_at"],
                    access_count=row["access_count"],
                    importance=row["importance"],
                    tags=json.loads(row["tags"]) if row["tags"] else [],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                )

                scored_memories.append((similarity, memory))

            # Sort by similarity
            scored_memories.sort(reverse=True, key=lambda x: x[0])

            # Return top memories
            return [mem for _, mem in scored_memories[:limit]]

    def list_memories(
        self, memory_type: Optional[MemoryType] = None, limit: Optional[int] = None
    ) -> List[Memory]:
        """List all memories"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            sql = "SELECT * FROM memories"
            params = []

            if memory_type:
                sql += " WHERE memory_type = ?"
                params.append(memory_type.value)

            sql += " ORDER BY importance DESC, accessed_at DESC"

            if limit:
                sql += " LIMIT ?"
                params.append(limit)

            cursor.execute(sql, params)

            memories = []
            for row in cursor.fetchall():
                memories.append(
                    Memory(
                        id=row["id"],
                        content=row["content"],
                        memory_type=MemoryType(row["memory_type"]),
                        created_at=row["created_at"],
                        accessed_at=row["accessed_at"],
                        access_count=row["access_count"],
                        importance=row["importance"],
                        tags=json.loads(row["tags"]) if row["tags"] else [],
                        metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                    )
                )

            return memories

    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Total memories
            cursor.execute("SELECT COUNT(*) as count FROM memories")
            total = cursor.fetchone()["count"]

            # By type
            cursor.execute(
                """
                SELECT memory_type, COUNT(*) as count
                FROM memories
                GROUP BY memory_type
            """
            )
            by_type = {row["memory_type"]: row["count"] for row in cursor.fetchall()}

            # Average importance
            cursor.execute("SELECT AVG(importance) as avg FROM memories")
            avg_importance = cursor.fetchone()["avg"] or 0

            return {
                "total_memories": total,
                "by_type": by_type,
                "average_importance": avg_importance,
                "database_path": str(self.db_path),
            }
