"""
Notification Automation System
=============================

Hệ thống tự động gửi notification cho learning events:
- Khi có proposal mới
- Khi proposal được approve/reject
- Khi hoàn thành học
- Khi community proposal đạt threshold

Author: StillMe AI Framework
Version: 2.0.0
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from stillme_core.alerting.alert_manager import send_alert

logger = logging.getLogger(__name__)


class LearningNotificationAutomation:
    """Tự động gửi notification cho learning events"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.enabled = True
        
    async def notify_new_proposal(self, proposal_id: str, title: str, 
                                 source: str, priority: str) -> bool:
        """Thông báo proposal mới"""
        try:
            if not self.enabled:
                return True
                
            message = f"📚 New Learning Proposal: {title}\n"
            message += f"Source: {source}\n"
            message += f"Priority: {priority}\n"
            message += f"ID: {proposal_id}"
            
            result = await send_alert(
                alert_type='info',
                severity='medium',
                title='New Learning Proposal',
                message=message,
                component='learning_system',
                channels=['telegram', 'email', 'desktop']
            )
            
            self.logger.info(f"Sent new proposal notification for {proposal_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to send new proposal notification: {e}")
            return False
    
    async def notify_proposal_approved(self, proposal_id: str, title: str, 
                                      approved_by: str) -> bool:
        """Thông báo proposal được approve"""
        try:
            if not self.enabled:
                return True
                
            message = f"✅ Learning Proposal Approved: {title}\n"
            message += f"Approved by: {approved_by}\n"
            message += f"ID: {proposal_id}\n"
            message += f"Learning will start soon..."
            
            result = await send_alert(
                alert_type='success',
                severity='medium',
                title='Proposal Approved',
                message=message,
                component='learning_system',
                channels=['telegram', 'email', 'desktop']
            )
            
            self.logger.info(f"Sent approval notification for {proposal_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to send approval notification: {e}")
            return False
    
    async def notify_proposal_rejected(self, proposal_id: str, title: str, 
                                      rejected_by: str, reason: str = None) -> bool:
        """Thông báo proposal bị reject"""
        try:
            if not self.enabled:
                return True
                
            message = f"❌ Learning Proposal Rejected: {title}\n"
            message += f"Rejected by: {rejected_by}\n"
            if reason:
                message += f"Reason: {reason}\n"
            message += f"ID: {proposal_id}"
            
            result = await send_alert(
                level='warning',
                severity='medium',
                title='Proposal Rejected',
                message=message,
                source='learning_system',
                channels=['telegram', 'email', 'desktop']
            )
            
            self.logger.info(f"Sent rejection notification for {proposal_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to send rejection notification: {e}")
            return False
    
    async def notify_learning_started(self, proposal_id: str, title: str, 
                                     estimated_duration: int) -> bool:
        """Thông báo bắt đầu học"""
        try:
            if not self.enabled:
                return True
                
            message = f"🚀 Learning Started: {title}\n"
            message += f"Estimated duration: {estimated_duration} minutes\n"
            message += f"ID: {proposal_id}\n"
            message += f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            result = await send_alert(
                level='info',
                severity='medium',
                title='Learning Started',
                message=message,
                source='learning_system',
                channels=['telegram', 'email', 'desktop']
            )
            
            self.logger.info(f"Sent learning started notification for {proposal_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to send learning started notification: {e}")
            return False
    
    async def notify_learning_completed(self, proposal_id: str, title: str, 
                                       duration: int, progress: float) -> bool:
        """Thông báo hoàn thành học"""
        try:
            if not self.enabled:
                return True
                
            message = f"🎉 Learning Completed: {title}\n"
            message += f"Duration: {duration} minutes\n"
            message += f"Progress: {progress:.1%}\n"
            message += f"ID: {proposal_id}\n"
            message += f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            result = await send_alert(
                alert_type='success',
                severity='high',
                title='Learning Completed',
                message=message,
                component='learning_system',
                channels=['telegram', 'email', 'desktop']
            )
            
            self.logger.info(f"Sent learning completed notification for {proposal_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to send learning completed notification: {e}")
            return False
    
    async def notify_learning_failed(self, proposal_id: str, title: str, 
                                    error: str) -> bool:
        """Thông báo học thất bại"""
        try:
            if not self.enabled:
                return True
                
            message = f"💥 Learning Failed: {title}\n"
            message += f"Error: {error}\n"
            message += f"ID: {proposal_id}\n"
            message += f"Failed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            result = await send_alert(
                level='error',
                severity='high',
                title='Learning Failed',
                message=message,
                source='learning_system',
                channels=['telegram', 'email', 'desktop']
            )
            
            self.logger.info(f"Sent learning failed notification for {proposal_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to send learning failed notification: {e}")
            return False
    
    async def notify_community_proposal_approved(self, proposal_id: str, title: str, 
                                                votes: int, threshold: int) -> bool:
        """Thông báo community proposal được auto-approve"""
        try:
            if not self.enabled:
                return True
                
            message = f"🗳️ Community Proposal Auto-Approved: {title}\n"
            message += f"Votes: {votes}/{threshold}\n"
            message += f"ID: {proposal_id}\n"
            message += f"StillMe will start learning this topic automatically!"
            
            result = await send_alert(
                level='success',
                severity='high',
                title='Community Proposal Approved',
                message=message,
                source='community_voting',
                channels=['telegram', 'email', 'desktop']
            )
            
            self.logger.info(f"Sent community approval notification for {proposal_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to send community approval notification: {e}")
            return False
    
    async def notify_learning_progress(self, proposal_id: str, title: str, 
                                      progress: float, current_objective: str) -> bool:
        """Thông báo tiến độ học (cho community dashboard)"""
        try:
            if not self.enabled:
                return True
                
            message = f"📊 Learning Progress: {title}\n"
            message += f"Progress: {progress:.1%}\n"
            message += f"Current objective: {current_objective}\n"
            message += f"ID: {proposal_id}"
            
            result = await send_alert(
                level='info',
                severity='low',
                title='Learning Progress Update',
                message=message,
                source='learning_system',
                channels=['telegram']  # Only Telegram for progress updates
            )
            
            self.logger.info(f"Sent progress notification for {proposal_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to send progress notification: {e}")
            return False
    
    async def notify_daily_summary(self, stats: Dict[str, Any]) -> bool:
        """Thông báo tóm tắt hàng ngày"""
        try:
            if not self.enabled:
                return True
                
            message = f"📈 Daily Learning Summary\n"
            message += f"New proposals: {stats.get('new_proposals', 0)}\n"
            message += f"Approved: {stats.get('approved', 0)}\n"
            message += f"Completed: {stats.get('completed', 0)}\n"
            message += f"Failed: {stats.get('failed', 0)}\n"
            message += f"Active sessions: {stats.get('active_sessions', 0)}"
            
            result = await send_alert(
                level='info',
                severity='medium',
                title='Daily Learning Summary',
                message=message,
                source='learning_system',
                channels=['telegram', 'email']
            )
            
            self.logger.info("Sent daily summary notification")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to send daily summary notification: {e}")
            return False
    
    def enable(self):
        """Bật notification automation"""
        self.enabled = True
        self.logger.info("Learning notification automation enabled")
    
    def disable(self):
        """Tắt notification automation"""
        self.enabled = False
        self.logger.info("Learning notification automation disabled")


# Global instance
_learning_notification_automation = None


def get_learning_notification_automation() -> LearningNotificationAutomation:
    """Get global learning notification automation instance"""
    global _learning_notification_automation
    if _learning_notification_automation is None:
        _learning_notification_automation = LearningNotificationAutomation()
    return _learning_notification_automation
