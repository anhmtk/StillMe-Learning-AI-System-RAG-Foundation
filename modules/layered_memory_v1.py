"""
LayeredMemory_v1.py
-------------------
Memory system with short/mid/long-term layers with intelligent forgetting.
Integrated with SecureMemoryManager for encrypted storage and backup.
"""

import sqlite3
import logging
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
from abc import ABC, abstractmethod
import pickle
from cryptography.fernet import Fernet
import warnings
import asyncio
import json

# Import SecureMemoryManager
try:
    from .secure_memory_manager import SecureMemoryManager, SecureMemoryConfig
except ImportError:
    from secure_memory_manager import SecureMemoryManager, SecureMemoryConfig

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
    embedding: Optional[np.ndarray] = None

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
        item.content = self._encrypt(item.content).decode('utf-8')

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

    def add(self, items: List[MemoryItem]):
        for item in items:
            if len(self.memories) >= self.max_size:
                # Remove lowest priority item
                self.memories.sort(key=lambda x: x.priority)
                self.memories.pop(0)
            
            # Encrypt content before storing
            item.content = self._encrypt(item.content).decode('utf-8')
            self.memories.append(item)

    def search(self, query: str) -> List[MemoryItem]:
        results = []
        for item in self.memories:
            decrypted_content = self._decrypt(item.content)
            if query.lower() in decrypted_content.lower():
                item.last_accessed = datetime.now()
                results.append(item)
        return sorted(results, key=lambda x: x.priority, reverse=True)

    def compress(self) -> List[MemoryItem]:
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
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY,
                    content TEXT NOT NULL,
                    priority REAL DEFAULT 0.5,
                    timestamp TEXT NOT NULL,
                    metadata BLOB
                )
            """)
            
            # FTS table for fast search
            self.conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts 
                USING fts5(content, content='memories', content_rowid='id')
            """)
            
            # Trigger to keep FTS in sync
            self.conn.execute("""
                CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
                    INSERT INTO memories_fts(rowid, content) VALUES (new.id, new.content);
                END
            """)
            
            self.conn.execute("""
                CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
                    INSERT INTO memories_fts(memories_fts, rowid, content) VALUES('delete', old.id, old.content);
                END
            """)
            
            self.conn.commit()
        except Exception as e:
            logging.error(f"[LongTermMemory] Table creation failed: {e}")

    def add(self, items: List[MemoryItem]):
        """Add multiple memory items to long-term storage"""
        try:
            for item in items:
                # Encrypt content before storing
                encrypted_content = self._encrypt(item.content)
                
                self.conn.execute("""
                    INSERT INTO memories (content, priority, timestamp, metadata)
                    VALUES (?, ?, ?, ?)
                """, (
                    encrypted_content.decode('utf-8'),
                    item.priority,
                    item.timestamp.isoformat(),
                    pickle.dumps(item.metadata)
                ))
            
            self.conn.commit()
        except Exception as e:
            logging.error(f"[LongTermMemory] Add failed: {e}")

    def search(self, query: str) -> List[MemoryItem]:
        """Search memories using FTS with fallback to LIKE"""
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

    def compress(self) -> List[MemoryItem]:
        """Compress memories by moving old items to archive"""
        # Move memories older than 30 days to archive
        cutoff_date = datetime.now() - timedelta(days=30)
        old_memories = []
        
        try:
            rows = self.conn.execute(
                "SELECT * FROM memories WHERE timestamp < ?",
                (cutoff_date.isoformat(),)
            ).fetchall()
            
            for row in rows:
                old_memories.append(self._row_to_item(row))
            
            # Delete old memories from main table
            self.conn.execute(
                "DELETE FROM memories WHERE timestamp < ?",
                (cutoff_date.isoformat(),)
            )
            self.conn.commit()
            
        except Exception as e:
            logging.error(f"[LongTermMemory] Compression failed: {e}")
        
        return old_memories

    def _row_to_item(self, row):
        """Convert DB row to MemoryItem"""
        # Decrypt content before returning
        encrypted_content = row[1]
        if isinstance(encrypted_content, str):
            decrypted_content = self._decrypt(encrypted_content.encode())
        else:
            decrypted_content = self._decrypt(encrypted_content)
        
        return MemoryItem(
            content=decrypted_content.decode('utf-8'),
            priority=row[2],
            timestamp=datetime.fromisoformat(row[3]),
            last_accessed=datetime.now(),
            metadata=pickle.loads(row[4])
        )

