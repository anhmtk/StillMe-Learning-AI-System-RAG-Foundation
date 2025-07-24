"""
LayeredMemory_v1.py
-------------------
Memory system with short/mid/long-term layers with intelligent forgetting.
"""

import sqlite3
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
from abc import ABC, abstractmethod
import pickle
from cryptography.fernet import Fernet
import warnings

# Constants
SHORT_TERM_CAPACITY = 1000
MID_TERM_COMPRESSION_THRESHOLD = 0.7
MEMORY_ENCRYPTION_KEY = Fernet.generate_key()

# -------------------- DATA STRUCTURES --------------------
@dataclass
class MemoryItem:
    content: str
    priority: float
    timestamp: datetime
    last_accessed: datetime
    metadata: dict

# -------------------- BASE LAYER --------------------
class BaseMemoryLayer(ABC):
    """Abstract base class for memory layers"""
    @abstractmethod
    def add(self, item: MemoryItem):
        pass
    
    @abstractmethod
    def search(self, query: str) -> List[MemoryItem]:
        pass
    
    @abstractmethod
    def compress(self) -> List[MemoryItem]:
        pass

# -------------------- SHORT-TERM MEMORY --------------------
class ShortTermMemory(BaseMemoryLayer):
    """Ring buffer implementation for short-term memory"""
    def __init__(self, max_size=SHORT_TERM_CAPACITY):
        self.buffer = []
        self.max_size = max_size
        self.pointer = 0
        self._setup_encryption()

    def _setup_encryption(self):
        self.cipher = Fernet(MEMORY_ENCRYPTION_KEY)

    def _encrypt(self, data: str) -> bytes:
        return self.cipher.encrypt(data.encode())

    def _decrypt(self, encrypted: bytes) -> str:
        return self.cipher.decrypt(encrypted).decode()

    def add(self, item: MemoryItem):
        # Auto-prune expired items
        self._prune_expired()
        
        if len(self.buffer) >= self.max_size:
            self.buffer[self.pointer] = item
            self.pointer = (self.pointer + 1) % self.max_size
        else:
            self.buffer.append(item)
        
        # Encrypt sensitive data
        item.content = self._encrypt(item.content)

    def search(self, query: str) -> List[MemoryItem]:
        results = []
        for item in self.buffer:
            decrypted_content = self._decrypt(item.content)
            if query.lower() in decrypted_content.lower():
                item.last_accessed = datetime.now()
                results.append(item)
        return sorted(results, key=lambda x: x.priority, reverse=True)

    def _prune_expired(self, ttl_hours=24):
        cutoff = datetime.now() - timedelta(hours=ttl_hours)
        self.buffer = [item for item in self.buffer if item.timestamp > cutoff]

    def compress(self) -> List[MemoryItem]:
        # Only compress high-priority items
        high_priority = [item for item in self.buffer if item.priority >= 0.7]
        self.buffer = [item for item in self.buffer if item.priority < 0.7]
        return high_priority

# -------------------- MID-TERM MEMORY --------------------
class MidTermMemory(BaseMemoryLayer):
    """Vector-based memory with semantic search"""
    def __init__(self):
        self.memories = []
        self.embedding_model = self._init_embedding_model()
        self.access_counts = {}
    
    def _init_embedding_model(self):
        # Placeholder for actual embedding model
        class DummyEmbedder:
            def embed(self, text):
                return np.random.rand(128)
        return DummyEmbedder()
    
    def add(self, item: MemoryItem):
        item.embedding = self.embedding_model.embed(item.content)
        self.memories.append(item)
        self.access_counts[id(item)] = 0
        
    def search(self, query: str) -> List[MemoryItem]:
        query_embed = self.embedding_model.embed(query)
        similarities = []
        
        for item in self.memories:
            sim = np.dot(query_embed, item.embedding)
            similarities.append((sim, item))
        
        # Update access counts
        for _, item in sorted(similarities, reverse=True)[:5]:
            self.access_counts[id(item)] += 1
            
        return [item for _, item in sorted(similarities, reverse=True)]

    def compress(self) -> List[MemoryItem]:
        # Move rarely accessed items to long-term
        if not self.access_counts:
            return []
        avg_access = np.mean(list(self.access_counts.values()))
        to_compress = [item for item in self.memories
                      if self.access_counts.get(id(item), 0) < avg_access * 0.5]
        
        self.memories = [item for item in self.memories
                        if item not in to_compress]
        return to_compress

