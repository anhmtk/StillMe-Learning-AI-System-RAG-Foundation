"""
Configuration for Code Review Tool
"""

import os
from dataclasses import dataclass
from typing import List


@dataclass
class CodeReviewConfig:
    """Configuration for code review tool"""

    # Feature flag
    enabled: bool = False

    # Ruff configuration
    ruff_check_enabled: bool = True
    ruff_format_check_enabled: bool = True
    ruff_exclude_patterns: List[str] = None

    # Security checks
    security_checks_enabled: bool = True

    # Comment limits
    max_comments_per_pr: int = 20
    max_comment_length: int = 5000

    # Thresholds
    min_severity_to_comment: str = "warning"  # error, warning, info

    # GitHub configuration
    github_token: str = None
    github_repo: str = None

    def __post_init__(self):
        """Initialize from environment variables"""
        if self.enabled is False:
            self.enabled = (
                os.getenv("ENABLE_CODE_REVIEW_COMMENTS", "false").lower() == "true"
            )

        if self.ruff_exclude_patterns is None:
            self.ruff_exclude_patterns = ["_graveyard", "__pycache__", ".git"]

        if self.github_token is None:
            self.github_token = os.getenv("GITHUB_TOKEN")

        if self.github_repo is None:
            # Default to StillMe repo
            self.github_repo = os.getenv(
                "GITHUB_REPOSITORY", "anhmtk/StillMe-Learning-AI-System-RAG-Foundation"
            )
