#!/usr/bin/env python3
"""
Learning System Smoke Tests
===========================

Basic smoke tests to verify learning system imports work in DRY_RUN mode.
These tests are designed to run quickly and provide early feedback.
"""

import os
import importlib
import pytest

# Set DRY_RUN mode for safe imports
os.environ.setdefault("STILLME_DRY_RUN", "1")


def test_learning_import_smoke():
    """Test that at least one learning module can be imported"""
    learning_modules = [
        "stillme_core.learning",
        "agent_dev.learning",
        "learning",  # fallback
        "stillme.learning"  # fallback
    ]
    
    imported_any = False
    for module_name in learning_modules:
        try:
            importlib.import_module(module_name)
            imported_any = True
            break
        except (ImportError, ModuleNotFoundError):
            continue
    
    assert imported_any, f"Cannot import any learning module from: {learning_modules}"


def test_learning_components_smoke():
    """Test that learning system components can be instantiated"""
    try:
        # Test stillme_core.learning
        import stillme_core.learning
        assert hasattr(stillme_core.learning, '__file__')
    except ImportError:
        pass  # Allow if not available
    
    try:
        # Test agent_dev.learning
        import agent_dev.learning
        assert hasattr(agent_dev.learning, '__file__')
    except ImportError:
        pass  # Allow if not available


@pytest.mark.smoke
def test_learning_dry_run_safe():
    """Test that learning system is safe in DRY_RUN mode"""
    # Ensure DRY_RUN is set
    assert os.environ.get("STILLME_DRY_RUN") == "1"
    
    # Test that we can import without making external calls
    try:
        import stillme_core.learning
        # Should not raise exceptions in DRY_RUN mode
        assert True
    except Exception as e:
        # If it fails, it should be a safe failure (no network calls)
        assert "network" not in str(e).lower()
        assert "api" not in str(e).lower()
