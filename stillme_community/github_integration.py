#!/usr/bin/env python3
"""
StillMe Community GitHub Integration
Tích hợp với GitHub Issues để đồng bộ proposals và voting
"""

import json
import os
import requests
from datetime import datetime
from typing import Any, Dict, List, Optional

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class GitHubIntegration:
    """Tích hợp với GitHub Issues cho community proposals"""
    
    def __init__(self, repo_owner: str = "stillme-ai", repo_name: str = "stillme_ai"):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.base_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
        
        if not self.github_token:
            logger.warning("⚠️ GITHUB_TOKEN not found. GitHub integration will be limited.")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get GitHub API headers"""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "StillMe-Community-Bot"
        }
        
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
        
        return headers
    
    def create_proposal_issue(
        self,
        title: str,
        description: str,
        learning_objectives: List[str],
        category: str,
        author: str,
        proposal_id: str
    ) -> Optional[str]:
        """Tạo GitHub Issue cho community proposal"""
        try:
            if not self.github_token:
                logger.warning("GitHub token not available. Skipping issue creation.")
                return None
            
            # Format issue body
            issue_body = f"""
## 🎯 Community Learning Proposal

**Proposed by:** @{author}  
**Category:** {category}  
**Proposal ID:** `{proposal_id}`

### 📝 Description
{description}

### 🎯 Learning Objectives
{chr(10).join(f"- {obj}" for obj in learning_objectives)}

### 🗳️ Voting Status
- **Upvotes:** 0 👍
- **Downvotes:** 0 👎
- **Status:** Voting in progress
- **Votes needed:** 50

### 📋 Instructions for Community
1. **Vote** by reacting with 👍 (upvote) or 👎 (downvote)
2. **Comment** with your thoughts and suggestions
3. **Share** with other community members

---
*This issue was automatically created from the community dashboard.*
            """.strip()
            
            # Create issue
            issue_data = {
                "title": f"🎯 [Community] {title}",
                "body": issue_body,
                "labels": ["community-proposal", f"category-{category}", "voting"]
            }
            
            response = requests.post(
                f"{self.base_url}/issues",
                headers=self._get_headers(),
                json=issue_data
            )
            
            if response.status_code == 201:
                issue_info = response.json()
                issue_url = issue_info["html_url"]
                issue_number = issue_info["number"]
                
                logger.info(f"✅ GitHub issue created: {issue_url}")
                return issue_url
            else:
                logger.error(f"❌ Failed to create GitHub issue: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error creating GitHub issue: {e}")
            return None
    
    def update_voting_status(
        self,
        issue_number: int,
        upvotes: int,
        downvotes: int,
        status: str
    ) -> bool:
        """Cập nhật voting status trên GitHub Issue"""
        try:
            if not self.github_token:
                logger.warning("GitHub token not available. Skipping issue update.")
                return False
            
            # Get current issue
            response = requests.get(
                f"{self.base_url}/issues/{issue_number}",
                headers=self._get_headers()
            )
            
            if response.status_code != 200:
                logger.error(f"❌ Failed to get issue {issue_number}: {response.text}")
                return False
            
            issue_data = response.json()
            current_body = issue_data["body"]
            
            # Update voting status in body
            updated_body = self._update_voting_in_body(
                current_body, upvotes, downvotes, status
            )
            
            # Update issue
            update_data = {
                "body": updated_body,
                "state": "open" if status == "voting" else "closed"
            }
            
            response = requests.patch(
                f"{self.base_url}/issues/{issue_number}",
                headers=self._get_headers(),
                json=update_data
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Updated voting status for issue {issue_number}")
                return True
            else:
                logger.error(f"❌ Failed to update issue {issue_number}: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error updating voting status: {e}")
            return False
    
    def _update_voting_in_body(
        self,
        body: str,
        upvotes: int,
        downvotes: int,
        status: str
    ) -> str:
        """Update voting information in issue body"""
        lines = body.split('\n')
        updated_lines = []
        
        for line in lines:
            if line.startswith("- **Upvotes:**"):
                updated_lines.append(f"- **Upvotes:** {upvotes} 👍")
            elif line.startswith("- **Downvotes:**"):
                updated_lines.append(f"- **Downvotes:** {downvotes} 👎")
            elif line.startswith("- **Status:**"):
                updated_lines.append(f"- **Status:** {status}")
            else:
                updated_lines.append(line)
        
        return '\n'.join(updated_lines)
    
    def add_voting_comment(
        self,
        issue_number: int,
        voter: str,
        vote_type: str,
        total_upvotes: int,
        total_downvotes: int
    ) -> bool:
        """Thêm comment khi có vote mới"""
        try:
            if not self.github_token:
                return False
            
            vote_emoji = "👍" if vote_type == "up" else "👎"
            comment_body = f"""
