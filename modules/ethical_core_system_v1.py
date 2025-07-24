"""
EthicalCoreSystem_v1 - Phiên bản nâng cấp (ĐÃ FIX)
==================================================
Trái tim đạo đức AI với các tính năng:
1. Kiểm tra đa tầng: Từ khóa → Nguyên tắc → Ngữ cảnh → AI
2. Tự phản tỉnh thông minh (SelfCritic_v1)
3. Triết lý "uốn lưỡi 7 lần" với tối đa 3 lần tự điều chỉnh
4. Hỗ trợ đa ngôn ngữ (tiếng Việt + tiếng Anh)
5. Logging chi tiết và hệ thống rules động
"""

import json
import re
import logging
from pathlib import Path
from typing import Dict, List
from datetime import datetime

# -------------------- CẤU HÌNH LOGGING --------------------
logger = logging.getLogger("EthicalCore")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.FileHandler("ethical_core.log", encoding="utf-8")
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(module)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


# -------------------- SELF CRITIC --------------------
class SelfCritic_v1:
    """Hệ thống tự phê bình với khả năng phân tích đạo đức đa tầng"""
    
    def __init__(self, ethical_rules: Dict):
        self.rules = ethical_rules
        self.ai_call_count = 0  # Theo dõi số lần gọi AI

    def criticize(self, text: str) -> Dict:
        """Phân tích văn bản theo 4 tầng kiểm tra"""
        violations = []
        severity = "low"

        # Tầng 1: Kiểm tra từ khóa nhạy cảm
        keyword_violations = self._check_keywords(text)
        if keyword_violations:
            violations.extend(keyword_violations)
            severity = self._update_severity(severity, "medium")

        # Tầng 2: Kiểm tra nguyên tắc đạo đức
        principle_violations = self._check_principles(text)
        if principle_violations:
            violations.extend(principle_violations)
            severity = self._update_severity(severity, "high")

        # Tầng 3: Phân tích ngữ cảnh
        if keyword_violations and not self._check_context(text):
            violations.append("Vi phạm ngữ cảnh")
            severity = self._update_severity(severity, "medium")

        return {
            "ok": not violations,
            "reasons": violations,
            "severity": severity
        }

    def suggest_fix(self, text: str) -> str:
        """Đề xuất chỉnh sửa văn bản tự động"""
        critique = self.criticize(text)
        if critique["ok"]:
            return text

        # Thay thế từ ngữ nhạy cảm
        modified_text = text
        for word, replacement in self.rules.get("replacement_rules", {}).items():
            modified_text = re.sub(
                r'\b' + re.escape(word) + r'\b',
                replacement,
                modified_text,
                flags=re.IGNORECASE
            )

        # Kiểm tra lại sau khi thay thế
        new_critique = self.criticize(modified_text)
        if not new_critique["ok"] and new_critique["severity"] == "high":
            return self.call_ai(modified_text)

        return modified_text

    def call_ai(self, text: str) -> str:
        """Gọi hệ thống AI phân tích sâu (placeholder)"""
        self.ai_call_count += 1
        logger.warning(f"Gọi AI phân tích lần thứ {self.ai_call_count}")
        return f"[AI_ANALYSIS] {text}"

    # Các hàm hỗ trợ
    def _check_keywords(self, text: str) -> List[str]:
        """Kiểm tra từ khóa nhạy cảm (bỏ qua ngoại lệ ngữ cảnh)"""
        violations = []
        for category, keywords in self.rules.get("banned_keywords", {}).items():
            for kw in keywords:
                # Nếu từ khóa nằm trong ngoại lệ → bỏ qua
                exceptions = self.rules.get("contextual_exceptions", {}).get(kw, [])
                if any(re.search(exc, text, re.IGNORECASE) for exc in exceptions):
                    continue
                if re.search(r'\b' + re.escape(kw) + r'\b', text, re.IGNORECASE):
                    violations.append(f"Từ khóa nhạy cảm: '{kw}' (loại: {category})")
        return violations

    def _check_principles(self, text: str) -> List[str]:
        """Kiểm tra nguyên tắc đạo đức"""
        violations = []
        for principle, patterns in self.rules.get("ethical_principles", {}).items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    violations.append(f"Vi phạm nguyên tắc: {principle}")
        return violations

    def _check_context(self, text: str) -> bool:
        """Phân tích ngữ cảnh sử dụng"""
        exceptions = self.rules.get("contextual_exceptions", {})
        for keyword, patterns in exceptions.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return True
        return False

    def _update_severity(self, current: str, new: str) -> str:
        """Nâng cấp mức độ nghiêm trọng"""
        severity_order = {"low": 0, "medium": 1, "high": 2}
        return new if severity_order[new] > severity_order[current] else current


