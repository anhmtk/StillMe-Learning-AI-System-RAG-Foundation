"""
GitHub API Client for PR Comments
"""

import logging
from typing import List, Optional
import requests

from .config import CodeReviewConfig

logger = logging.getLogger(__name__)


class GitHubPRClient:
    """Client for interacting with GitHub PRs via API"""

    def __init__(self, config: CodeReviewConfig):
        self.config = config
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {config.github_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "StillMe-CodeReview-Tool",
        }
        logger.info("GitHubPRClient initialized")

    def post_pr_comments(
        self, pr_number: int, comments: List[str], repo: Optional[str] = None
    ) -> bool:
        """
        Post comments to a GitHub PR

        Args:
            pr_number: PR number
            comments: List of comment strings
            repo: Repository in format "owner/repo" (defaults to config)

        Returns:
            True if successful, False otherwise
        """
        if not self.config.enabled:
            logger.debug("Code review disabled, skipping PR comments")
            return False

        if not self.config.github_token:
            logger.warning("GitHub token not configured, cannot post comments")
            return False

        if not comments:
            logger.debug("No comments to post")
            return True

        repo = repo or self.config.github_repo

        # Limit comments to max_comments_per_pr
        comments_to_post = comments[: self.config.max_comments_per_pr]

        if len(comments) > self.config.max_comments_per_pr:
            logger.warning(
                f"Limiting comments from {len(comments)} to {self.config.max_comments_per_pr}"
            )

        success_count = 0

        for i, comment in enumerate(comments_to_post):
            # Truncate if too long
            if len(comment) > self.config.max_comment_length:
                comment = comment[: self.config.max_comment_length - 3] + "..."
                logger.warning(
                    f"Comment {i + 1} truncated to {self.config.max_comment_length} chars"
                )

            if self._post_single_comment(pr_number, comment, repo):
                success_count += 1
            else:
                logger.error(f"Failed to post comment {i + 1}")

        logger.info(
            f"Posted {success_count}/{len(comments_to_post)} comments to PR #{pr_number}"
        )
        return success_count > 0

    def _post_single_comment(self, pr_number: int, body: str, repo: str) -> bool:
        """Post a single comment to PR"""
        url = f"{self.base_url}/repos/{repo}/issues/{pr_number}/comments"

        payload = {"body": body}

        try:
            response = requests.post(
                url, headers=self.headers, json=payload, timeout=10
            )

            if response.status_code == 201:
                logger.debug(f"Successfully posted comment to PR #{pr_number}")
                return True
            else:
                logger.error(
                    f"Failed to post comment: {response.status_code} - {response.text}"
                )
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Error posting comment: {e}")
            return False

    def get_pr_info(self, pr_number: int, repo: Optional[str] = None) -> Optional[dict]:
        """
        Get PR information

        Args:
            pr_number: PR number
            repo: Repository in format "owner/repo"

        Returns:
            PR info dict or None if error
        """
        repo = repo or self.config.github_repo
        url = f"{self.base_url}/repos/{repo}/pulls/{pr_number}"

        try:
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get PR info: {response.status_code}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting PR info: {e}")
            return None
