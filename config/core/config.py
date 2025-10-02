"""
Core Configuration - Configuration cho StillMe Core system

This module provides core system configuration:
- AI model settings
- Performance configuration
- Core system parameters

Author: StillMe AI Team
Version: 2.0.0
"""

import os
from dataclasses import dataclass
from typing import Any


@dataclass
class CoreConfig:
    """Core system configuration"""

    # AI Model settings
    default_model: str = os.getenv("DEFAULT_MODEL", "gemma2:2b")
    model_chooser: str = os.getenv("MODEL_CHOOSER", "auto")
    keep_warm_sec: int = int(os.getenv("KEEP_WARM_SEC", "600"))

    # Performance settings
    max_concurrent_tasks: int = int(os.getenv("MAX_CONCURRENT_TASKS", "10"))
    task_timeout: int = int(os.getenv("TASK_TIMEOUT", "300"))

    # Core system
    repo_root: str = os.getenv("REPO_ROOT", os.getcwd())
    sandbox_dir: str = os.getenv("SANDBOX_DIR", os.path.join(os.getcwd(), ".sandbox"))

    # Git settings
    git_user: str = os.getenv("GIT_USER", "agentdev")
    git_email: str = os.getenv("GIT_EMAIL", "agentdev@example.com")

    @classmethod
    def from_env(cls) -> "CoreConfig":
        """Create CoreConfig from environment variables"""
        return cls()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "default_model": self.default_model,
            "model_chooser": self.model_chooser,
            "keep_warm_sec": self.keep_warm_sec,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "task_timeout": self.task_timeout,
            "repo_root": self.repo_root,
            "sandbox_dir": self.sandbox_dir,
            "git_user": self.git_user,
            "git_email": self.git_email
        }
