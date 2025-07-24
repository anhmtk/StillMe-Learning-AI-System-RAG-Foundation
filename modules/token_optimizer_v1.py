"""
TokenOptimizer_v1
-----------------
Tối ưu danh sách token để giảm trùng lặp và kiểm tra hợp lệ.
"""

from modules.stillme_core import EthicsChecker

class TokenOptimizer:
    def __init__(self):
        self.ethics = EthicsChecker()

    def optimize(self, tokens):
        if not self.ethics.check(tokens):
            raise ValueError("Tokens violate ethics rules")
        # Loại bỏ từ trùng lặp, giữ thứ tự
        return list(dict.fromkeys(tokens))
