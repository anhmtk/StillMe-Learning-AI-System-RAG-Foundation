#!/usr/bin/env python3
"""
🧠 LAYERED MEMORY V1 - SIMPLE VERSION
🧠 LAYERED MEMORY V1 - PHIÊN BẢN ĐƠN GIẢN

PURPOSE / MỤC ĐÍCH:
- Simple layered memory system without complex dependencies
- Hệ thống bộ nhớ phân lớp đơn giản không có dependencies phức tạp
- Manages short/mid/long-term memory layers
- Quản lý các lớp bộ nhớ ngắn hạn/trung hạn/dài hạn
- Provides intelligent forgetting and memory consolidation
- Cung cấp quên thông minh và củng cố bộ nhớ
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict

# Initialize logger
logger = logging.getLogger("StillMe.LayeredMemory")

@dataclass
class MemoryItem:
    """Simple memory item structure"""
    id: str
    content: str
    timestamp: float
    importance: float
    access_count: int = 0
    last_accessed: float = 0.0
    tags: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.last_accessed == 0.0:
            self.last_accessed = self.timestamp

class LayeredMemoryV1:
    """Simple layered memory system with intelligent forgetting"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = logger
        self.config = config or self._get_default_config()
        
        # Memory layers
        self.short_term: List[MemoryItem] = []
        self.mid_term: List[MemoryItem] = []
        self.long_term: List[MemoryItem] = []
        
        # Statistics
        self.stats = {
            "total_memories": 0,
            "short_term_count": 0,
            "mid_term_count": 0,
            "long_term_count": 0,
            "forgotten_count": 0,
            "consolidated_count": 0
        }
        
        self.logger.info("✅ LayeredMemoryV1 initialized (simple mode)")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "short_term_capacity": 100,
            "mid_term_capacity": 500,
            "long_term_capacity": 2000,
            "short_term_ttl": 3600,  # 1 hour
            "mid_term_ttl": 86400,   # 1 day
            "consolidation_threshold": 0.7,
            "forgetting_threshold": 0.3,
            "importance_decay_rate": 0.1
        }
    
    def store(self, content: str, importance: float = 0.5, tags: Optional[List[str]] = None) -> str:
        """Store a new memory item"""
        try:
            memory_id = f"mem_{int(time.time() * 1000)}"
            timestamp = time.time()
            
            memory_item = MemoryItem(
                id=memory_id,
                content=content,
                timestamp=timestamp,
                importance=importance,
                tags=tags or []
            )
            
            # Store in short-term memory first
            self.short_term.append(memory_item)
            self.stats["total_memories"] += 1
            self.stats["short_term_count"] += 1
            
            # Trigger consolidation if needed
            self._consolidate_memories()
            
            self.logger.info(f"💾 Stored memory: {memory_id}")
            return memory_id
            
        except Exception as e:
            self.logger.error(f"❌ Failed to store memory: {e}")
            return ""
    
    def retrieve(self, query: str, limit: int = 10) -> List[MemoryItem]:
        """Retrieve memories based on query"""
        try:
            query_lower = query.lower()
            results = []
            
            # Search in all layers
            for memory in self.short_term + self.mid_term + self.long_term:
                if query_lower in memory.content.lower():
                    # Update access statistics
                    memory.access_count += 1
                    memory.last_accessed = time.time()
                    results.append(memory)
            
            # Sort by relevance (importance + recency)
            results.sort(key=lambda x: (
                x.importance * 0.7 + 
                (1.0 / (time.time() - x.timestamp + 1)) * 0.3
            ), reverse=True)
            
            return results[:limit]
            
        except Exception as e:
            self.logger.error(f"❌ Failed to retrieve memories: {e}")
            return []
    
    def _consolidate_memories(self):
        """Consolidate memories between layers"""
        try:
            current_time = time.time()
            
            # Consolidate short-term to mid-term
            to_consolidate = []
            remaining_short = []
            
            for memory in self.short_term:
                age = current_time - memory.timestamp
                if age > self.config["short_term_ttl"]:
                    if memory.importance >= self.config["consolidation_threshold"]:
                        to_consolidate.append(memory)
                    else:
                        # Forget low-importance memories
                        self.stats["forgotten_count"] += 1
                else:
                    remaining_short.append(memory)
            
            self.short_term = remaining_short
            self.stats["short_term_count"] = len(self.short_term)
            
            # Add consolidated memories to mid-term
            for memory in to_consolidate:
                self.mid_term.append(memory)
                self.stats["consolidated_count"] += 1
            
            self.stats["mid_term_count"] = len(self.mid_term)
            
            # Consolidate mid-term to long-term
            to_consolidate = []
            remaining_mid = []
            
            for memory in self.mid_term:
                age = current_time - memory.timestamp
                if age > self.config["mid_term_ttl"]:
                    if memory.importance >= self.config["consolidation_threshold"]:
                        to_consolidate.append(memory)
                    else:
                        # Forget low-importance memories
                        self.stats["forgotten_count"] += 1
                else:
                    remaining_mid.append(memory)
            
            self.mid_term = remaining_mid
            self.stats["mid_term_count"] = len(self.mid_term)
            
            # Add consolidated memories to long-term
            for memory in to_consolidate:
                self.long_term.append(memory)
            
            self.stats["long_term_count"] = len(self.long_term)
            
            # Apply capacity limits
            self._enforce_capacity_limits()
            
        except Exception as e:
            self.logger.error(f"❌ Failed to consolidate memories: {e}")
    
    def _enforce_capacity_limits(self):
        """Enforce capacity limits for each layer"""
        try:
            # Short-term capacity
            if len(self.short_term) > self.config["short_term_capacity"]:
                # Remove oldest, least important memories
                self.short_term.sort(key=lambda x: (x.importance, x.timestamp))
                excess = len(self.short_term) - self.config["short_term_capacity"]
                for _ in range(excess):
                    forgotten = self.short_term.pop(0)
                    self.stats["forgotten_count"] += 1
            
            # Mid-term capacity
            if len(self.mid_term) > self.config["mid_term_capacity"]:
                self.mid_term.sort(key=lambda x: (x.importance, x.timestamp))
                excess = len(self.mid_term) - self.config["mid_term_capacity"]
                for _ in range(excess):
                    forgotten = self.mid_term.pop(0)
                    self.stats["forgotten_count"] += 1
            
            # Long-term capacity
            if len(self.long_term) > self.config["long_term_capacity"]:
                self.long_term.sort(key=lambda x: (x.importance, x.timestamp))
                excess = len(self.long_term) - self.config["long_term_capacity"]
                for _ in range(excess):
                    forgotten = self.long_term.pop(0)
                    self.stats["forgotten_count"] += 1
                    
        except Exception as e:
            self.logger.error(f"❌ Failed to enforce capacity limits: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        return {
            **self.stats,
            "current_short_term": len(self.short_term),
            "current_mid_term": len(self.mid_term),
            "current_long_term": len(self.long_term),
            "total_current": len(self.short_term) + len(self.mid_term) + len(self.long_term)
        }
    
    def clear_all(self):
        """Clear all memories"""
        self.short_term.clear()
        self.mid_term.clear()
        self.long_term.clear()
        self.stats = {
            "total_memories": 0,
            "short_term_count": 0,
            "mid_term_count": 0,
            "long_term_count": 0,
            "forgotten_count": 0,
            "consolidated_count": 0
        }
        self.logger.info("🗑️ All memories cleared")
    
    def export_memories(self) -> Dict[str, Any]:
        """Export all memories for backup"""
        return {
            "short_term": [asdict(memory) for memory in self.short_term],
            "mid_term": [asdict(memory) for memory in self.mid_term],
            "long_term": [asdict(memory) for memory in self.long_term],
            "stats": self.stats,
            "export_timestamp": time.time()
        }
    
    def import_memories(self, data: Dict[str, Any]):
        """Import memories from backup"""
        try:
            self.clear_all()
            
            # Import memories
            for memory_data in data.get("short_term", []):
                memory = MemoryItem(**memory_data)
                self.short_term.append(memory)
            
            for memory_data in data.get("mid_term", []):
                memory = MemoryItem(**memory_data)
                self.mid_term.append(memory)
            
            for memory_data in data.get("long_term", []):
                memory = MemoryItem(**memory_data)
                self.long_term.append(memory)
            
            # Import stats
            self.stats.update(data.get("stats", {}))
            
            self.logger.info("📥 Memories imported successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to import memories: {e}")
