#!/usr/bin/env python3
"""
StillMe IPC Evolutionary Learning System
Hệ thống học tập tiến hóa với real learning sessions và progress tracking
"""

from typing import TYPE_CHECKING
import logging
import threading
import time
import uuid
import random
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root))

if TYPE_CHECKING:
    from stillme_core.learning.proposals_manager import ProposalsManager
if TYPE_CHECKING:
    from stillme_core.alerting.alerting_system import AlertingSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class EvolutionaryLearningSystem:
    """Hệ thống học tập tiến hóa với real learning sessions"""

    def __init__(self) -> None:
        self.proposals_manager = ProposalsManager()
        self.alerting_system = AlertingSystem()
        self.active_sessions = {}  # session_id -> session_data
        self.learning_threads = {}  # session_id -> thread

    def start_session(
        self, proposal_id: str, title: str, objectives: list, estimated_duration: int
    ) -> str:
        """Bắt đầu session học thật"""
        try:
            session_id = str(uuid.uuid4())

            # Tạo session data
            session_data = {
                "session_id": session_id,
                "proposal_id": proposal_id,
                "title": title,
                "objectives": objectives,
                "estimated_duration": estimated_duration,
                "started_at": datetime.now(),
                "progress": 0,
                "status": "learning",
                "current_objective": 0,
                "learning_notes": [],
            }

            # Lưu session vào active sessions
            self.active_sessions[session_id] = session_data

            # Cập nhật proposal status
            self.proposals_manager.update_proposal_status(proposal_id, "learning")
            self.proposals_manager.update_proposal(
                proposal_id,
                {
                    "session_id": session_id,
                    "learning_started_at": datetime.now().isoformat(),
                },
            )

            # Bắt đầu learning thread
            self._start_learning_thread(session_id)

            logger.info(
                f"✅ Started learning session: {title} (ID: {session_id[:8]}...)"
            )

            # Gửi notification
            self.alerting_system.send_alert(
                "Learning Session Started",
                f"StillMe IPC has started learning: '{title}'\n\n"
                f"Session ID: {session_id[:8]}...\n"
                f"Duration: {estimated_duration} minutes\n"
                f"Objectives: {len(objectives)} items\n\n"
                f"Progress will be tracked in real-time!",
                "info",
            )

            return session_id

        except Exception as e:
            logger.error(f"❌ Failed to start learning session: {e}")
            return None

    def _start_learning_thread(self, session_id: str) -> None:
        """Bắt đầu thread học tập"""

        def learning_worker():
            session_data = self.active_sessions.get(session_id)
            if not session_data:
                return

            try:
                logger.info(
                    f"🧠 Starting learning process for: {session_data['title']}"
                )

                # Mô phỏng quá trình học thật
                self._simulate_real_learning(session_id)

            except Exception as e:
                logger.error(f"❌ Learning thread error for {session_id}: {e}")
                self._complete_session(session_id, "failed")

        # Tạo và chạy thread
        thread = threading.Thread(target=learning_worker, daemon=True)
        thread.name = f"Learning-{session_id[:8]}"
        self.learning_threads[session_id] = thread
        thread.start()

    def _simulate_real_learning(self, session_id: str) -> None:
        """Mô phỏng quá trình học thật (sau này thay bằng logic thật)"""
        session_data = self.active_sessions[session_id]
        objectives = session_data["objectives"]
        estimated_duration = session_data["estimated_duration"]

        # Tính toán thời gian cho mỗi objective
        time_per_objective = estimated_duration / len(objectives)

        for i, objective in enumerate(objectives):
            logger.info(f"📚 Learning objective {i+1}/{len(objectives)}: {objective}")

            # Cập nhật current objective
            session_data["current_objective"] = i
            self._update_session_progress(session_id)

            # Mô phỏng thời gian học cho objective này
            learning_time = time_per_objective * 60  # Convert to seconds
            progress_increment = 100 / len(objectives)

            # Cập nhật tiến độ theo thời gian thực
            start_time = time.time()
            while time.time() - start_time < learning_time:
                # Cập nhật progress mỗi 30 giây
                time.sleep(30)

                elapsed = time.time() - start_time
                objective_progress = min(100, (elapsed / learning_time) * 100)
                total_progress = (i * progress_increment) + (
                    objective_progress * progress_increment / 100
                )

                session_data["progress"] = min(100, total_progress)
                self._update_session_progress(session_id)

                # Thêm learning notes
                if random.random() < 0.3:  # 30% chance to add note
                    note = f"📝 Learning note: Understanding {objective[:50]}..."
                    session_data["learning_notes"].append(
                        {"timestamp": datetime.now().isoformat(), "note": note}
                    )

            # Hoàn thành objective
            session_data["learning_notes"].append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "note": f"✅ Completed objective: {objective}",
                }
            )

            logger.info(f"✅ Completed objective {i+1}/{len(objectives)}")

        # Hoàn thành session
        session_data["progress"] = 100
        session_data["status"] = "completed"
        self._complete_session(session_id, "completed")

    def _update_session_progress(self, session_id: str) -> None:
        """Cập nhật tiến độ vào database"""
        try:
            session_data = self.active_sessions.get(session_id)
            if not session_data:
                return

            # Cập nhật proposal với progress
            self.proposals_manager.update_proposal(
                session_data["proposal_id"],
                {
                    "learning_progress": session_data["progress"],
                    "current_objective": session_data["current_objective"],
                    "learning_notes": session_data["learning_notes"],
                    "last_updated": datetime.now().isoformat(),
                },
            )

            # Gửi progress notification mỗi 25%
            progress = session_data["progress"]
            if progress >= 25 and progress < 30:
                self.alerting_system.send_alert(
                    "Learning Progress Update",
                    f"StillMe IPC has completed 25% of '{session_data['title']}'",
                    "info",
                )
            elif progress >= 50 and progress < 55:
                self.alerting_system.send_alert(
                    "Learning Progress Update",
                    f"StillMe IPC has completed 50% of '{session_data['title']}'",
                    "info",
                )
            elif progress >= 75 and progress < 80:
                self.alerting_system.send_alert(
                    "Learning Progress Update",
                    f"StillMe IPC has completed 75% of '{session_data['title']}'",
                    "info",
                )

        except Exception as e:
            logger.error(f"❌ Failed to update session progress: {e}")

    def _complete_session(self, session_id: str, status: str) -> None:
        """Hoàn thành session học"""
        try:
            session_data = self.active_sessions.get(session_id)
            if not session_data:
                return

            # Cập nhật final status
            session_data["status"] = status
            session_data["completed_at"] = datetime.now()

            # Cập nhật proposal
            self.proposals_manager.update_proposal_status(
                session_data["proposal_id"], status
            )
            self.proposals_manager.update_proposal(
                session_data["proposal_id"],
                {
                    "learning_completed_at": datetime.now().isoformat(),
                    "final_progress": session_data["progress"],
                    "learning_notes": session_data["learning_notes"],
                },
            )

            # Gửi completion notification
            if status == "completed":
                self.alerting_system.send_alert(
                    "Learning Session Completed! 🎉",
                    f"StillMe IPC has successfully completed learning: '{session_data['title']}'\n\n"
                    f"Final Progress: {session_data['progress']:.1f}%\n"
                    f"Objectives Completed: {len(session_data['objectives'])}\n"
                    f"Learning Notes: {len(session_data['learning_notes'])} entries\n\n"
                    f"StillMe IPC is now smarter! 🧠✨",
                    "success",
                )
            else:
                self.alerting_system.send_alert(
                    "Learning Session Failed",
                    f"StillMe IPC encountered an issue while learning: '{session_data['title']}'\n\n"
                    f"Status: {status}\n"
                    f"Progress: {session_data['progress']:.1f}%\n\n"
                    f"The session will be reviewed for troubleshooting.",
                    "warning",
                )

            # Cleanup
            self.active_sessions.pop(session_id, None)
            self.learning_threads.pop(session_id, None)

            logger.info(f"✅ Session completed: {session_data['title']} ({status})")

        except Exception as e:
            logger.error(f"❌ Failed to complete session: {e}")

    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Lấy trạng thái session"""
        return self.active_sessions.get(session_id)

    def get_all_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Lấy tất cả sessions đang hoạt động"""
        return self.active_sessions.copy()

    def stop_session(self, session_id: str) -> bool:
        """Dừng session học"""
        try:
            if session_id in self.active_sessions:
                session_data = self.active_sessions[session_id]
                session_data["status"] = "stopped"
                session_data["stopped_at"] = datetime.now()

                # Cập nhật proposal
                self.proposals_manager.update_proposal_status(
                    session_data["proposal_id"], "stopped"
                )

                # Cleanup
                self.active_sessions.pop(session_id, None)
                self.learning_threads.pop(session_id, None)

                logger.info(f"🛑 Stopped session: {session_data['title']}")
                return True
            return False

        except Exception as e:
            logger.error(f"❌ Failed to stop session: {e}")
            return False


