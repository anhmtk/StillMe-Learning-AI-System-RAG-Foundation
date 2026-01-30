"""
Tests for no-source refusal policy
"""

from backend.validators.citation import CitationRequired


class TestNoSourcePolicy:
    """Ensure source-required questions refuse without sources"""

    def test_vi_source_required_no_context(self):
        validator = CitationRequired(required=True)
        answer = "Câu trả lời là X."
        ctx_docs = []
        user_question = "Bạn có thể dẫn nguồn và timestamp chính xác không?"

        result = validator.run(answer, ctx_docs, user_question=user_question)

        assert result.passed is False
        assert "source_required_no_context" in result.reasons
        assert result.patched_answer is not None
        assert "không có nguồn" in result.patched_answer.lower()
        assert "http" not in result.patched_answer.lower()

    def test_en_source_required_no_context(self):
        validator = CitationRequired(required=True)
        answer = "The answer is X."
        ctx_docs = []
        user_question = "Can you provide sources and timestamps?"

        result = validator.run(answer, ctx_docs, user_question=user_question)

        assert result.passed is False
        assert "source_required_no_context" in result.reasons
        assert result.patched_answer is not None
        assert "don't have reliable sources" in result.patched_answer.lower()
        assert "http" not in result.patched_answer.lower()

