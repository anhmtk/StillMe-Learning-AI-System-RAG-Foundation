"""
Unified Memory System for StillMe Framework
==========================================

This module provides a unified memory management system with TTL support,
persistence, and layered storage capabilities.

Author: StillMe AI Framework
Version: 1.0.0
"""

import json
import logging
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class MemoryItem:
    """Memory item with TTL support"""

    value: Any
    timestamp: float
    ttl: int | None = None
    last_accessed: float | None = None

    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = self.timestamp

    def is_expired(self) -> bool:
        """Check if item has expired based on TTL"""
        if self.ttl is None:
            return False
        return time.time() - self.timestamp > self.ttl


class MemoryLayer:
    """Memory layer with TTL support"""

    def __init__(self, name: str, config: dict[str, Any]):
        self.name = name
        self.config = config
        self.data: dict[str, MemoryItem] = {}
        self.ttl = config.get("ttl", 3600)
        self.max_size = config.get("max_size", 1000)

    def store(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Store value with TTL"""
        try:
            # Clean expired items
            self._clean_expired()

            # Check size limit
            if len(self.data) >= self.max_size:
                self._evict_oldest()

            # Store new item
            self.data[key] = MemoryItem(
                value=value, timestamp=time.time(), ttl=ttl or self.ttl
            )
            return True
        except Exception as e:
            logger.error(f"Failed to store in layer {self.name}: {e}")
            return False

    def retrieve(self, key: str) -> Any | None:
        """Retrieve value, return None if expired or not found"""
        try:
            if key not in self.data:
                return None

            item = self.data[key]

            # Check if expired
            if item.is_expired():
                del self.data[key]
                return None

            # Update last accessed
            item.last_accessed = time.time()
            return item.value
        except Exception as e:
            logger.error(f"Failed to retrieve from layer {self.name}: {e}")
            return None

    def _clean_expired(self):
        """Remove expired items"""
        expired_keys = [k for k, v in self.data.items() if v.is_expired()]
        for key in expired_keys:
            del self.data[key]

    def _evict_oldest(self):
        """Evict oldest item when at capacity"""
        if not self.data:
            return

        oldest_key = min(
            self.data.keys(), key=lambda k: self.data[k].last_accessed or 0.0
        )
        del self.data[oldest_key]


class MemoryManager:
    """Main memory manager with layered storage and TTL support"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.layers: dict[str, MemoryLayer] = {}
        self.ttl_enabled = config.get("ttl_enabled", True)
        self.max_size = config.get("max_size", 1000)

        # Initialize default layers
        self._init_layers()

        logger.info("✅ MemoryManager initialized")

    def _init_layers(self):
        """Initialize memory layers"""
        layer_configs = self.config.get(
            "layers",
            {
                "short_term": {"ttl": 300, "max_size": 100},  # 5 minutes
                "mid_term": {"ttl": 3600, "max_size": 500},  # 1 hour
                "long_term": {"ttl": None, "max_size": 1000},  # No expiry
            },
        )

        for name, config in layer_configs.items():
            self.layers[name] = MemoryLayer(name, config)

    def store(
        self, key: str, value: Any, ttl: int | None = None, layer: str = "mid_term"
    ) -> bool:
        """Store value in specified layer"""
        # Validate inputs
        if key is None:
            raise ValueError("Key cannot be None")
        if not isinstance(key, str):
            raise ValueError("Key must be a string")
        if not key.strip():
            raise ValueError("Key cannot be empty")
        if layer not in self.layers:
            logger.error(f"Layer {layer} not found")
            return False

        return self.layers[layer].store(key, value, ttl)

    def retrieve(self, key: str, layer: str | None = None) -> Any | None:
        """Retrieve value from layers (searches all if layer not specified)"""
        # Validate inputs
        if key is None:
            raise ValueError("Key cannot be None")
        if not isinstance(key, str):
            raise ValueError("Key must be a string")
        if not key.strip():
            raise ValueError("Key cannot be empty")

        if layer:
            if layer not in self.layers:
                logger.error(f"Layer {layer} not found")
                return None
            return self.layers[layer].retrieve(key)

        # Search all layers in order
        for layer_name in ["short_term", "mid_term", "long_term"]:
            if layer_name in self.layers:
                value = self.layers[layer_name].retrieve(key)
                if value is not None:
                    return value

        return None

    def clear(self, layer: str | None = None) -> bool:
        """Clear memory layer(s)"""
        try:
            if layer:
                if layer in self.layers:
                    self.layers[layer].data.clear()
                else:
                    logger.error(f"Layer {layer} not found")
                    return False
            else:
                for layer_obj in self.layers.values():
                    layer_obj.data.clear()
            return True
        except Exception as e:
            logger.error(f"Failed to clear memory: {e}")
            return False

    def get_stats(self) -> dict[str, Any]:
        """Get memory statistics"""
        stats = {
            "total_items": sum(len(layer.data) for layer in self.layers.values()),
            "layers": {},
        }

        for name, layer in self.layers.items():
            stats["layers"][name] = {
                "items": len(layer.data),
                "max_size": layer.max_size,
                "ttl": layer.ttl,
            }

        return stats


class PersistenceManager:
    """Persistence manager for saving/loading memory data"""

    def __init__(self, config: dict[str, Any] | None = None):
        if config is None:
            config = {}

        # Handle both string db_path and config dict
        if isinstance(config, str):
            db_path = config
        else:
            db_path = config.get("db_path", "memory.db")
            # If storage_path is provided, use it as base directory
            if "storage_path" in config:
                storage_path = Path(config["storage_path"])
                storage_path.mkdir(exist_ok=True)
                db_path = str(storage_path / db_path)

        self.db_path = Path(db_path)
        self.logger = logging.getLogger(__name__)
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS memory_items (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        layer TEXT NOT NULL,
                        timestamp REAL NOT NULL,
                        ttl INTEGER,
                        last_accessed REAL
                    )
                """)
                conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise

    def save_data(self, memory_manager: MemoryManager) -> bool:
        """Save memory data to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Clear existing data
                conn.execute("DELETE FROM memory_items")

                # Save all items from all layers
                for layer_name, layer in memory_manager.layers.items():
                    for key, item in layer.data.items():
                        conn.execute(
                            """
                            INSERT INTO memory_items
                            (key, value, layer, timestamp, ttl, last_accessed)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """,
                            (
                                key,
                                json.dumps(item.value),
                                layer_name,
                                item.timestamp,
                                item.ttl,
                                item.last_accessed,
                            ),
                        )

                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Failed to save data: {e}")
            return False

    def load_data(self, memory_manager: MemoryManager) -> bool:
        """Load memory data from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT key, value, layer, timestamp, ttl, last_accessed
                    FROM memory_items
                """)

                for row in cursor.fetchall():
                    key, value_str, layer_name, timestamp, ttl, last_accessed = row

                    if layer_name in memory_manager.layers:
                        try:
                            value = json.loads(value_str)
                            item = MemoryItem(
                                value=value,
                                timestamp=timestamp,
                                ttl=ttl,
                                last_accessed=last_accessed,
                            )
                            memory_manager.layers[layer_name].data[key] = item
                        except json.JSONDecodeError as e:
                            self.logger.warning(
                                f"Failed to decode value for key {key}: {e}"
                            )

                return True
        except Exception as e:
            self.logger.error(f"Failed to load data: {e}")
            return False

    def save(self, data: dict[str, Any]) -> bool:
        """Save data directly to database (for backward compatibility)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Clear existing data
                conn.execute("DELETE FROM memory_items")

                # Save data as key-value pairs in mid_term layer
                for key, value in data.items():
                    conn.execute(
                        """
                        INSERT INTO memory_items
                        (key, value, layer, timestamp, ttl, last_accessed)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """,
                        (
                            key,
                            json.dumps(value),
                            "mid_term",
                            time.time(),
                            None,
                            time.time(),
                        ),
                    )

                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Failed to save data: {e}")
            return False

    def load(self) -> dict[str, Any]:
        """Load data directly from database (for backward compatibility)"""
        try:
            data = {}
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT key, value FROM memory_items
                """)

                for row in cursor.fetchall():
                    key, value_str = row
                    try:
                        data[key] = json.loads(value_str)
                    except json.JSONDecodeError as e:
                        self.logger.warning(
                            f"Failed to decode value for key {key}: {e}"
                        )

                return data
        except Exception as e:
            self.logger.error(f"Failed to load data: {e}")
            return {}
