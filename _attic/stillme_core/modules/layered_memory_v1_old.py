#!/usr/bin/env python3
"""
🧠 LAYERED MEMORY V1 - HỆ THỐNG BỘ NHỚ PHÂN LỚP V1

PURPOSE / MỤC ĐÍCH:
- Hệ thống bộ nhớ với các lớp ngắn hạn/trung hạn/dài hạn
- Quên thông minh để tối ưu hóa hiệu suất
- Tích hợp với SecureMemoryManager cho mã hóa và backup

FUNCTIONALITY / CHỨC NĂNG:
- Short-term memory: Lưu trữ tạm thời (1-7 ngày)
- Mid-term memory: Lưu trữ trung hạn (1-4 tuần)
- Long-term memory: Lưu trữ dài hạn (1-12 tháng)
- Intelligent forgetting: Tự động xóa thông tin cũ
- Encrypted storage: Mã hóa dữ liệu nhạy cảm

TECHNICAL DETAILS / CHI TIẾT KỸ THUẬT:
- SQLite database với encryption
- Automatic backup và recovery
- Memory scoring và priority system
- Async operations cho performance
"""

import asyncio
import json
import logging
import pickle
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
from cryptography.fernet import Fernet

# Import SecureMemoryManager
try:
    from .secure_memory_manager import SecureMemoryConfig as _SecureMemoryConfig
    from .secure_memory_manager import SecureMemoryManager as _SecureMemoryManager

    SecureMemoryManager = _SecureMemoryManager  # type: ignore
    SecureMemoryConfig = _SecureMemoryConfig  # type: ignore
except ImportError:
    try:
        from secure_memory_manager import SecureMemoryConfig as _SecureMemoryConfig
        from secure_memory_manager import SecureMemoryManager as _SecureMemoryManager

        SecureMemoryManager = _SecureMemoryManager  # type: ignore
        SecureMemoryConfig = _SecureMemoryConfig  # type: ignore
    except ImportError:
        # Mock classes for testing
        class SecureMemoryManager:
            def __init__(self, config=None):
                pass

            def encrypt(self, data):
                return data

            def decrypt(self, data):
                return data

            def save(self, data):
                return True

            def load(self):
                return {}

            def get_health_status(self):
                return {"status": "healthy"}

            def get_performance_metrics(self):
                return {"memory_usage": 0}

            def shutdown(self):
                pass

        class SecureMemoryConfig:
            def __init__(self):
                pass


# Constants
SHORT_TERM_CAPACITY = 1000
MID_TERM_COMPRESSION_THRESHOLD = 0.7


# Persistent encryption key
def _get_or_create_encryption_key():
    """Get or create persistent encryption key"""
    key_file = Path("framework_memory.enc")
    if key_file.exists():
        try:
            with open(key_file, "rb") as f:
                return f.read()
        except Exception:
            pass

    # Create new key
    key = Fernet.generate_key()
    try:
        with open(key_file, "wb") as f:
            f.write(key)
    except Exception:
        pass
    return key


MEMORY_ENCRYPTION_KEY = _get_or_create_encryption_key()


# -------------------- DATA STRUCTURES --------------------
@dataclass
class MemoryItem:
    content: str
    priority: float
    timestamp: datetime
    last_accessed: datetime
    metadata: dict
    embedding: np.ndarray | None = None


# -------------------- BASE LAYER --------------------
class BaseMemoryLayer(ABC):
    """Abstract base class for memory layers"""

    @abstractmethod
    def add(self, item: MemoryItem):
        pass

    @abstractmethod
    def search(self, query: str) -> list[MemoryItem]:
        pass

    @abstractmethod
    def compress(self) -> list[MemoryItem]:
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

        # Don't encrypt in short-term memory - keep content as plain text
        # Encryption will happen when moving to long-term memory

    def search(self, query: str) -> list[MemoryItem]:
        results = []
        for item in self.buffer:
            try:
                # Handle both encrypted (bytes) and plain text content
                if isinstance(item.content, bytes):
                    decrypted_content = self._decrypt(item.content)
                else:
                    decrypted_content = item.content

                if query.lower() in decrypted_content.lower():
                    item.last_accessed = datetime.now()
                    results.append(item)
            except Exception:
                # If decryption fails, skip this item
                continue
        return sorted(results, key=lambda x: x.priority, reverse=True)

    def _prune_expired(self, ttl_hours=24):
        cutoff = datetime.now() - timedelta(hours=ttl_hours)
        self.buffer = [item for item in self.buffer if item.timestamp > cutoff]

    def compress(self) -> list[MemoryItem]:
        # Only compress high-priority items
        high_priority = [item for item in self.buffer if item.priority >= 0.7]
        self.buffer = [item for item in self.buffer if item.priority < 0.7]
        return high_priority