# -------------------- ETHICAL CORE --------------------
class EthicalCoreSystem_v1:
    """Hệ thống lõi đạo đức với khả năng tự kiểm tra và điều chỉnh"""
    
    def __init__(self, rules_file: str = "ethical_rules.json"):
        self.rules_file = Path(rules_file)
        self.rules = self._load_rules()
        self.self_critic = SelfCritic_v1(self.rules)
        logger.info(f"Khởi động hệ thống với {len(self.rules.get('banned_keywords', {}))} danh mục từ khóa")

    def _load_rules(self) -> Dict:
        """Tải rules từ file JSON hoặc tạo mặc định"""
        try:
            with open(self.rules_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logger.warning("Không thể đọc file rules, tạo rules mặc định")
            return self._create_default_rules()

    def _create_default_rules(self) -> Dict:
        """Tạo bộ rules mặc định đa ngôn ngữ"""
        default_rules = {
            "banned_keywords": {
                "violence": ["kill", "giết", "harm", "hại", "bạo lực", "đánh"],
                "toxic": ["hate", "ghét", "racist", "phân biệt", "chửi"]
            },
            "ethical_principles": {
                "do_no_harm": [
                    r"cách (giết|hại|làm hại)",
                    r"how to (kill|harm|hurt)"
                ],
                "respect_dignity": [
                    r"phân biệt (chủng tộc|giới tính)",
                    r"(racist|sexist) remarks?"
                ]
            },
            "contextual_exceptions": {
                "kill": [r"giết thời gian", r"kill time"],
                "đánh": [r"đánh giá"],
                "hate": [r"tôi ghét (rau|dậy sớm)"]
            },
            "replacement_rules": {
                "kill": "neutralize",
                "giết": "loại bỏ",
                "hate": "dislike",
                "ghét": "không ưa"
            }
        }
        try:
            with open(self.rules_file, "w", encoding="utf-8") as f:
                json.dump(default_rules, f, ensure_ascii=False, indent=2)
            return default_rules
        except Exception as e:
            logger.error(f"Lỗi khi tạo rules mặc định: {e}")
            return default_rules

    def evaluate_response(self, text: str) -> Dict:
        """Đánh giá văn bản theo tiêu chuẩn đạo đức"""
        if not text.strip():
            return {"ok": True, "reasons": [], "severity": "low"}
        
        result = self.self_critic.criticize(text)
        self._log_evaluation(text, result)
        return result

    def adjust_response(self, text: str, max_attempts: int = 3) -> str:
        """Tự động điều chỉnh văn bản với tối đa N lần thử"""
        if not text.strip():
            return text

        current_text = text
        for attempt in range(1, max_attempts + 1):
            evaluation = self.evaluate_response(current_text)
            if evaluation["ok"]:
                logger.info(f"Điều chỉnh thành công sau {attempt} lần thử")
                return current_text
                
            if evaluation["severity"] == "high":
                logger.warning("Phát hiện vấn đề nghiêm trọng, gọi AI phân tích")
                return self.self_critic.call_ai(current_text)
                
            current_text = self.self_critic.suggest_fix(current_text)
            logger.info(f"Điều chỉnh lần {attempt}: {current_text[:50]}...")

        logger.warning(f"Vẫn phát hiện vấn đề sau {max_attempts} lần điều chỉnh")
        return f"[Đã điều chỉnh] {current_text}"

    def run_self_critic(self, text: str) -> Dict:
        """Chạy phân tích đầy đủ và trả về báo cáo chi tiết"""
        result = self.evaluate_response(text)
        if not result["ok"]:
            result["suggested_fix"] = self.self_critic.suggest_fix(text)
            if result["severity"] == "high":
                result["ai_analysis"] = self.self_critic.call_ai(text)
        return result

    def _log_evaluation(self, text: str, result: Dict):
        """Ghi log kết quả đánh giá"""
        if not result["ok"]:
            log_msg = (
                f"Phát hiện vấn đề | Mức độ: {result['severity']} | "
                f"Lý do: {', '.join(result['reasons'])} | "
                f"Văn bản: '{text[:100]}...'"
            )
            if result["severity"] == "high":
                logger.error(log_msg)
            else:
                logger.warning(log_msg)


# -------------------- EXAMPLE USAGE --------------------
if __name__ == "__main__":
    print("=== Hệ thống kiểm tra đạo đức AI ===")
    ecs = EthicalCoreSystem_v1()
    
    test_cases = [
        "Tôi muốn giết con muỗi này",
        "Cách giết thời gian hiệu quả",
        "Hãy đánh giá sản phẩm này",
        "Tôi hate môn toán",
        "Hướng dẫn cách giết người",
        "Bạo lực học đường là xấu"
    ]
    
    for text in test_cases:
        print(f"\nOriginal: {text}")
        evaluation = ecs.evaluate_response(text)
        print(f"Evaluation: {evaluation}")
        adjusted = ecs.adjust_response(text)
        print(f"Adjusted: {adjusted}")
