#!/usr/bin/env python3
"""Debug memory search detailed"""

from modules.layered_memory_v1 import LayeredMemoryV1

memory = LayeredMemoryV1()

# Check all layers
print("Short-term memory:")
print(f"  Items: {len(memory.short_term.buffer)}")
for i, item in enumerate(memory.short_term.buffer):
    print(f"  {i}: {item.metadata.get('type', 'unknown')} - {item.content[:50]}...")

print("\nMid-term memory:")
print(f"  Items: {len(memory.mid_term.memories)}")
for i, item in enumerate(memory.mid_term.memories):
    print(f"  {i}: {item.metadata.get('type', 'unknown')} - {item.content[:50]}...")

print("\nLong-term memory:")
# Check long-term memory
try:
    conn = memory.long_term.conn
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM memories")
    count = cursor.fetchone()[0]
    print(f"  Items: {count}")
    
    cursor.execute("SELECT content, metadata FROM memories LIMIT 3")
    rows = cursor.fetchall()
    for i, (content, metadata) in enumerate(rows):
        print(f"  {i}: {content[:50]}...")
except Exception as e:
    print(f"  Error accessing long-term memory: {e}")

# Test search
print("\nSearch results:")
results = memory.search('learning_result')
print(f"Found {len(results)} results")
