import importlib


def test_defaults_loaded(monkeypatch):
    monkeypatch.delenv("DEFAULT_MODE", raising=False)
    mod = importlib.import_module("stillme_core.config_defaults")
    assert mod.DEFAULT_MODE == "fast"


def test_env_override(monkeypatch):
    monkeypatch.setenv("DEFAULT_MODE", "think")
    # reload to pick new env
    mod = importlib.reload(importlib.import_module("stillme_core.config_defaults"))
    assert mod.DEFAULT_MODE == "think"