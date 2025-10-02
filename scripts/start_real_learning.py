#!/usr/bin/env python3
"""
StillMe IPC Real Learning System
Kích hoạt hệ thống học tập thực sự với automation và alerting
"""

import logging
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from stillme_core.alerting.alerting_system import AlertingSystem
from stillme_core.learning.automation_service import AutomationService
from stillme_core.learning.proposals_manager import ProposalsManager
from stillme_core.learning.scheduler import StillMeScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class RealLearningSystem:
    def __init__(self):
        self.scheduler = StillMeScheduler()
        self.proposals_manager = ProposalsManager()
        self.alerting_system = AlertingSystem()
        self.automation_service = AutomationService(
            self.scheduler, self.proposals_manager, self.alerting_system
        )

    def start(self):
        """Khởi động hệ thống học tập thực sự"""
        logger.info("🧠 StillMe IPC Real Learning System")
        logger.info("==========================================")
        logger.info("🚀 Starting Real Learning System...")

        try:
            # 1. Start Learning Scheduler
            logger.info("📅 Starting Learning Scheduler...")
            self.scheduler.start()
            logger.info("✅ Scheduler started successfully.")

            # 2. Start Automation Service
            logger.info("🤖 Starting Automation Service...")
            self.automation_service.start()
            logger.info("✅ Automation Service started successfully.")

            # 3. Test Alerting System
            logger.info("🔔 Testing Alerting System...")
            self.alerting_system.send_alert(
                "Real Learning System Activated",
                "StillMe IPC is now ready to learn new knowledge automatically! 🧠✨",
                "info",
            )
            logger.info("✅ Alerting system tested successfully.")

            # 4. Create initial learning proposal
            logger.info("📝 Creating initial learning proposal...")
            self._create_initial_proposal()

            logger.info("🎉 StillMe IPC Real Learning System is now ACTIVE!")
            logger.info("💡 The system will:")
            logger.info("   • Automatically discover new knowledge")
            logger.info("   • Generate learning proposals")
            logger.info("   • Send notifications via Email/Telegram")
            logger.info("   • Wait for your approval before learning")
            logger.info("   • Track learning progress in real-time")

            return True

        except Exception as e:
            logger.error(f"❌ Failed to start Real Learning System: {e}")
            self.shutdown()
            return False

    def _create_initial_proposal(self):
        """Tạo proposal học tập ban đầu"""
        try:
            proposal = self.proposals_manager.create_proposal(
                title="Advanced Python Programming",
                description="Learn advanced Python concepts including decorators, generators, async/await, and metaprogramming",
                learning_objectives=[
                    "Master Python decorators and their applications",
                    "Understand generators and memory efficiency",
                    "Learn async/await programming patterns",
                    "Explore metaprogramming techniques",
                ],
                prerequisites=["Python basics", "Object-oriented programming"],
                expected_outcomes=[
                    "Advanced Python proficiency",
                    "Ability to write efficient, scalable code",
                    "Understanding of modern Python patterns",
                ],
                estimated_duration=300,
                quality_score=0.95,
                source="ai_generated",
                priority="high",
                risk_assessment={
                    "complexity": "high",
                    "time_commitment": "high",
                    "prerequisites": "medium",
                    "practical_value": "very_high",
                },
                created_by="real_learning_system",
            )

            logger.info(f"✅ Initial proposal created: {proposal.title}")

            # Send notification
            self.alerting_system.send_alert(
                "New Learning Proposal Generated",
                f"StillMe IPC has generated a new learning proposal: '{proposal.title}'\n\n"
                f"Quality Score: {proposal.quality_score}\n"
                f"Duration: {proposal.estimated_duration} minutes\n"
                f"Priority: {proposal.priority}\n\n"
                f"Please review and approve in the dashboard!",
                "info",
            )

        except Exception as e:
            logger.error(f"❌ Failed to create initial proposal: {e}")

    def shutdown(self):
        """Tắt hệ thống"""
        logger.info("🛑 Shutting down Real Learning System...")
        try:
            self.scheduler.shutdown()
            self.automation_service.shutdown()
            logger.info("✅ Real Learning System shut down successfully.")
        except Exception as e:
            logger.error(f"❌ Error during shutdown: {e}")


def main():
    """Main function"""
    learning_system = RealLearningSystem()

    try:
        if learning_system.start():
            logger.info("💡 Real Learning System is running in the background.")
            logger.info("   Keep this terminal open to maintain the system.")
            logger.info("   Press Ctrl+C to stop the system.")

            # Keep the system running
            while True:
                time.sleep(1)
        else:
            logger.error("❌ Failed to start Real Learning System.")
            sys.exit(1)

    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Received shutdown signal...")
        learning_system.shutdown()
        logger.info("👋 Real Learning System stopped. Goodbye!")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        learning_system.shutdown()
        sys.exit(1)


if __name__ == "__main__":
    main()
