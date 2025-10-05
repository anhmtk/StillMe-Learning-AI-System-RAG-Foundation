#!/usr/bin/env python3
"""
StillMe Community Voting Engine
Xử lý voting tự động và auto-approval cho community proposals
"""

import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import logging

from .proposal_manager import CommunityProposalManager
from .github_integration import GitHubIntegration

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class VotingEngine:
    """Engine xử lý voting và auto-approval cho community proposals"""
    
    def __init__(self):
        self.proposal_manager = CommunityProposalManager()
        self.github_integration = GitHubIntegration()
        
        # Voting configuration
        self.min_votes = 50
        self.vote_ratio_threshold = 2.0  # Upvotes must be 2x downvotes
        self.auto_approve = True
        self.check_interval = 3600  # Check every hour (in seconds)
        
        logger.info("🎯 Voting Engine initialized")
    
    def process_daily_voting(self) -> Dict[str, int]:
        """Xử lý voting hàng ngày - chạy tự động"""
        try:
            logger.info("🔄 Processing daily community voting...")
            
            # Get all active proposals
            active_proposals = self.proposal_manager.get_active_proposals()
            
            processed = {
                'checked': 0,
                'approved': 0,
                'expired': 0,
                'still_voting': 0,
                'errors': 0
            }
            
            for proposal in active_proposals:
                try:
                    processed['checked'] += 1
                    
                    # Check approval status
                    status = self.proposal_manager.check_approval_status(proposal['id'])
                    
                    if status == 'approved':
                        processed['approved'] += 1
                        self._handle_approved_proposal(proposal)
                        
                    elif status == 'expired':
                        processed['expired'] += 1
                        self._handle_expired_proposal(proposal)
                        
                    else:
                        processed['still_voting'] += 1
                        # Update GitHub issue if exists
                        self._update_github_voting_status(proposal)
                
                except Exception as e:
                    logger.error(f"❌ Error processing proposal {proposal.get('id', 'unknown')}: {e}")
                    processed['errors'] += 1
            
            logger.info(f"📊 Daily voting processed: {processed}")
            return processed
            
        except Exception as e:
            logger.error(f"❌ Error in daily voting processing: {e}")
            return {'checked': 0, 'approved': 0, 'expired': 0, 'still_voting': 0, 'errors': 1}
    
    def _handle_approved_proposal(self, proposal: Dict[str, Any]) -> None:
        """Xử lý proposal được approve"""
        try:
            logger.info(f"🎉 Proposal approved: {proposal['title']}")
            
            # Start learning process
            self._start_learning_process(proposal)
            
            # Notify community
            self._notify_community_approved(proposal)
            
            # Update GitHub issue
            self._update_github_approval(proposal)
            
            # Notify admin
            self._notify_admin_approved(proposal)
            
        except Exception as e:
            logger.error(f"❌ Error handling approved proposal: {e}")
    
    def _handle_expired_proposal(self, proposal: Dict[str, Any]) -> None:
        """Xử lý proposal hết hạn voting"""
        try:
            logger.info(f"⏰ Proposal expired: {proposal['title']}")
            
            # Notify community about expiration
            self._notify_community_expired(proposal)
            
            # Update GitHub issue
            self._update_github_expired(proposal)
            
        except Exception as e:
            logger.error(f"❌ Error handling expired proposal: {e}")
    
    def _start_learning_process(self, proposal: Dict[str, Any]) -> None:
        """Bắt đầu quá trình học cho proposal được approve"""
        try:
            # Import learning system
            from stillme_core.learning.silent_learning_system import SilentEvolutionaryLearningSystem
            
            # Create learning session
            learning_system = SilentEvolutionaryLearningSystem()
            session_id = learning_system.start_silent_learning(proposal['id'])
            
            if session_id:
                logger.info(f"🚀 Learning session started: {session_id}")
                
                # Update proposal with learning session ID
                self._update_proposal_learning_session(proposal['id'], session_id)
            else:
                logger.error(f"❌ Failed to start learning session for proposal {proposal['id']}")
                
        except Exception as e:
            logger.error(f"❌ Error starting learning process: {e}")
    
    def _update_proposal_learning_session(self, proposal_id: str, session_id: str) -> None:
        """Update proposal with learning session ID"""
        try:
            # This would need to be implemented in the proposal manager
            # For now, just log the session ID
            logger.info(f"📚 Proposal {proposal_id} -> Learning session {session_id}")
            
        except Exception as e:
            logger.error(f"❌ Error updating proposal learning session: {e}")
    
    def _notify_community_approved(self, proposal: Dict[str, Any]) -> None:
        """Thông báo cộng đồng khi proposal được approve"""
        try:
            from stillme_core.alerting.alerting_system import AlertingSystem
            
            alerting = AlertingSystem()
            
            message = f"""
🎉 **COMMUNITY PROPOSAL APPROVED!**

📚 **Lesson:** {proposal['title']}
👤 **Proposed by:** {proposal['author']}
✅ **Final Votes:** {proposal['upvotes']} 👍 / {proposal['downvotes']} 👎
🚀 **Status:** StillMe is now learning this content!

Thank you to all community members who participated in the voting! 🎯
            """.strip()
            
            alerting.send_alert(
                "🎉 Community Proposal Approved",
                message,
                "success"
            )
            
            logger.info(f"📢 Community notified about approved proposal: {proposal['title']}")
            
        except Exception as e:
            logger.error(f"❌ Error notifying community: {e}")
    
    def _notify_community_expired(self, proposal: Dict[str, Any]) -> None:
        """Thông báo cộng đồng khi proposal hết hạn"""
        try:
            from stillme_core.alerting.alerting_system import AlertingSystem
            
            alerting = AlertingSystem()
            
            message = f"""
⏰ **PROPOSAL VOTING EXPIRED**

📚 **Lesson:** {proposal['title']}
👤 **Proposed by:** {proposal['author']}
📊 **Final Votes:** {proposal['upvotes']} 👍 / {proposal['downvotes']} 👎
❌ **Status:** Did not reach approval threshold

Thank you for participating! Feel free to submit new proposals! 🎯
            """.strip()
            
            alerting.send_alert(
                "⏰ Proposal Voting Expired",
                message,
                "info"
            )
            
            logger.info(f"📢 Community notified about expired proposal: {proposal['title']}")
            
        except Exception as e:
            logger.error(f"❌ Error notifying community about expiration: {e}")
    
    def _notify_admin_approved(self, proposal: Dict[str, Any]) -> None:
        """Thông báo admin khi proposal được auto-approve"""
        try:
            from stillme_core.alerting.alerting_system import AlertingSystem
            
            alerting = AlertingSystem()
            
            message = f"""
🤖 **COMMUNITY PROPOSAL AUTO-APPROVED**

📖 **Lesson:** {proposal['title']}
👥 **From:** {proposal['author']}
📊 **Votes:** {proposal['upvotes']} 👍 / {proposal['downvotes']} 👎
⏰ **Approved:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
🔗 **GitHub:** {proposal.get('github_issue_url', 'N/A')}

StillMe will automatically learn this lesson. No action required! 🎯
            """.strip()
            
            alerting.send_alert(
                "🤖 Community Auto-Approval",
                message,
                "success"
            )
            
            logger.info(f"📢 Admin notified about auto-approved proposal: {proposal['title']}")
            
        except Exception as e:
            logger.error(f"❌ Error notifying admin: {e}")
    
    def _update_github_voting_status(self, proposal: Dict[str, Any]) -> None:
        """Update GitHub issue voting status"""
        try:
            if proposal.get('github_issue_url'):
                issue_number = self.github_integration._extract_issue_number(proposal['github_issue_url'])
                if issue_number:
                    self.github_integration.update_voting_status(
                        issue_number=issue_number,
                        upvotes=proposal['upvotes'],
                        downvotes=proposal['downvotes'],
                        status=proposal['status']
                    )
                    
        except Exception as e:
            logger.error(f"❌ Error updating GitHub voting status: {e}")
    
    def _update_github_approval(self, proposal: Dict[str, Any]) -> None:
        """Update GitHub issue when proposal is approved"""
        try:
            if proposal.get('github_issue_url'):
                issue_number = self.github_integration._extract_issue_number(proposal['github_issue_url'])
                if issue_number:
                    self.github_integration.add_approval_comment(
                        issue_number=issue_number,
                        proposal_title=proposal['title'],
                        total_votes=proposal['upvotes']
                    )
                    
        except Exception as e:
            logger.error(f"❌ Error updating GitHub approval: {e}")
    
    def _update_github_expired(self, proposal: Dict[str, Any]) -> None:
        """Update GitHub issue when proposal expires"""
        try:
            if proposal.get('github_issue_url'):
                issue_number = self.github_integration._extract_issue_number(proposal['github_issue_url'])
                if issue_number:
                    # Add expiration comment
                    comment_body = f"""
## ⏰ Voting Period Expired

**Proposal:** {proposal['title']}
**Final Votes:** {proposal['upvotes']} 👍 / {proposal['downvotes']} 👎
**Status:** Did not reach approval threshold

Thank you for participating in the community voting process! 🎯

Feel free to submit new proposals or improve this one for future voting.
                    """.strip()
                    
                    # This would need to be implemented in GitHub integration
                    logger.info(f"📝 Would add expiration comment to issue {issue_number}")
                    
        except Exception as e:
            logger.error(f"❌ Error updating GitHub expiration: {e}")
    
    def run_continuous_voting(self) -> None:
        """Chạy voting engine liên tục"""
        logger.info("🔄 Starting continuous voting engine...")
        
        while True:
            try:
                # Process daily voting
                results = self.process_daily_voting()
                
                # Log results
                logger.info(f"📊 Voting cycle completed: {results}")
                
                # Wait for next check
                logger.info(f"⏳ Waiting {self.check_interval} seconds for next check...")
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("🛑 Voting engine stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Error in continuous voting: {e}")
                logger.info("⏳ Waiting 5 minutes before retry...")
                time.sleep(300)  # Wait 5 minutes on error
    
    def get_voting_statistics(self) -> Dict[str, Any]:
        """Get voting statistics"""
        try:
            # Get dashboard statistics
            stats = self.proposal_manager.get_dashboard_statistics()
            
            # Add voting-specific stats
            stats.update({
                'min_votes_required': self.min_votes,
                'vote_ratio_threshold': self.vote_ratio_threshold,
                'auto_approve_enabled': self.auto_approve,
                'check_interval_minutes': self.check_interval // 60
            })
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error getting voting statistics: {e}")
            return {}


def main():
    """Test Voting Engine"""
    print("🗳️ Testing StillMe Voting Engine...")
    
    # Initialize voting engine
    engine = VotingEngine()
    
    # Test daily voting processing
    results = engine.process_daily_voting()
    print(f"📊 Voting results: {results}")
    
    # Test statistics
    stats = engine.get_voting_statistics()
    print(f"📈 Voting statistics: {stats}")
    
    print("🎉 Voting Engine test completed!")


if __name__ == "__main__":
    main()
