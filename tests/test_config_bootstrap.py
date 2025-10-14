#!/usr/bin/env python3
"""
Config Bootstrap Tests
======================

Tests for the config bootstrap functionality to ensure
sample config files are created when missing.
"""

import os
import shutil
import pathlib
import tempfile
import pytest
import yaml

from stillme_core.config_bootstrap import (
    ensure_minimum_config,
    check_config_health,
    _create_config_file,
    _create_env_from_example
)


def test_bootstrap_creates_defaults(tmp_path, monkeypatch):
    """Test that bootstrap creates default config files when missing"""
    # Setup temporary directory structure
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    config_dir = repo_root / "config"
    config_dir.mkdir()
    
    # Change to repo directory
    monkeypatch.chdir(repo_root)
    
    # Create env.example
    env_example = repo_root / "env.example"
    env_example.write_text("STILLME_DRY_RUN=1\nOPENAI_API_KEY=sk-xxxx\n")
    
    # Run bootstrap
    ensure_minimum_config()
    
    # Check that required files were created
    assert (config_dir / "reflection.yaml").exists()
    assert (config_dir / "runtime_base_url.txt").exists()
    assert (config_dir / "env" / "dev.yaml").exists()
    assert (config_dir / "env" / "prod.yaml").exists()
    assert (config_dir / "env" / "staging.yaml").exists()
    assert (repo_root / ".env").exists()


def test_bootstrap_does_not_overwrite_existing(tmp_path, monkeypatch):
    """Test that bootstrap doesn't overwrite existing config files"""
    # Setup temporary directory structure
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    config_dir = repo_root / "config"
    config_dir.mkdir()
    
    # Change to repo directory
    monkeypatch.chdir(repo_root)
    
    # Create existing config file
    existing_config = config_dir / "reflection.yaml"
    existing_content = "existing: content\ncustom: value\n"
    existing_config.write_text(existing_content)
    
    # Create env.example
    env_example = repo_root / "env.example"
    env_example.write_text("STILLME_DRY_RUN=1\n")
    
    # Run bootstrap
    ensure_minimum_config()
    
    # Check that existing file wasn't overwritten
    assert existing_config.read_text() == existing_content


def test_bootstrap_creates_env_from_example(tmp_path, monkeypatch):
    """Test that bootstrap creates .env from env.example"""
    # Setup temporary directory structure
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    config_dir = repo_root / "config"
    config_dir.mkdir()
    
    # Change to repo directory
    monkeypatch.chdir(repo_root)
    
    # Create env.example with specific content
    env_example_content = """# Test env example
STILLME_DRY_RUN=1
OPENAI_API_KEY=sk-xxxx
RUNTIME_BASE_URL=http://localhost:8000
"""
    env_example = repo_root / "env.example"
    env_example.write_text(env_example_content)
    
    # Run bootstrap
    ensure_minimum_config()
    
    # Check that .env was created with content from env.example
    env_file = repo_root / ".env"
    assert env_file.exists()
    
    env_content = env_file.read_text()
    assert "GENERATED FROM env.example" in env_content
    assert "STILLME_DRY_RUN=1" in env_content
    assert "OPENAI_API_KEY=sk-xxxx" in env_content


def test_config_health_check(tmp_path, monkeypatch):
    """Test config health check functionality"""
    # Setup temporary directory structure
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    config_dir = repo_root / "config"
    config_dir.mkdir()
    
    # Change to repo directory
    monkeypatch.chdir(repo_root)
    
    # Create some config files but not all
    (config_dir / "reflection.yaml").write_text("test: content")
    (config_dir / "runtime_base_url.txt").write_text("http://localhost:8000")
    
    # Create env.example but not .env
    env_example = repo_root / "env.example"
    env_example.write_text("STILLME_DRY_RUN=1\n")
    
    # Run health check
    health = check_config_health()
    
    # Check results
    assert health["config_dir_exists"] is True
    assert health["env_file_exists"] is False
    assert health["env_example_exists"] is True
    assert health["required_files"]["reflection.yaml"]["exists"] is True
    assert health["required_files"]["env/dev.yaml"]["exists"] is False
    assert len(health["issues"]) > 0
    assert "Missing config file: env/dev.yaml" in health["issues"]


def test_create_config_file_yaml(tmp_path):
    """Test _create_config_file with YAML content"""
    config_file = tmp_path / "test.yaml"
    content = {"test": {"key": "value", "nested": {"data": 123}}}
    
    _create_config_file(config_file, content)
    
    assert config_file.exists()
    content_text = config_file.read_text()
    assert "GENERATED SAMPLE CONFIG" in content_text
    assert "test:" in content_text
    assert "key: value" in content_text


def test_create_config_file_text(tmp_path):
    """Test _create_config_file with text content"""
    config_file = tmp_path / "test.txt"
    content = "http://localhost:8000"
    
    _create_config_file(config_file, content)
    
    assert config_file.exists()
    content_text = config_file.read_text()
    assert "GENERATED SAMPLE CONFIG" in content_text
    assert "http://localhost:8000" in content_text


def test_create_env_from_example(tmp_path):
    """Test _create_env_from_example function"""
    example_file = tmp_path / "env.example"
    env_file = tmp_path / ".env"
    
    example_content = """# Test example
STILLME_DRY_RUN=1
OPENAI_API_KEY=sk-xxxx
"""
    example_file.write_text(example_content)
    
    _create_env_from_example(example_file, env_file)
    
    assert env_file.exists()
    env_content = env_file.read_text()
    assert "GENERATED FROM env.example" in env_content
    assert "STILLME_DRY_RUN=1" in env_content
    assert "OPENAI_API_KEY=sk-xxxx" in env_content


def test_bootstrap_in_dry_run_mode(tmp_path, monkeypatch):
    """Test that bootstrap works correctly in DRY_RUN mode"""
    # Set DRY_RUN environment variable
    monkeypatch.setenv("STILLME_DRY_RUN", "1")
    
    # Setup temporary directory structure
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    config_dir = repo_root / "config"
    config_dir.mkdir()
    
    # Change to repo directory
    monkeypatch.chdir(repo_root)
    
    # Create env.example
    env_example = repo_root / "env.example"
    env_example.write_text("STILLME_DRY_RUN=1\n")
    
    # Run bootstrap
    ensure_minimum_config()
    
    # Check that files were created (should work in DRY_RUN mode)
    assert (config_dir / "reflection.yaml").exists()
    assert (repo_root / ".env").exists()
    
    # Check that DRY_RUN is set in .env
    env_content = (repo_root / ".env").read_text()
    assert "STILLME_DRY_RUN=1" in env_content


@pytest.mark.smoke
def test_bootstrap_smoke():
    """Smoke test for config bootstrap - should not crash"""
    # This test ensures the bootstrap module can be imported and basic functions work
    from stillme_core.config_bootstrap import ensure_minimum_config, check_config_health
    
    # Should not crash when called
    try:
        health = check_config_health()
        assert isinstance(health, dict)
        assert "config_dir_exists" in health
        assert "required_files" in health
        assert "issues" in health
    except Exception as e:
        pytest.fail(f"Config bootstrap smoke test failed: {e}")


if __name__ == "__main__":
    # Run tests when called directly
    pytest.main([__file__, "-v"])