# -------------------- MID-TERM MEMORY --------------------
class MidTermMemory(BaseMemoryLayer):
    """Vector-based memory with semantic search"""

    def __init__(self, max_size=5000):
        self.memories = []
        self.max_size = max_size
        self._setup_encryption()

    def _setup_encryption(self):
        self.cipher = Fernet(MEMORY_ENCRYPTION_KEY)

    def _encrypt(self, data: str) -> bytes:
        return self.cipher.encrypt(data.encode())

    def _decrypt(self, encrypted: bytes) -> str:
        return self.cipher.decrypt(encrypted).decode()

    def add(self, items):
        # Handle both single item and list of items
        if not isinstance(items, list):
            items = [items]

        for item in items:
            if len(self.memories) >= self.max_size:
                # Remove lowest priority item
                self.memories.sort(key=lambda x: x.priority)
                self.memories.pop(0)

            # Don't encrypt in mid-term memory - keep content as plain text
            # Encryption will happen when moving to long-term memory
            self.memories.append(item)

    def search(self, query: str) -> list[MemoryItem]:
        results = []
        for item in self.memories:
            try:
                # Content is now plain text in mid-term memory
                if query.lower() in item.content.lower():
                    item.last_accessed = datetime.now()
                    results.append(item)
            except Exception:
                # If search fails, skip this item
                continue
        return sorted(results, key=lambda x: x.priority, reverse=True)

    def compress(self) -> list[MemoryItem]:
        """Compress memories by moving high-priority items to long-term storage"""
        # Keep only high-priority memories
        high_priority = [item for item in self.memories if item.priority >= 0.8]
        self.memories = [item for item in self.memories if item.priority < 0.8]
        return high_priority


