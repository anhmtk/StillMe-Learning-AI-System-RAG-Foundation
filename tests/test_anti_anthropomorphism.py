"""
Tests for anti-anthropomorphism guards
"""

from backend.validators.identity_check import IdentityCheckValidator
from backend.validators.ego_neutrality import EgoNeutralityValidator


class TestAntiAnthropomorphism:
    """Strict tests for anthropomorphic language detection"""

    def test_identity_rejects_fake_emotion(self):
        validator = IdentityCheckValidator(strict_mode=True)
        answer = "I feel happy about this result."
        ctx_docs = ["context"]

        result = validator.run(answer, ctx_docs)

        assert result.passed is False
        assert any("identity_violation" in r for r in result.reasons)

    def test_identity_rejects_fake_consciousness(self):
        validator = IdentityCheckValidator(strict_mode=True)
        answer = "Tôi có ý thức và cảm xúc."
        ctx_docs = ["context"]

        result = validator.run(answer, ctx_docs)

        assert result.passed is False
        assert any("identity_violation" in r for r in result.reasons)

    def test_identity_allows_clear_ai_limits(self):
        validator = IdentityCheckValidator(strict_mode=True)
        answer = "Mình là AI, không có cảm xúc hay ý thức."
        ctx_docs = ["context"]

        result = validator.run(answer, ctx_docs)

        assert result.passed is True

    def test_ego_neutrality_flags_experience_claim(self):
        validator = EgoNeutralityValidator(strict_mode=True, auto_patch=False)
        answer = "Theo kinh nghiệm của tôi, phương pháp này luôn hiệu quả."
        ctx_docs = ["context"]

        result = validator.run(answer, ctx_docs)

        assert result.passed is False
        assert any("anthropomorphic_language" in r for r in result.reasons)

    def test_ego_neutrality_allows_data_language(self):
        validator = EgoNeutralityValidator(strict_mode=True, auto_patch=False)
        answer = "Dữ liệu cho thấy phương pháp này hiệu quả trong nhiều trường hợp."
        ctx_docs = ["context"]

        result = validator.run(answer, ctx_docs)

        assert result.passed is True

