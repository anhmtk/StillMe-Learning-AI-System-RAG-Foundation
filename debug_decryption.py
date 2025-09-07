#!/usr/bin/env python3
"""Debug decryption"""

from modules.layered_memory_v1 import LayeredMemoryV1

# Create memory manager
memory = LayeredMemoryV1()

# Add a test item
memory.add_memory(
    content="This is a test learning result about machine learning",
    priority=0.8,
    metadata={"type": "learning_result", "test": True}
)

print("Testing decryption...")
try:
    conn = memory.long_term.conn
    cursor = conn.cursor()
    
    # Get recent items
    cursor.execute("SELECT * FROM memories ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    
    print(f"Row: {row}")
    print(f"Row[1] type: {type(row[1])}")
    print(f"Row[1] value: {row[1]}")
    
    # Test decryption
    encrypted_content = row[1]
    print(f"Encrypted content type: {type(encrypted_content)}")
    
    try:
        decrypted_content = memory.long_term._decrypt(encrypted_content.encode())
        print(f"Decrypted content: {decrypted_content}")
    except Exception as e:
        print(f"Decryption error: {e}")
        
    # Test _row_to_item
    try:
        item = memory.long_term._row_to_item(row)
        print(f"Row to item success: {item}")
        if item:
            print(f"Item content: {item.content}")
            print(f"Item metadata: {item.metadata}")
    except Exception as e:
        print(f"Row to item error: {e}")
        import traceback
        traceback.print_exc()
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
