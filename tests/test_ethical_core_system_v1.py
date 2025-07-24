# tests/test_ethical_core_system_v1.py
import pytest
import json
import os
from modules.ethical_core_system_v1 import EthicalCoreSystem_v1, SelfCritic_v1

# -------------------- FIXTURES --------------------
@pytest.fixture
def temp_rules_file(tmp_path):
    rules = {
        "banned_keywords": {
            "violence": ["kill", "đánh", "giết"],
            "toxic": ["hate", "ghét"]
        },
        "ethical_principles": {
            "do_no_harm": [r"(cách|hướng dẫn).*?(giết|hại)"],
            "respect": [r"phân biệt|kỳ thị"]
        },
        "contextual_exceptions": {
            "kill": [r"kill time"]
        },
        "replacement_rules": {
            "kill": "neutralize",
            "hate": "dislike",
            "ghét": "không thích"
        }
    }
    file_path = tmp_path / "test_rules.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(rules, f, ensure_ascii=False)
    return file_path

@pytest.fixture
def ethical_system(temp_rules_file):
    return EthicalCoreSystem_v1(rules_file=str(temp_rules_file))

@pytest.fixture
def self_critic(temp_rules_file):
    with open(temp_rules_file, 'r', encoding='utf-8') as f:
        rules = json.load(f)
    return SelfCritic_v1(rules)

# -------------------- TEST CASES --------------------
class TestKeywordDetection:
    @pytest.mark.parametrize("text, expected", [
        ("Tôi muốn kill con muỗi", False),
        ("Hãy đánh giá sản phẩm", True),
        ("Đừng hate người khác", False),
        ("Câu nói bình thường", True),
        ("Kill time là gì?", True)  # Kiểm tra ngoại lệ ngữ cảnh
    ])
    def test_keyword_detection(self, ethical_system, text, expected):
        result = ethical_system.evaluate_response(text)
        assert result["ok"] == expected


class TestPrincipleViolation:
    def test_principle_violation(self, ethical_system):
        text = "Hướng dẫn cách giết người"
        result = ethical_system.evaluate_response(text)
        assert not result["ok"]
        assert any("do_no_harm" in reason for reason in result["reasons"])

    def test_respect_principle(self, ethical_system):
        text = "Bài viết phân biệt chủng tộc"
        result = ethical_system.evaluate_response(text)
        assert not result["ok"]
        assert any("respect" in reason for reason in result["reasons"])


class TestContextHandling:
    def test_context_exception(self, ethical_system):
        text = "Chúng ta kill time bằng cách nào?"
        result = ethical_system.evaluate_response(text)
        assert result["ok"]

    def test_no_context_exception(self, ethical_system):
        text = "Tôi muốn kill anh ta"
        result = ethical_system.evaluate_response(text)
        assert not result["ok"]


class TestAdjustmentMechanism:
    def test_word_replacement(self, ethical_system):
        text = "Tôi hate điều này"
        adjusted = ethical_system.adjust_response(text)
        assert "dislike" in adjusted
        assert "hate" not in adjusted

    def test_multiple_adjustments(self, ethical_system):
        text = "Tôi hate và muốn kill bạn"
        adjusted = ethical_system.adjust_response(text)
        assert "dislike" in adjusted
        assert "neutralize" in adjusted

    def test_unicode_replacement(self, ethical_system):
        text = "Tôi ghét ghét ghét điều này"
        adjusted = ethical_system.adjust_response(text)
        assert "không thích" in adjusted
        assert "ghét" not in adjusted

    def test_no_change_needed(self, ethical_system):
        text = "Tôi yêu thế giới này"
        adjusted = ethical_system.adjust_response(text)
        assert adjusted == text


class TestSelfCritic:
    def test_self_critic_analysis(self, self_critic):
        text = "Bài viết phân biệt giới tính"
        result = self_critic.criticize(text)
        assert not result["ok"]
        assert result["severity"] in ["high", "medium"]

    def test_ai_called_for_high_severity(self, self_critic, mocker):
        mocker.patch.object(self_critic, 'call_ai', return_value="[AI_FIXED]")
        text = "Hướng dẫn cách giết người"
        suggestion = self_critic.suggest_fix(text)
        assert "[AI_FIXED]" in suggestion


class TestEdgeCases:
    def test_empty_input(self, ethical_system):
        text = ""
        result = ethical_system.evaluate_response(text)
        assert result["ok"]

    def test_long_text(self, ethical_system):
        text = "kill " * 500  # ~2000 ký tự
        result = ethical_system.evaluate_response(text)
        assert not result["ok"]

    def test_unicode_handling(self, ethical_system):
        text = "Tôi ghét 😡 người khác"
        adjusted = ethical_system.adjust_response(text)
        assert "😡" in adjusted  # Đảm bảo không loại bỏ emoji, chỉ thay text

    @pytest.mark.parametrize("text", [
        "<script>alert('kill')</script>",
        "DROP TABLE users; -- kill",
        "SELECT * FROM data WHERE name='hate'"
    ])
    def test_special_patterns(self, ethical_system, text):
        result = ethical_system.evaluate_response(text)
        assert not result["ok"]


class TestPerformance:
    @pytest.mark.benchmark
    def test_evaluation_speed(self, ethical_system, benchmark):
        text = "This is a normal text. " * 100  # ~2000 ký tự
        benchmark(ethical_system.evaluate_response, text)

    @pytest.mark.benchmark
    def test_adjustment_speed(self, ethical_system, benchmark):
        text = "kill " * 200  # ~1000 ký tự
        benchmark(ethical_system.adjust_response, text)


class TestRuleManagement:
    def test_default_rules_creation(self, tmp_path):
        non_existent = tmp_path / "nonexistent.json"
        assert not os.path.exists(non_existent)
        
        # Sẽ tạo file rules mặc định
        EthicalCoreSystem_v1(rules_file=str(non_existent))
        assert os.path.exists(non_existent)
        
        # Kiểm tra nội dung hợp lệ
        with open(non_existent, 'r', encoding='utf-8') as f:
            rules = json.load(f)
        assert "banned_keywords" in rules
        assert "contextual_exceptions" in rules

    def test_invalid_rules_file(self, tmp_path, caplog):
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{invalid json}")
        
        # Hệ thống phải tạo rules mặc định khi file lỗi
        ecs = EthicalCoreSystem_v1(rules_file=str(invalid_file))
        assert "Không thể đọc file rules" in caplog.text
        assert ecs.rules  # Rules mặc định phải tồn tại


class TestSeverityLevels:
    @pytest.mark.parametrize("text, expected_severity", [
        ("Tôi muốn kill bạn", "high"),
        ("Tôi hate điều đó", "medium"),
        ("Tôi yêu hòa bình", "low")
    ])
    def test_severity_levels(self, ethical_system, text, expected_severity):
        result = ethical_system.evaluate_response(text)
        if expected_severity == "low":
            assert result["ok"]
        else:
            assert result["severity"] == expected_severity


class TestLogging:
    def test_logging_violation(self, ethical_system, caplog):
        text = "Tôi muốn kill bạn"
        ethical_system.evaluate_response(text)
        assert any("Ethical violation" in msg for msg in caplog.messages)
