#!/usr/bin/env python3
"""Test memory search functionality"""

from modules.layered_memory_v1 import LayeredMemoryV1, MemoryItem
from datetime import datetime

# Create memory manager
memory = LayeredMemoryV1()

# Add a test item directly
test_item = MemoryItem(
    content="This is a test learning result about machine learning",
    priority=0.8,
    timestamp=datetime.now(),
    last_accessed=datetime.now(),
    metadata={"type": "learning_result", "test": True}
)

print("Adding test item...")
memory.add_memory(
    content="This is a test learning result about machine learning",
    priority=0.8,
    metadata={"type": "learning_result", "test": True}
)

print("Searching for 'learning'...")
results = memory.search("learning")
print(f"Found {len(results)} results")

for r in results:
    print(f"  - {r.metadata.get('type')}: {r.content[:50]}...")

print("\nSearching for 'machine'...")
results = memory.search("machine")
print(f"Found {len(results)} results")

for r in results:
    print(f"  - {r.metadata.get('type')}: {r.content[:50]}...")