# -------------------- LAYERED MEMORY --------------------
class LayeredMemoryV1:
    """Orchestrates all memory layers with secure storage integration"""
    def __init__(self, secure_storage_config: Optional[SecureMemoryConfig] = None, 
                 external_secure_storage: Optional[Any] = None):
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
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
    
    async def _load_from_secure_storage(self):
        """Load memory data from secure storage on startup"""
        try:
            self.logger.info("🔄 Loading memory data from secure storage...")
            stored_data = await self.secure_storage.load()
            
            if stored_data:
                memory_data = json.loads(stored_data)
                
                # Restore short-term memories
                if 'short_term' in memory_data:
                    for item_data in memory_data['short_term']:
                        item = MemoryItem(
                            content=item_data['content'],
                            priority=item_data['priority'],
                            timestamp=datetime.fromisoformat(item_data['timestamp']),
                            last_accessed=datetime.fromisoformat(item_data['last_accessed']),
                            metadata=item_data['metadata']
                        )
                        self.short_term.buffer.append(item)
                
                # Restore mid-term memories
                if 'mid_term' in memory_data:
                    for item_data in memory_data['mid_term']:
                        item = MemoryItem(
                            content=item_data['content'],
                            priority=item_data['priority'],
                            timestamp=datetime.fromisoformat(item_data['timestamp']),
                            last_accessed=datetime.fromisoformat(item_data['last_accessed']),
                            metadata=item_data['metadata']
                        )
                        self.mid_term.memories.append(item)
                
                self.logger.info(f"✅ Loaded {len(memory_data.get('short_term', []))} short-term and {len(memory_data.get('mid_term', []))} mid-term memories")
            else:
                self.logger.info("📁 No existing memory data found, starting fresh")
                
        except Exception as e:
            self.logger.error(f"❌ Error loading from secure storage: {e}")
    
    async def _save_to_secure_storage(self, reason: str = "auto"):
        """Save current memory state to secure storage"""
        try:
            # Prepare data for storage
            memory_data = {
                'short_term': [
                    {
                        'content': item.content,
                        'priority': item.priority,
                        'timestamp': item.timestamp.isoformat(),
                        'last_accessed': item.last_accessed.isoformat(),
                        'metadata': item.metadata
                    }
                    for item in self.short_term.buffer
                ],
                'mid_term': [
                    {
                        'content': item.content,
                        'priority': item.priority,
                        'timestamp': item.timestamp.isoformat(),
                        'last_accessed': item.last_accessed.isoformat(),
                        'metadata': item.metadata
                    }
                    for item in self.mid_term.memories
                ],
                'last_save': datetime.now().isoformat(),
                'total_memories': len(self.short_term.buffer) + len(self.mid_term.memories)
            }
            
            # Save to secure storage
            success = await self.secure_storage.save(memory_data, auto_backup=True)
            
            if success:
                self.last_save_time = datetime.now()
                self.logger.info(f"💾 Memory data saved to secure storage ({reason})")
            else:
                self.logger.error(f"❌ Failed to save memory data to secure storage")
                
        except Exception as e:
            self.logger.error(f"❌ Error saving to secure storage: {e}")
    
    def add_memory(self, content: str, priority: float = 0.5, 
                  auto_compress: bool = True, metadata: Optional[dict] = None):
        """Add memory with automatic layer selection and secure storage"""
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
        
        # Auto-save to secure storage if enabled
        if self.auto_save_enabled:
            asyncio.create_task(self._save_to_secure_storage("memory_added"))
    
    def search(self, query: str, time_range: Optional[Tuple[datetime, datetime]] = None
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
        
        # Auto-save after compression
        if self.auto_save_enabled:
            asyncio.create_task(self._save_to_secure_storage("compression"))
    
    async def force_save(self):
        """Force save current memory state to secure storage"""
        await self._save_to_secure_storage("manual")
    
    async def force_load(self):
        """Force reload memory data from secure storage"""
        await self._load_from_secure_storage()
    
    def get_storage_status(self) -> Dict[str, any]:
        """Get status of secure storage integration"""
        try:
            health = self.secure_storage.get_health_status()
            metrics = self.secure_storage.get_performance_metrics()
            
            return {
                'secure_storage_enabled': True,
                'auto_save_enabled': self.auto_save_enabled,
                'last_save_time': self.last_save_time.isoformat() if self.last_save_time else None,
                'storage_health': health,
                'storage_metrics': metrics,
                'memory_counts': {
                    'short_term': len(self.short_term.buffer),
                    'mid_term': len(self.mid_term.memories),
                    'total': len(self.short_term.buffer) + len(self.mid_term.memories)
                }
            }
        except Exception as e:
            return {
                'secure_storage_enabled': False,
                'error': str(e),
                'memory_counts': {
                    'short_term': len(self.short_term.buffer),
                    'mid_term': len(self.mid_term.memories),
                    'total': len(self.short_term.buffer) + len(self.mid_term.memories)
                }
            }
    
    async def shutdown(self):
        """Cleanup and save final state"""
        try:
            # Save final memory state
            await self._save_to_secure_storage("shutdown")
            
            # Shutdown secure storage
            await self.secure_storage.shutdown()
            
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