## 🗳️ New Vote Recorded

**Voter:** @{voter}  
**Vote:** {vote_emoji} {vote_type.title()}vote

**Current Status:**
- 👍 Upvotes: {total_upvotes}
- 👎 Downvotes: {total_downvotes}
- 📊 Progress: {total_upvotes}/50 votes needed

Thank you for participating in the community voting! 🎯
            """.strip()
            
            response = requests.post(
                f"{self.base_url}/issues/{issue_number}/comments",
                headers=self._get_headers(),
                json={"body": comment_body}
            )
            
            if response.status_code == 201:
                logger.info(f"✅ Added voting comment to issue {issue_number}")
                return True
            else:
                logger.error(f"❌ Failed to add comment: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error adding voting comment: {e}")
            return False
    
    def add_approval_comment(
        self,
        issue_number: int,
        proposal_title: str,
        total_votes: int
    ) -> bool:
        """Thêm comment khi proposal được approve"""
        try:
            if not self.github_token:
                return False
            
            comment_body = f"""
## 🎉 PROPOSAL APPROVED BY COMMUNITY!

**Lesson:** {proposal_title}  
**Final Votes:** {total_votes} 👍  
**Status:** ✅ **APPROVED**

StillMe AI will now start learning this content automatically! 🚀

Thank you to all community members who participated in the voting process! 🎯

---
*This proposal has been automatically approved based on community votes and is now in the learning queue.*
            """.strip()
            
            response = requests.post(
                f"{self.base_url}/issues/{issue_number}/comments",
                headers=self._get_headers(),
                json={"body": comment_body}
            )
            
            if response.status_code == 201:
                logger.info(f"✅ Added approval comment to issue {issue_number}")
                return True
            else:
                logger.error(f"❌ Failed to add approval comment: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error adding approval comment: {e}")
            return False
    
    def sync_proposals_to_issues(self, proposals: List[Dict[str, Any]]) -> Dict[str, int]:
        """Đồng bộ proposals sang GitHub Issues"""
        try:
            synced = {"created": 0, "updated": 0, "errors": 0}
            
            for proposal in proposals:
                try:
                    if not proposal.get("github_issue_url"):
                        # Create new issue
                        issue_url = self.create_proposal_issue(
                            title=proposal["title"],
                            description=proposal["description"],
                            learning_objectives=proposal["learning_objectives"],
                            category=proposal["category"],
                            author=proposal["author"],
                            proposal_id=proposal["id"]
                        )
                        
                        if issue_url:
                            # Update proposal with GitHub URL
                            # This would need to be implemented in the proposal manager
                            synced["created"] += 1
                        else:
                            synced["errors"] += 1
                    else:
                        # Update existing issue
                        issue_number = self._extract_issue_number(proposal["github_issue_url"])
                        if issue_number:
                            success = self.update_voting_status(
                                issue_number=issue_number,
                                upvotes=proposal["upvotes"],
                                downvotes=proposal["downvotes"],
                                status=proposal["status"]
                            )
                            
                            if success:
                                synced["updated"] += 1
                            else:
                                synced["errors"] += 1
                
                except Exception as e:
                    logger.error(f"❌ Error syncing proposal {proposal.get('id', 'unknown')}: {e}")
                    synced["errors"] += 1
            
            logger.info(f"📊 GitHub sync completed: {synced}")
            return synced
            
        except Exception as e:
            logger.error(f"❌ Error syncing proposals to GitHub: {e}")
            return {"created": 0, "updated": 0, "errors": 1}
    
    def _extract_issue_number(self, issue_url: str) -> Optional[int]:
        """Extract issue number from GitHub URL"""
        try:
            # URL format: https://github.com/owner/repo/issues/123
            parts = issue_url.split('/')
            if 'issues' in parts:
                issue_index = parts.index('issues')
                if issue_index + 1 < len(parts):
                    return int(parts[issue_index + 1])
            return None
        except (ValueError, IndexError):
            return None
    
    def create_community_leaderboard_issue(self, contributors: List[Dict[str, Any]]) -> Optional[str]:
        """Tạo GitHub Issue cho community leaderboard"""
        try:
            if not self.github_token:
                return None
            
            # Format leaderboard
            leaderboard_body = """