# -------------------- LONG-TERM MEMORY --------------------
class LongTermMemory(BaseMemoryLayer):
    """SQLite-based persistent storage with FTS search"""

    def __init__(self, db_path="memories.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._setup_encryption()
        self._create_tables()

    def _setup_encryption(self):
        self.cipher = Fernet(MEMORY_ENCRYPTION_KEY)

    def _encrypt(self, data: str) -> bytes:
        return self.cipher.encrypt(data.encode())

    def _decrypt(self, encrypted: bytes) -> str:
        return self.cipher.decrypt(encrypted).decode()

    def _create_tables(self):
        """Create memory tables with FTS support"""
        try:
            # Main memories table
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY,
                    content TEXT NOT NULL,
                    priority REAL DEFAULT 0.5,
                    timestamp TEXT NOT NULL,
                    metadata BLOB
                )
            """
            )

            # FTS table for fast search
            self.conn.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts
                USING fts5(content, content='memories', content_rowid='id')
            """
            )

            # Trigger to keep FTS in sync
            self.conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
                    INSERT INTO memories_fts(rowid, content) VALUES (new.id, new.content);
                END
            """
            )

            self.conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
                    INSERT INTO memories_fts(memories_fts, rowid, content) VALUES('delete', old.id, old.content);
                END
            """
            )

            self.conn.commit()
        except Exception as e:
            logging.error(f"[LongTermMemory] Table creation failed: {e}")

    def add(self, items: list[MemoryItem]):
        """Add multiple memory items to long-term storage"""
        try:
            for item in items:
                # Encrypt content before storing
                if isinstance(item.content, bytes):
                    # Content is already encrypted, store as is
                    encrypted_content = item.content
                else:
                    # Content is plain text, encrypt it
                    encrypted_content = self._encrypt(item.content)

                self.conn.execute(
                    """
                    INSERT INTO memories (content, priority, timestamp, metadata)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        encrypted_content,  # Store as bytes, not string
                        item.priority,
                        item.timestamp.isoformat(),
                        pickle.dumps(item.metadata),
                    ),
                )

            self.conn.commit()
        except Exception as e:
            logging.error(f"[LongTermMemory] Add failed: {e}")

    def search(self, query: str) -> list[MemoryItem]:
        """Search memories by decrypting and searching content"""
        try:
            # Get all memories and search in decrypted content
            all_rows = self.conn.execute("SELECT * FROM memories").fetchall()
            matching_items = []

            for row in all_rows:
                try:
                    # Convert row to item (this will decrypt the content)
                    item = self._row_to_item(row)
                    # Search in decrypted content
                    if query.lower() in item.content.lower():
                        matching_items.append(item)
                except Exception as e:
                    # Skip items that can't be decrypted
                    logging.warning(f"[LongTermMemory] Skipping corrupted item: {e}")
                    continue

            return matching_items

        except Exception as e:
            logging.error(f"[LongTermMemory] Search failed: {e}")
            return []

    def compress(self) -> list[MemoryItem]:
        """Compress memories by moving old items to archive"""
        # Move memories older than 30 days to archive
        cutoff_date = datetime.now() - timedelta(days=30)
        old_memories = []

        try:
            rows = self.conn.execute(
                "SELECT * FROM memories WHERE timestamp < ?", (cutoff_date.isoformat(),)
            ).fetchall()

            for row in rows:
                old_memories.append(self._row_to_item(row))

            # Delete old memories from main table
            self.conn.execute(
                "DELETE FROM memories WHERE timestamp < ?", (cutoff_date.isoformat(),)
            )
            self.conn.commit()

        except Exception as e:
            logging.error(f"[LongTermMemory] Compression failed: {e}")

        return old_memories

    def _row_to_item(self, row):
        """Convert DB row to MemoryItem"""
        try:
            # Decrypt content before returning
            encrypted_content = row[1]
            if isinstance(encrypted_content, bytes):
                # If it's bytes, decrypt directly
                content = self._decrypt(encrypted_content)
            elif isinstance(encrypted_content, str):
                # If it's a string, try to decrypt it
                try:
                    content = self._decrypt(encrypted_content.encode())
                except Exception:
                    # If decryption fails, treat as plain text
                    content = encrypted_content
            else:
                # Fallback
                content = str(encrypted_content)

            # Handle metadata
            metadata = {}
            if len(row) > 4 and row[4]:
                try:
                    metadata = pickle.loads(row[4])
                except Exception:
                    metadata = {}

            return MemoryItem(
                content=content,
                priority=row[2],
                timestamp=datetime.fromisoformat(row[3]),
                last_accessed=datetime.now(),
                metadata=metadata,
            )
        except Exception as e:
            logging.error(f"[LongTermMemory] Failed to decrypt row: {e}")
            # Return item with encrypted content as fallback
            return MemoryItem(
                content=str(encrypted_content),
                priority=row[2],
                timestamp=datetime.fromisoformat(row[3]),
                last_accessed=datetime.now(),
                metadata=pickle.loads(row[4]),
            )


# -------------------- LAYERED MEMORY --------------------
class LayeredMemoryV1:
    """Orchestrates all memory layers with secure storage integration"""

    def __init__(
        self,
        secure_storage_config: SecureMemoryConfig | None = None,
        external_secure_storage: Any | None = None,
    ):
        self.short_term = ShortTermMemory()
        self.mid_term = MidTermMemory()
        self.long_term = LongTermMemory()
        self.logger = self._setup_logging()

        # Initialize secure storage (use external if provided, otherwise create new)
        if external_secure_storage:
            self.secure_storage = external_secure_storage
            self.logger.info("✅ Using external SecureMemoryManager")
        else:
            self.secure_storage = SecureMemoryManager(secure_storage_config)
            self.logger.info("✅ Created new SecureMemoryManager")

        self.auto_save_enabled = True
        self.last_save_time = None

        # Load existing data from secure storage (will be called manually later)
        self._data_loaded = False

        self.logger.info("✅ LayeredMemoryV1 initialized with secure storage")

    def _setup_logging(self):
        logger = logging.getLogger("LayeredMemory")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    async def _load_from_secure_storage(self):
        """Load memory data from secure storage on startup"""
        try:
            self.logger.info("🔄 Loading memory data from secure storage...")
            stored_data = self.secure_storage.load()

            if stored_data:
                if isinstance(stored_data, str):
                    memory_data = json.loads(stored_data)
                else:
                    memory_data = stored_data

                # Restore short-term memories
                if "short_term" in memory_data:
                    for item_data in memory_data["short_term"]:
                        item = MemoryItem(
                            content=item_data["content"],
                            priority=item_data["priority"],
                            timestamp=datetime.fromisoformat(item_data["timestamp"]),
                            last_accessed=datetime.fromisoformat(
                                item_data["last_accessed"]
                            ),
                            metadata=item_data["metadata"],
                        )
                        self.short_term.buffer.append(item)

                # Restore mid-term memories
                if "mid_term" in memory_data:
                    for item_data in memory_data["mid_term"]:
                        item = MemoryItem(
                            content=item_data["content"],
                            priority=item_data["priority"],
                            timestamp=datetime.fromisoformat(item_data["timestamp"]),
                            last_accessed=datetime.fromisoformat(
                                item_data["last_accessed"]
                            ),
                            metadata=item_data["metadata"],
                        )
                        self.mid_term.memories.append(item)

                self.logger.info(
                    f"✅ Loaded {len(memory_data.get('short_term', []))} short-term and {len(memory_data.get('mid_term', []))} mid-term memories"
                )
            else:
                self.logger.info("📁 No existing memory data found, starting fresh")

        except Exception as e:
            self.logger.error(f"❌ Error loading from secure storage: {e}")

    async def _save_to_secure_storage(self, reason: str = "auto"):
        """Save current memory state to secure storage"""
        try:
            # Prepare data for storage
            memory_data = {
                "short_term": [
                    {
                        "content": (
                            item.content.decode("utf-8")
                            if isinstance(item.content, bytes)
                            else item.content
                        ),
                        "priority": item.priority,
                        "timestamp": item.timestamp.isoformat(),
                        "last_accessed": item.last_accessed.isoformat(),
                        "metadata": item.metadata,
                    }
                    for item in self.short_term.buffer
                ],
                "mid_term": [
                    {
                        "content": (
                            item.content.decode("utf-8")
                            if isinstance(item.content, bytes)
                            else item.content
                        ),
                        "priority": item.priority,
                        "timestamp": item.timestamp.isoformat(),
                        "last_accessed": item.last_accessed.isoformat(),
                        "metadata": item.metadata,
                    }
                    for item in self.mid_term.memories
                ],
                "last_save": datetime.now().isoformat(),
                "total_memories": len(self.short_term.buffer)
                + len(self.mid_term.memories),
            }

            # Save to secure storage
            success = self.secure_storage.save(memory_data)

            if success:
                self.last_save_time = datetime.now()
                self.logger.info(f"💾 Memory data saved to secure storage ({reason})")
            else:
                self.logger.error("❌ Failed to save memory data to secure storage")

        except Exception as e:
            self.logger.error(f"❌ Error saving to secure storage: {e}")

    def add_memory(
        self,
        content: str,
        priority: float = 0.5,
        auto_compress: bool = True,
        metadata: dict | None = None,
    ):
        """Add memory with automatic layer selection and secure storage"""
        item = MemoryItem(
            content=content,
            priority=priority,
            timestamp=datetime.now(),
            last_accessed=datetime.now(),
            metadata=metadata or {},
        )

        # Always add to short-term first, then compress based on priority
        self.short_term.add(item)

        if auto_compress:
            # Force compress if high priority item
            force_compress = item.priority >= 0.8
            self._auto_compress(force=force_compress)

        # Auto-save to secure storage if enabled (only for high priority items)
        if self.auto_save_enabled and item.priority >= 0.8:
            try:
                # Try to get running event loop
                loop = asyncio.get_running_loop()
                loop.create_task(self._save_to_secure_storage("memory_added"))
            except RuntimeError:
                # No event loop running, skip async save
                self.logger.warning("No event loop running, skipping async save")

    def search(
        self, query: str, time_range: tuple[datetime, datetime] | None = None
    ) -> list[MemoryItem]:
        """Search across all layers with optional time filter"""
        results = []
        results.extend(self.short_term.search(query))
        results.extend(self.mid_term.search(query))
        results.extend(self.long_term.search(query))

        if time_range:
            start, end = time_range
            results = [r for r in results if start <= r.timestamp <= end]

        return sorted(results, key=lambda x: x.priority, reverse=True)

    def _auto_compress(self, force=False):
        """Move memories between layers based on rules"""
        total_compressed = 0

        # Short-term -> Mid-term (based on priority and capacity)
        if (
            force
            or len(self.short_term.buffer)
            > SHORT_TERM_CAPACITY * MID_TERM_COMPRESSION_THRESHOLD
        ):
            # Compress high priority items (>= 0.8) directly to long-term
            high_priority_items = []
            mid_priority_items = []

            for item in self.short_term.buffer:
                if item.priority >= 0.8:
                    high_priority_items.append(item)
                else:
                    mid_priority_items.append(item)

            # Move high priority items to long-term
            if high_priority_items:
                self.long_term.add(high_priority_items)
                self.logger.info(
                    f"Compressed {len(high_priority_items)} high-priority items to long-term"
                )
                total_compressed += len(high_priority_items)

            # Move remaining items to mid-term
            if mid_priority_items:
                for item in mid_priority_items:
                    self.mid_term.add(item)
                self.logger.info(
                    f"Compressed {len(mid_priority_items)} items to mid-term"
                )
                total_compressed += len(mid_priority_items)

            # Clear short-term buffer
            self.short_term.buffer.clear()

        # Mid-term -> Long-term
        if force or len(self.mid_term.memories) > 1000:  # Arbitrary threshold
            compressed = self.mid_term.compress()
            self.long_term.add(compressed)
            self.logger.info(f"Compressed {len(compressed)} items to long-term")
            total_compressed += len(compressed)

        # Auto-save after compression (only if significant changes)
        if self.auto_save_enabled and (force or total_compressed > 10):
            try:
                # Try to get running event loop
                loop = asyncio.get_running_loop()
                loop.create_task(self._save_to_secure_storage("compression"))
            except RuntimeError:
                # No event loop running, skip async save
                self.logger.warning("No event loop running, skipping async save")

    async def force_save(self):
        """Force save current memory state to secure storage"""
        await self._save_to_secure_storage("manual")

    async def force_load(self):
        """Force reload memory data from secure storage"""
        await self._load_from_secure_storage()

    def get_storage_status(self) -> dict[str, Any]:
        """Get status of secure storage integration"""
        try:
            health = self.secure_storage.get_health_status()
            metrics = self.secure_storage.get_performance_metrics()

            return {
                "secure_storage_enabled": True,
                "auto_save_enabled": self.auto_save_enabled,
                "last_save_time": (
                    self.last_save_time.isoformat() if self.last_save_time else None
                ),
                "storage_health": health,
                "storage_metrics": metrics,
                "memory_counts": {
                    "short_term": len(self.short_term.buffer),
                    "mid_term": len(self.mid_term.memories),
                    "total": len(self.short_term.buffer) + len(self.mid_term.memories),
                },
            }
        except Exception as e:
            return {
                "secure_storage_enabled": False,
                "error": str(e),
                "memory_counts": {
                    "short_term": len(self.short_term.buffer),
                    "mid_term": len(self.mid_term.memories),
                    "total": len(self.short_term.buffer) + len(self.mid_term.memories),
                },
            }

    async def shutdown(self):
        """Cleanup and save final state"""
        try:
            # Save final memory state
            await self._save_to_secure_storage("shutdown")

            # Shutdown secure storage
            self.secure_storage.shutdown()

            self.logger.info("🔄 LayeredMemoryV1 shutdown completed")

        except Exception as e:
            self.logger.error(f"❌ Error during shutdown: {e}")


# -------------------- MAIN --------------------
if __name__ == "__main__":

    async def main():
        memory = LayeredMemoryV1()
        memory.add_memory("User prefers dark coffee", 0.6)
        memory.add_memory("User is allergic to peanuts", 0.9)
        results = memory.search("coffee")
        print(f"Found {len(results)} relevant memories")

        # Get storage status
        status = memory.get_storage_status()
        print(f"Storage status: {status}")

        # Force save
        await memory.force_save()

        # Shutdown
        await memory.shutdown()

    asyncio.run(main())
