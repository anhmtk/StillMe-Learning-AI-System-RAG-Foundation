# modules/secure_memory_manager.py
"""
SecureMemoryManager - Module quản lý bộ nhớ an toàn cho StillMeFramework.
Dữ liệu được mã hóa khi lưu ra file.
"""

from cryptography.fernet import Fernet
from pathlib import Path

class SecureMemoryManager:
    def __init__(self, file_path: str = "memory.enc", key_path: str = "memory.key"):
        self.file_path = Path(file_path)
        self.key_path = Path(key_path)
        self.key = self.load_or_create_key()
        self.cipher = Fernet(self.key)

    def load_or_create_key(self) -> bytes:
        """Tải key từ file hoặc tạo mới nếu chưa có."""
        if self.key_path.exists():
            return self.key_path.read_bytes()
        else:
            key = Fernet.generate_key()
            self.key_path.write_bytes(key)
            return key

    def save(self, data: str):
        """Mã hóa và lưu dữ liệu vào file."""
        encrypted = self.cipher.encrypt(data.encode("utf-8"))
        self.file_path.write_bytes(encrypted)

    def load(self) -> str:
        """Giải mã dữ liệu từ file."""
        if self.file_path.exists():
            encrypted = self.file_path.read_bytes()
            return self.cipher.decrypt(encrypted).decode("utf-8")
        return ""

    def clear(self):
        """Xóa dữ liệu bộ nhớ."""
        if self.file_path.exists():
            self.file_path.unlink()
