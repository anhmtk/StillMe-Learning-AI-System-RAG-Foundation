#!/usr/bin/env python3
"""
🤖 AUTO-APPROVAL ENGINE
Tự động approve và bắt đầu học tập cho StillMe IPC
"""

import logging
from typing import List, Dict, Any

from stillme_core.learning.proposals_manager import ProposalsManager
from stillme_core.learning.silent_learning_system import (
    SilentEvolutionaryLearningSystem,
)

logger = logging.getLogger(__name__)


class AutoApprovalEngine:
    def __init__(self):
        self.proposals_manager = ProposalsManager()
        self.learning_system = SilentEvolutionaryLearningSystem()

        # Auto-approval criteria
        self.quality_threshold = 0.75
        self.max_duration = 180  # phút
        self.min_objectives = 1
        self.max_concurrent_sessions = 5

        logger.info("🤖 Auto-Approval Engine initialized")
        logger.info(f"📊 Quality threshold: {self.quality_threshold}")
        logger.info(f"⏱️ Max duration: {self.max_duration} phút")
        logger.info(f"🔄 Max concurrent sessions: {self.max_concurrent_sessions}")

    def process_pending_proposals(self) -> int:
        """Tự động xử lý và approve proposals đạt chuẩn"""
        try:
            # Lấy pending proposals
            pending_proposals = self._get_pending_proposals()
            logger.info(f"📋 Tìm thấy {len(pending_proposals)} pending proposals")

            approved_count = 0

            for proposal in pending_proposals:
                if self._meets_auto_approval_criteria(proposal):
                    if self._can_start_new_session():
                        success = self._auto_approve_and_start(proposal)
                        if success:
                            approved_count += 1
                            logger.info(f"✅ Auto-approved: {proposal.title}")
                        else:
                            logger.warning(
                                f"⚠️ Failed to start learning for: {proposal.title}"
                            )
                    else:
                        logger.info(
                            f"⏳ Queue proposal (max sessions reached): {proposal.title}"
                        )
                else:
                    logger.debug(f"❌ Proposal không đạt tiêu chuẩn: {proposal.title}")

            if approved_count > 0:
                logger.info(f"🎯 Đã auto-approve {approved_count} proposals")
            else:
                logger.info("ℹ️ Không có proposal nào đạt tiêu chuẩn auto-approval")

            return approved_count

        except Exception as e:
            logger.error(f"❌ Lỗi trong process_pending_proposals: {e}")
            return 0

    def _get_pending_proposals(self) -> List[Dict[str, Any]]:
        """Lấy danh sách pending proposals"""
        try:
            # Get all pending proposals from database
            proposals = self.proposals_manager.get_all_proposals()
            pending = [p for p in proposals if p.get("status") == "pending"]
            return pending
        except Exception as e:
            logger.error(f"❌ Lỗi lấy pending proposals: {e}")
            return []

    def _meets_auto_approval_criteria(self, proposal: Dict[str, Any]) -> bool:
        """Kiểm tra proposal có đủ điều kiện tự động approve không"""
        try:
            # Check quality score
            quality_score = proposal.get("quality_score", 0)
            if quality_score < self.quality_threshold:
                logger.debug(
                    f"❌ Quality score too low: {quality_score} < {self.quality_threshold}"
                )
                return False

            # Check duration
            estimated_duration = proposal.get("estimated_duration", 0)
            if estimated_duration > self.max_duration:
                logger.debug(
                    f"❌ Duration too long: {estimated_duration} > {self.max_duration}"
                )
                return False

            # Check learning objectives
            objectives = proposal.get("learning_objectives", [])
            if len(objectives) < self.min_objectives:
                logger.debug(
                    f"❌ Too few objectives: {len(objectives)} < {self.min_objectives}"
                )
                return False

            # Check for duplicates
            if self._is_duplicate(proposal):
                logger.debug(
                    f"❌ Duplicate proposal: {proposal.get('title', 'Unknown')}"
                )
                return False

            logger.debug(
                f"✅ Proposal meets criteria: {proposal.get('title', 'Unknown')}"
            )
            return True

        except Exception as e:
            logger.error(f"❌ Lỗi kiểm tra criteria: {e}")
            return False

    def _is_duplicate(self, proposal: Dict[str, Any]) -> bool:
        """Kiểm tra proposal có trùng lặp không"""
        try:
            title = proposal.get("title", "").lower()

            # Get all approved/learning proposals
            all_proposals = self.proposals_manager.get_all_proposals()
            active_proposals = [
                p
                for p in all_proposals
                if p.get("status") in ["approved", "learning", "completed"]
            ]

            # Check for similar titles
            for existing in active_proposals:
                existing_title = existing.get("title", "").lower()
                if title in existing_title or existing_title in title:
                    return True

            return False

        except Exception as e:
            logger.error(f"❌ Lỗi kiểm tra duplicate: {e}")
            return True  # Assume duplicate if error

    def _can_start_new_session(self) -> bool:
        """Kiểm tra có thể bắt đầu session mới không"""
        try:
            # Count active learning sessions
            all_proposals = self.proposals_manager.get_all_proposals()
            active_sessions = [
                p for p in all_proposals if p.get("status") == "learning"
            ]

            return len(active_sessions) < self.max_concurrent_sessions

        except Exception as e:
            logger.error(f"❌ Lỗi kiểm tra concurrent sessions: {e}")
            return False

    def _auto_approve_and_start(self, proposal: Dict[str, Any]) -> bool:
        """Tự động approve và bắt đầu học"""
        try:
            proposal_id = proposal.get("id")
            if not proposal_id:
                logger.error("❌ Proposal ID không tồn tại")
                return False

            # Approve proposal
            success = self.proposals_manager.approve_proposal(
                proposal_id, "auto_approval_system"
            )
            if not success:
                logger.error(f"❌ Không thể approve proposal: {proposal_id}")
                return False

            # Start silent learning
            session_id = self.learning_system.start_silent_learning(proposal_id)
            if not session_id:
                logger.error(f"❌ Không thể bắt đầu learning session: {proposal_id}")
                return False

            logger.info(
                f"🎯 Đã bắt đầu silent learning: {proposal.get('title', 'Unknown')}"
            )
            return True

        except Exception as e:
            logger.error(f"❌ Lỗi trong auto_approve_and_start: {e}")
            return False

    def run_approval_cycle(self) -> int:
        """Chạy một chu kỳ auto-approval"""
        logger.info("🔄 Bắt đầu auto-approval cycle...")
        approved_count = self.process_pending_proposals()
        logger.info(
            f"✅ Hoàn thành auto-approval cycle: {approved_count} proposals approved"
        )
        return approved_count


def main():
    """Test function"""
    engine = AutoApprovalEngine()
    approved_count = engine.run_approval_cycle()
    print(f"🎯 Auto-approved {approved_count} proposals")


if __name__ == "__main__":
    main()