## 🏆 StillMe AI Community Leaderboard

*Updated automatically every 24 hours*

### Top Contributors

            """.strip()
            
            for contributor in contributors[:10]:  # Top 10
                leaderboard_body += f"""
**#{contributor['rank']}** @{contributor['username']}
- 📝 Proposals: {contributor['proposals']}
- 🗳️ Votes Received: {contributor['votes_received']}
- 🎯 Total Votes Given: {contributor['total_votes']}

                """.strip()
            
            leaderboard_body += """

---
*This leaderboard is automatically generated from community activity.*
            """.strip()
            
            # Create or update leaderboard issue
            issue_data = {
                "title": "🏆 Community Leaderboard - StillMe AI",
                "body": leaderboard_body,
                "labels": ["community", "leaderboard", "automated"]
            }
            
            response = requests.post(
                f"{self.base_url}/issues",
                headers=self._get_headers(),
                json=issue_data
            )
            
            if response.status_code == 201:
                issue_info = response.json()
                logger.info(f"✅ Community leaderboard created: {issue_info['html_url']}")
                return issue_info["html_url"]
            else:
                logger.error(f"❌ Failed to create leaderboard issue: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error creating leaderboard issue: {e}")
            return None
    
    def get_github_issue_reactions(self, issue_number: int) -> Dict[str, int]:
        """Get reactions from GitHub issue (👍 👎)"""
        try:
            if not self.github_token:
                return {"upvotes": 0, "downvotes": 0}
            
            response = requests.get(
                f"{self.base_url}/issues/{issue_number}/reactions",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                reactions = response.json()
                upvotes = sum(1 for r in reactions if r["content"] == "+1")
                downvotes = sum(1 for r in reactions if r["content"] == "-1")
                
                return {"upvotes": upvotes, "downvotes": downvotes}
            else:
                logger.error(f"❌ Failed to get reactions: {response.text}")
                return {"upvotes": 0, "downvotes": 0}
                
        except Exception as e:
            logger.error(f"❌ Error getting GitHub reactions: {e}")
            return {"upvotes": 0, "downvotes": 0}


def main():
    """Test GitHub Integration"""
    print("🔗 Testing StillMe GitHub Integration...")
    
    # Initialize integration
    github = GitHubIntegration()
    
    # Test creating a proposal issue
    issue_url = github.create_proposal_issue(
        title="Test Community Proposal",
        description="This is a test proposal for StillMe AI learning",
        learning_objectives=[
            "Learn test automation",
            "Master testing frameworks",
            "Implement CI/CD testing"
        ],
        category="programming",
        author="test_user",
        proposal_id="test-123"
    )
    
    if issue_url:
        print(f"✅ GitHub issue created: {issue_url}")
    else:
        print("❌ Failed to create GitHub issue")
    
    print("🎉 GitHub Integration test completed!")


if __name__ == "__main__":
    main()
