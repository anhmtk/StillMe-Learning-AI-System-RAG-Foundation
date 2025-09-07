#!/usr/bin/env python3
"""Debug long-term memory search"""

from modules.layered_memory_v1 import LayeredMemoryV1
from datetime import datetime

# Create memory manager
memory = LayeredMemoryV1()

# Add a test item
memory.add_memory(
    content="This is a test learning result about machine learning",
    priority=0.8,
    metadata={"type": "learning_result", "test": True}
)

print("Checking long-term memory directly...")
try:
    conn = memory.long_term.conn
    cursor = conn.cursor()
    
    # Get total count
    cursor.execute("SELECT COUNT(*) FROM memories")
    count = cursor.fetchone()[0]
    print(f"Total items in long-term memory: {count}")
    
    # Get recent items
    cursor.execute("SELECT id, content, metadata FROM memories ORDER BY id DESC LIMIT 3")
    rows = cursor.fetchall()
    
    for row in rows:
        print(f"ID: {row[0]}")
        print(f"Content (encrypted): {row[1][:50]}...")
        print(f"Metadata: {row[2]}")
        print("---")
        
        # Try to decrypt
        try:
            decrypted = memory.long_term._row_to_item(row)
            print(f"Decrypted content: {decrypted.content[:50]}...")
            print(f"Decrypted metadata: {decrypted.metadata}")
        except Exception as e:
            print(f"Decryption error: {e}")
        print("=" * 50)
        
except Exception as e:
    print(f"Error accessing long-term memory: {e}")

print("\nTesting long-term search directly...")
try:
    results = memory.long_term.search("learning")
    print(f"Long-term search found {len(results)} results")
    for r in results:
        print(f"  - {r.content[:50]}...")
except Exception as e:
    print(f"Long-term search error: {e}")
