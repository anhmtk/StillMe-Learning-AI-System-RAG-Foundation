#!/usr/bin/env python3
"""Debug encryption key"""

from modules.layered_memory_v1 import LayeredMemoryV1, MEMORY_ENCRYPTION_KEY
from cryptography.fernet import Fernet

print(f"Global encryption key: {MEMORY_ENCRYPTION_KEY}")

# Create memory manager
memory = LayeredMemoryV1()

print(f"Long-term encryption key: {memory.long_term.cipher._signing_key}")

# Test encryption/decryption
test_content = "This is a test"
print(f"Original content: {test_content}")

# Encrypt with long-term cipher
encrypted = memory.long_term._encrypt(test_content)
print(f"Encrypted: {encrypted}")

# Decrypt with long-term cipher
decrypted = memory.long_term._decrypt(encrypted)
print(f"Decrypted: {decrypted}")

# Test with global key
global_cipher = Fernet(MEMORY_ENCRYPTION_KEY)
encrypted_global = global_cipher.encrypt(test_content.encode())
print(f"Encrypted with global key: {encrypted_global}")

decrypted_global = global_cipher.decrypt(encrypted_global).decode()
print(f"Decrypted with global key: {decrypted_global}")
