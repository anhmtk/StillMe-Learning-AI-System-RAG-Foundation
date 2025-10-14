import logging

import git

logger = logging.getLogger("StillmeCore-GitManager")


class GitManager:
    def __init__(self, repo_path: str = "."):
        try:
            self.repo = git.Repo(repo_path)
            logger.info("GitManager initialized.")
        except git.InvalidGitRepositoryError:
            logger.error(
                f"Path {repo_path} is not a Git repository. Please initialize git."
            )
            exit(1)

    def create_and_checkout_branch(self, branch_name: str) -> bool:
        try:
            if branch_name in self.repo.heads:
                self.repo.git.checkout(branch_name)
                logger.info(f"Checked out existing branch: {branch_name}")
            else:
                self.repo.git.checkout("-b", branch_name)
                logger.info(f"Creating and checking out branch: {branch_name}")
            return True
        except Exception as e:
            logger.error(f"Error creating/checking out branch {branch_name}: {e}")
            return False

    def commit_changes(self, message: str) -> bool:
        try:
            self.repo.git.add(A=True)  # Add all changes
            if self.repo.is_dirty(
                untracked_files=True
            ):  # Check if there are actual changes to commit
                self.repo.index.commit(message)
                logger.info(f"Committed changes: {message}")
                return True
            else:
                logger.info("No changes to commit.")
                return False
        except Exception as e:
            logger.error(f"Error committing changes: {e}")
            return False

    def get_current_branch(self) -> str:
        return self.repo.active_branch.name

    def revert_uncommitted_changes(self):
        try:
            self.repo.git.reset("--hard")
            self.repo.git.clean("-fd")  # Clean untracked files and directories
            logger.info("Reverted all uncommitted changes and cleaned untracked files.")
        except Exception as e:
            logger.error(f"Error reverting changes: {e}")