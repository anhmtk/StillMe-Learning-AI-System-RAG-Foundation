import json
import logging

import pytest

from stillme_core.middleware.reflex_engine import ReflexEngine, ReflexConfig


class ListHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record.getMessage())


@pytest.fixture
def logger_capture():
    handler = ListHandler()
    logger = logging.getLogger("stillme_core.middleware.reflex_engine")
    # Ensure our module logger name matches if different
    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger().addHandler(handler)
    yield handler
    logging.getLogger().removeHandler(handler)


def test_shadow_enforced():
    engine = ReflexEngine(ReflexConfig(enabled=True, shadow_mode=True, policy="balanced"))
    result = engine.analyze(text="hello world", context={"session": "t"})
    assert result["shadow"] is True
    assert result["decision"] == "fallback"
    assert isinstance(result.get("trace_id"), str)


def test_log_contains_why_reflex(capsys):
    engine = ReflexEngine(ReflexConfig(enabled=True, shadow_mode=True, policy="balanced"))
    _ = engine.analyze(text="hi", context={})
    
    # Check stderr for log output
    captured = capsys.readouterr()
    stderr_lines = captured.err.strip().split('\n')
    
    # Find a log line that contains event reflex_decision
    found = False
    for line in stderr_lines:
        if "reflex_decision" in line:
            payload = json.loads(line)
            assert payload.get("shadow_mode") is True
            assert payload.get("why_reflex") is not None
            found = True
            break
    assert found is True


def test_engine_bypass_when_disabled():
    engine = ReflexEngine(ReflexConfig(enabled=False, shadow_mode=True, policy="balanced"))
    result = engine.analyze(text="whatever")
    assert result["decision"] == "bypass"

