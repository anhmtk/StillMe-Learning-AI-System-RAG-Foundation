#!/usr/bin/env python3
"""Debug memory search"""

from modules.layered_memory_v1 import LayeredMemoryV1

memory = LayeredMemoryV1()
results = memory.search('learning_result')
print(f'Found {len(results)} results')

for r in results:
    print(f'Type: {r.metadata.get("type")}, Content: {r.content[:100]}...')