# -------------------- LONG-TERM MEMORY --------------------
class LongTermMemory:
    """SQLite-backed persistent memory with full-text search (FTS5)"""
    def __init__(self, db_path=":memory:"):
        self.conn = sqlite3.connect(db_path)
        self._init_db()

    def _init_db(self):
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY,
            content TEXT,
            priority REAL,
            timestamp DATETIME,
            metadata BLOB,
            embedding BLOB
        )
        """)
        self.conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts 
        USING fts5(content, tokenize='unicode61')
        """)
        self.conn.commit()

    def add(self, items: List[MemoryItem]):
        """Add multiple memory items to long-term storage"""
        try:
            for item in items:
                # Insert into main table
                self.conn.execute(
                    "INSERT OR REPLACE INTO memories (id, content, priority, timestamp, metadata, embedding) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        id(item),
                        item.content,
                        item.priority,
                        item.timestamp.isoformat(),
                        pickle.dumps(item.metadata),
                        pickle.dumps(getattr(item, 'embedding', None))
                    )
                )
                # Insert into FTS index
                self.conn.execute(
                    "INSERT INTO memories_fts (rowid, content) VALUES (last_insert_rowid(), ?)",
                    (item.content,)
                )
            self.conn.commit()
        except Exception as e:
            logging.error(f"[LongTermMemory] Add failed: {e}")
            self.conn.rollback()

    def search(self, query: str) -> List[MemoryItem]:
        """
        Hybrid search: FTS + semantic fallback.
        If FTS fails, returns all memories containing the query.
        """
        results = []
        try:
            # Normalize query for special characters
            norm_query = query.replace('"', '""').strip()
            fts_results = self.conn.execute(
                "SELECT rowid FROM memories_fts WHERE content MATCH ?",
                (norm_query,)
            ).fetchall()

            # If no FTS matches, fallback to LIKE search
            if not fts_results:
                fts_results = self.conn.execute(
                    "SELECT id FROM memories WHERE content LIKE ?",
                    (f"%{query}%",)
                ).fetchall()

            # Get all matching rows
            all_ids = [r[0] for r in fts_results]
            if not all_ids:
                return []

            placeholders = ",".join("?" for _ in all_ids)
            rows = self.conn.execute(
                f"SELECT * FROM memories WHERE id IN ({placeholders})",
                all_ids
            ).fetchall()

            results = [self._row_to_item(row) for row in rows]
        except Exception as e:
            logging.error(f"[LongTermMemory] Search failed: {e}")

        return results

    def _row_to_item(self, row):
        """Convert DB row to MemoryItem"""
        return MemoryItem(
            content=row[1],
            priority=row[2],
            timestamp=datetime.fromisoformat(row[3]),
            last_accessed=datetime.now(),
            metadata=pickle.loads(row[4])
        )

# -------------------- LAYERED MEMORY --------------------
class LayeredMemoryV1:
    """Orchestrates all memory layers"""
    def __init__(self):
        self.short_term = ShortTermMemory()
        self.mid_term = MidTermMemory()
        self.long_term = LongTermMemory()
        self.logger = self._setup_logging()
    
    def _setup_logging(self):
        logger = logging.getLogger("LayeredMemory")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
    
    def add_memory(self, content: str, priority: float = 0.5, 
                  auto_compress: bool = True, metadata: dict = None):
        """Add memory with automatic layer selection"""
        item = MemoryItem(
            content=content,
            priority=priority,
            timestamp=datetime.now(),
            last_accessed=datetime.now(),
            metadata=metadata or {})
        
        if priority > 0.8:  # High priority -> long-term
            self.long_term.add([item])
        else:
            self.short_term.add(item)
            
        if auto_compress:
            self._auto_compress()
    
    def search(self, query: str, time_range: Tuple[datetime, datetime] = None
              ) -> List[MemoryItem]:
        """Search across all layers with optional time filter"""
        results = []
        results.extend(self.short_term.search(query))
        results.extend(self.mid_term.search(query))
        results.extend(self.long_term.search(query))
        
        if time_range:
            start, end = time_range
            results = [r for r in results 
                      if start <= r.timestamp <= end]
        
        return sorted(results, key=lambda x: x.priority, reverse=True)
    
    def _auto_compress(self, force=False):
        """Move memories between layers based on rules"""
        # Short-term -> Mid-term
        if force or len(self.short_term.buffer) > SHORT_TERM_CAPACITY * MID_TERM_COMPRESSION_THRESHOLD:
            compressed = self.short_term.compress()
            for item in compressed:
                self.mid_term.add(item)
            self.logger.info(f"Compressed {len(compressed)} items to mid-term")

        # Mid-term -> Long-term
        if force or len(self.mid_term.memories) > 1000:  # Arbitrary threshold
            compressed = self.mid_term.compress()
            self.long_term.add(compressed)
            self.logger.info(f"Compressed {len(compressed)} items to long-term")

# -------------------- MAIN --------------------
if __name__ == "__main__":
    memory = LayeredMemoryV1()
    memory.add_memory("User prefers dark coffee", 0.6)
    memory.add_memory("User is allergic to peanuts", 0.9)
    results = memory.search("coffee")
    print(f"Found {len(results)} relevant memories")
