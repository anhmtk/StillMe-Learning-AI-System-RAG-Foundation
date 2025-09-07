#!/usr/bin/env python3
"""Debug row structure"""

from modules.layered_memory_v1 import LayeredMemoryV1

# Create memory manager
memory = LayeredMemoryV1()

# Add a test item
memory.add_memory(
    content="This is a test learning result about machine learning",
    priority=0.8,
    metadata={"type": "learning_result", "test": True}
)

print("Checking row structure...")
try:
    conn = memory.long_term.conn
    cursor = conn.cursor()
    
    # Get recent items
    cursor.execute("SELECT * FROM memories ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    
    print(f"Row length: {len(row)}")
    print(f"Row: {row}")
    
    for i, item in enumerate(row):
        print(f"  {i}: {type(item)} - {item}")
        
except Exception as e:
    print(f"Error: {e}")
