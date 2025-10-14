"""
StillMe Core
------------
Cung cấp các tiện ích lõi: SecureMemoryManager, AuditLogger, EthicsChecker.
"""


class SecureMemoryManager:
    def __init__(self):
        self.data = {}

    def store(self, key, value):
        self.data[key] = value

    def retrieve(self, key):
        return self.data.get(key, None)


class AuditLogger:
    def __init__(self, log_file="audit.log"):
        self.log_file = log_file

    def log(self, message: str):
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"[LOG] {message}\n")

    def log_error(self, message: str):
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"[ERROR] {message}\n")


class EthicsChecker:
    def check(self, payload) -> bool:
        """
        Kiểm tra payload có vi phạm rule không.
        """
        if isinstance(payload, list):
            payload = " ".join(payload)
        lower_payload = payload.lower()
        return "violation" not in lower_payload