"""
Code Review Tool - Helps community contributors write quality code

This module provides automated code review capabilities:
- Ruff linting analysis
- Basic security checks
- PR comment generation (educational, non-blocking)

Principles:
- Help, don't automate
- Educate contributors
- Low risk, no auto-changes
- Focus on StillMe's codebase only
"""

from .analyzer import CodeAnalyzer
from .github_client import GitHubPRClient
from .comment_formatter import CommentFormatter
from .config import CodeReviewConfig

__all__ = [
    "CodeAnalyzer",
    "GitHubPRClient",
    "CommentFormatter",
    "CodeReviewConfig",
]