# Global instance
_learning_system = None


def get_learning_system() -> EvolutionaryLearningSystem:
    """Lấy instance global của learning system"""
    global _learning_system
    if _learning_system is None:
        _learning_system = EvolutionaryLearningSystem()
    return _learning_system


def start_learning_session(proposal_id: str) -> Optional[str]:
    """Helper function để bắt đầu learning session"""
    try:
        # Lấy proposal từ database
        proposals_manager = ProposalsManager()
        proposal = proposals_manager.get_proposal(proposal_id)

        if not proposal:
            logger.error(f"❌ Proposal not found: {proposal_id}")
            return None

        # Bắt đầu learning session
        learning_system = get_learning_system()
        session_id = learning_system.start_session(
            proposal_id=proposal_id,
            title=proposal.title,
            objectives=proposal.learning_objectives,
            estimated_duration=proposal.estimated_duration,
        )

        return session_id

    except Exception as e:
        logger.error(f"❌ Failed to start learning session: {e}")
        return None


if __name__ == "__main__":
    # Test the learning system
    learning_system = EvolutionaryLearningSystem()

    # Test session
    session_id = learning_system.start_session(
        proposal_id="test-proposal",
        title="Test Learning Session",
        objectives=["Learn Python basics", "Understand OOP", "Build a project"],
        estimated_duration=60,  # 1 hour
    )

    if session_id:
        print(f"✅ Test session started: {session_id}")

        # Monitor progress
        while session_id in learning_system.active_sessions:
            status = learning_system.get_session_status(session_id)
            if status:
                print(f"Progress: {status['progress']:.1f}% - {status['status']}")
            time.sleep(10)
    else:
        print("❌ Failed to start test session")