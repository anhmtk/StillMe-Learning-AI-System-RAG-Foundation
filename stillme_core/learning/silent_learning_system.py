#!/usr/bin/env python3
"""
🔇 SILENT LEARNING SYSTEM
Học tập im lặng - chỉ thông báo khi hoàn thành 100%
"""

import logging
import threading
import time
import uuid
import random
from datetime import datetime
from typing import Any, Dict, List

from stillme_core.learning.proposals_manager import ProposalsManager
from stillme_core.alerting.completion_alerts import CompletionAlertService

logger = logging.getLogger(__name__)

class SilentEvolutionaryLearningSystem:
    def __init__(self):
        self.proposals_manager = ProposalsManager()
        self.completion_alerts = CompletionAlertService()
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        logger.info("🔇 SilentEvolutionaryLearningSystem initialized")
        logger.info("📝 Chế độ: Silent learning - chỉ thông báo khi hoàn thành")
    
    def start_silent_learning(self, proposal_id: str) -> str:
        """Khởi động học tập im lặng - chỉ thông báo khi hoàn thành"""
        try:
            # Get proposal details
            proposal = self.proposals_manager.get_proposal(proposal_id)
            if not proposal:
                logger.error(f"❌ Proposal {proposal_id} không tồn tại")
                return ""
            
            # Create session
            session_id = str(uuid.uuid4())
            started_at = datetime.now().isoformat()
            
            session_data = {
                "proposal_id": proposal_id,
                "title": proposal.title,
                "objectives": proposal.learning_objectives,
                "estimated_duration": proposal.estimated_duration,
                "progress": 0.0,
                "status": "silent_learning",
                "current_objective_index": 0,
                "learning_notes": [],
                "started_at": started_at,
                "last_updated": started_at,
                "thread": None,
                "silent_mode": True  # Flag for silent mode
            }
            self.active_sessions[session_id] = session_data
            
            # Update proposal in database
            self.proposals_manager.update_proposal(
                proposal_id,
                {
                    'session_id': session_id,
                    'learning_started_at': started_at,
                    'status': 'learning',
                    'learning_progress': 0.0,
                    'current_objective': 0,
                    'learning_notes': []
                }
            )
            
            logger.info(f"🔇 Bắt đầu silent learning: {proposal.title}")
            logger.info(f"📊 Session ID: {session_id[:8]}...")
            logger.info(f"⏱️ Estimated duration: {proposal.estimated_duration} phút")
            
            # Start silent learning thread
            thread = threading.Thread(
                target=self._silent_learning_process,
                args=(session_id, proposal_id)
            )
            thread.daemon = True
            thread.start()
            session_data["thread"] = thread
            
            return session_id
            
        except Exception as e:
            logger.error(f"❌ Lỗi khởi động silent learning: {e}")
            return ""
    
    def _silent_learning_process(self, session_id: str, proposal_id: str):
        """Quá trình học im lặng - không spam notifications"""
        try:
            session_data = self.active_sessions.get(session_id)
            if not session_data:
                logger.error(f"❌ Session {session_id} không tồn tại")
                return
            
            objectives = session_data['objectives']
            total_objectives = len(objectives)
            progress_per_objective = 100 / total_objectives if total_objectives > 0 else 100
            
            logger.info(f"📚 Bắt đầu học {total_objectives} objectives...")
            
            # Learn each objective silently
            for i, objective in enumerate(objectives):
                session_data['current_objective_index'] = i
                self.proposals_manager.update_proposal(proposal_id, {'current_objective': i})
                
                logger.info(f"🎯 Learning objective {i+1}/{total_objectives}: {objective}")
                
                objective_start_progress = i * progress_per_objective
                objective_end_progress = (i + 1) * progress_per_objective
                
                # Simulate learning within this objective
                current_objective_progress = 0
                while current_objective_progress < 100:
                    time.sleep(random.uniform(0.5, 1.5))  # Simulate work
                    
                    # Random progress increment
                    progress_increment = random.uniform(1, 5)
                    current_objective_progress += progress_increment
                    if current_objective_progress > 100:
                        current_objective_progress = 100
                    
                    # Calculate overall progress
                    overall_progress = objective_start_progress + (current_objective_progress / 100) * progress_per_objective
                    if overall_progress > 100:
                        overall_progress = 100.0
                    
                    # Update session data
                    session_data['progress'] = overall_progress
                    session_data['last_updated'] = datetime.now().isoformat()
                    session_data['learning_notes'].append({
                        'timestamp': datetime.now().strftime("%H:%M:%S"),
                        'note': f"Silent progress on '{objective}': {current_objective_progress:.1f}%"
                    })
                    
                    # Update database (silent - no notifications)
                    self.proposals_manager.update_proposal(
                        proposal_id,
                        {
                            'learning_progress': overall_progress,
                            'last_updated': session_data['last_updated'],
                            'learning_notes': session_data['learning_notes']
                        }
                    )
                
                logger.info(f"✅ Completed objective {i+1}/{total_objectives}")
            
            # Mark session as completed
            session_data['progress'] = 100.0
            session_data['status'] = "completed"
            session_data['last_updated'] = datetime.now().isoformat()
            
            self.proposals_manager.update_proposal(
                proposal_id,
                {
                    'learning_progress': 100.0,
                    'status': 'completed',
                    'learning_completed_at': session_data['last_updated'],
                    'last_updated': session_data['last_updated'],
                    'final_progress': 100.0
                }
            )
            
            # CHỈ KHI HOÀN THÀNH 100% mới gửi thông báo
            logger.info(f"🎉 Hoàn thành silent learning: {session_data['title']}")
            self._send_completion_notification(proposal_id, session_data)
            
        except Exception as e:
            logger.error(f"❌ Lỗi trong silent learning process: {e}")
            self._send_error_notification(proposal_id, str(e))
    
    def _send_completion_notification(self, proposal_id: str, session_data: Dict[str, Any]):
        """Gửi thông báo hoàn thành"""
        try:
            proposal = self.proposals_manager.get_proposal(proposal_id)
            if proposal:
                self.completion_alerts.send_learning_completed_alert(proposal)
                logger.info(f"📢 Đã gửi completion notification: {proposal.title}")
            else:
                logger.warning(f"⚠️ Không thể lấy proposal để gửi notification: {proposal_id}")
        except Exception as e:
            logger.error(f"❌ Lỗi gửi completion notification: {e}")
    
    def _send_error_notification(self, proposal_id: str, error_message: str):
        """Gửi thông báo lỗi"""
        try:
            logger.error(f"🚨 Learning error for proposal {proposal_id}: {error_message}")
            # Could send error notification here if needed
        except Exception as e:
            logger.error(f"❌ Lỗi gửi error notification: {e}")
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Lấy trạng thái session"""
        return self.active_sessions.get(session_id, {})
    
    def get_active_sessions_count(self) -> int:
        """Đếm số session đang hoạt động"""
        return len([s for s in self.active_sessions.values() if s.get('status') == 'silent_learning'])

def main():
    """Test function"""
    system = SilentEvolutionaryLearningSystem()
    print("🔇 Silent Learning System initialized")
    print(f"📊 Active sessions: {system.get_active_sessions_count()}")

if __name__ == "__main__":
    main()
