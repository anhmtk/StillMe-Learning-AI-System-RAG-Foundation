"""
System-status specific citation policy tests.

CRITICAL:
- For system status / learning sources queries, CitationRequired must NOT allow "[general knowledge]".
- If telemetry context is available, it may auto-patch with "[system telemetry]".
"""

from backend.validators.citation import CitationRequired


def test_system_status_forbids_general_knowledge_citation():
    v = CitationRequired(required=True)
    res = v.run(
        answer="There are 7 learning sources and no errors. [general knowledge]",
        ctx_docs=[],
        is_philosophical=False,
        user_question="How many learning sources do you have right now? Any errors?",
        context=None,
    )
    assert res.passed is False
    assert "forbidden_general_knowledge_for_system_status" in res.reasons


def test_system_status_auto_patches_system_telemetry_citation_when_available():
    v = CitationRequired(required=True)
    telemetry_doc = {
        "document": "REAL-TIME SYSTEM STATUS (telemetry)\nRSS feeds_total=22\nRSS feeds_failed=3",
        "metadata": {"source": "SYSTEM_TELEMETRY"},
    }
    res = v.run(
        answer="RSS has 22 feeds total, 19 OK, 3 failed.",
        ctx_docs=[telemetry_doc],
        is_philosophical=False,
        user_question="hiện giờ bạn có bao nhiêu nguồn học tập? có nguồn nào bị lỗi ko?",
        context={"system_telemetry": True},
    )
    assert res.passed is True
    assert res.patched_answer is not None
    assert "[system telemetry]" in res.patched_answer

