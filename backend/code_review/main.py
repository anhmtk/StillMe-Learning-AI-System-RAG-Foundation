"""
Main entry point for Code Review Tool

Usage in GitHub Actions:
    python -m backend.code_review.main
"""

import os
import sys
import logging

from .config import CodeReviewConfig
from .analyzer import CodeAnalyzer
from .comment_formatter import CommentFormatter
from .github_client import GitHubPRClient

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for code review tool"""
    # Get GitHub context from environment
    pr_number = os.getenv("GITHUB_PR_NUMBER")
    github_repo = os.getenv("GITHUB_REPOSITORY")
    github_token = os.getenv("GITHUB_TOKEN")
    repo_path = os.getenv("GITHUB_WORKSPACE", ".")

    # Check if enabled
    config = CodeReviewConfig()
    if not config.enabled:
        logger.info("Code review comments disabled (ENABLE_CODE_REVIEW_COMMENTS=false)")
        return 0

    # Validate required inputs
    if not pr_number:
        logger.warning("GITHUB_PR_NUMBER not set, skipping PR comments")
        return 0

    if not github_token:
        logger.warning("GITHUB_TOKEN not set, cannot post PR comments")
        return 0

    # Override config with environment
    if github_repo:
        config.github_repo = github_repo
    if github_token:
        config.github_token = github_token

    logger.info(f"Starting code review for PR #{pr_number}")
    logger.info(f"Repository: {config.github_repo}")
    logger.info(f"Repo path: {repo_path}")

    try:
        # Initialize components
        analyzer = CodeAnalyzer(config)
        formatter = CommentFormatter()
        github_client = GitHubPRClient(config)

        # Run analysis
        logger.info("Running code analysis...")
        issues = analyzer.analyze(repo_path)

        if not issues:
            logger.info("No issues found, posting success comment")
            summary = formatter.format_summary_comment(0, 0)
            github_client.post_pr_comments(int(pr_number), [summary])
            return 0

        # Format issues into comments
        logger.info(f"Formatting {len(issues)} issues into comments...")
        comments = formatter.format_issues(issues)

        # Add summary comment
        files_affected = len(set(issue.file_path for issue in issues))
        summary = formatter.format_summary_comment(len(issues), files_affected)
        comments.insert(0, summary)

        # Post comments
        logger.info(f"Posting {len(comments)} comments to PR #{pr_number}...")
        success = github_client.post_pr_comments(int(pr_number), comments)

        if success:
            logger.info("Code review completed successfully")
            return 0
        else:
            logger.error("Failed to post some comments")
            return 1

    except Exception as e:
        logger.error(f"Error during code review: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
