"""
StillMe Learning Approval Queue Manager
Quản lý hàng đợi phê duyệt và workflow
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .approval_system import (
    ApprovalSystem, ApprovalRequest, ApprovalStatus, 
    ContentType, ApprovalPriority, ApprovalConfig
)

logger = logging.getLogger(__name__)

@dataclass
class QueueStats:
    """Thống kê hàng đợi"""
    total_pending: int
    high_priority: int
    expired_soon: int  # Hết hạn trong 1h
    auto_approved_today: int
    human_approved_today: int
    rejection_rate: float

class ApprovalQueueManager:
    """Quản lý hàng đợi phê duyệt"""
    
    def __init__(self, approval_system: ApprovalSystem):
        self.approval_system = approval_system
        self.notification_callbacks = []
        
    async def add_notification_callback(self, callback):
        """Thêm callback thông báo"""
        self.notification_callbacks.append(callback)
    
    async def _notify(self, message: str, data: Dict[str, Any] = None):
        """Gửi thông báo đến tất cả callbacks"""
        for callback in self.notification_callbacks:
            try:
                await callback(message, data or {})
            except Exception as e:
                logger.error(f"Notification callback failed: {e}")
    
    async def submit_learning_content(
        self,
        content_type: ContentType,
        title: str,
        description: str,
        content_preview: str,
        quality_score: float,
        risk_score: float,
        source_url: Optional[str] = None,
        priority: ApprovalPriority = ApprovalPriority.MEDIUM,
        metadata: Dict[str, Any] = None
    ) -> Optional[str]:
        """Gửi nội dung học tập để phê duyệt"""
        
        # Kiểm tra có cần phê duyệt không
        if not self._requires_approval(content_type, quality_score, risk_score):
            logger.info(f"Content auto-approved: {title[:50]}...")
            await self._notify("content_auto_approved", {
                "title": title,
                "content_type": content_type.value,
                "quality_score": quality_score
            })
            return await self._create_auto_approved_request(
                content_type, title, quality_score, risk_score
            )
        
        # Gửi để phê duyệt
        request_id = await self.approval_system.submit_for_approval(
            content_type=content_type,
            title=title,
            description=description,
            content_preview=content_preview,
            quality_score=quality_score,
            risk_score=risk_score,
            source_url=source_url,
            priority=priority,
            metadata=metadata
        )
        
        if request_id:
            await self._notify("content_pending_approval", {
                "request_id": request_id,
                "title": title,
                "content_type": content_type.value,
                "priority": priority.value
            })
        
        return request_id
    
    def _requires_approval(self, content_type: ContentType, quality_score: float, risk_score: float) -> bool:
        """Kiểm tra có cần phê duyệt thủ công không"""
        config = self.approval_system.config
        
        # Nếu system disabled, không cần phê duyệt
        if not config.enabled:
            return False
        
        # Nếu loại nội dung cần phê duyệt thủ công
        if content_type in config.require_human_approval:
            return True
        
        # Nếu quality thấp hoặc risk cao
        if (quality_score < config.auto_approve_threshold or 
            risk_score > (1.0 - config.auto_approve_threshold)):
            return True
        
        return False
    
    async def _create_auto_approved_request(
        self, 
        content_type: ContentType, 
        title: str, 
        quality_score: float, 
        risk_score: float
    ) -> str:
        """Tạo request tự động phê duyệt"""
        return await self.approval_system._auto_approve(
            content_type, title, quality_score, risk_score
        )
    
    async def get_pending_queue(self, limit: int = 20) -> List[ApprovalRequest]:
        """Lấy hàng đợi chờ phê duyệt"""
        return await self.approval_system.get_pending_requests(limit)
    
    async def get_queue_stats(self) -> QueueStats:
        """Lấy thống kê hàng đợi"""
        stats = await self.approval_system.get_approval_stats()
        
        # Lấy thêm thống kê chi tiết
        pending_requests = await self.get_pending_queue(100)
        
        high_priority = sum(1 for req in pending_requests 
                           if req.priority in [ApprovalPriority.HIGH, ApprovalPriority.CRITICAL])
        
        expired_soon = sum(1 for req in pending_requests 
                          if req.expires_at < datetime.now() + timedelta(hours=1))
        
        # Thống kê hôm nay
        today = datetime.now().date()
        auto_approved_today = 0
        human_approved_today = 0
        
        # TODO: Implement daily stats query
        # This would require additional database queries
        
        return QueueStats(
            total_pending=stats["pending_count"],
            high_priority=high_priority,
            expired_soon=expired_soon,
            auto_approved_today=auto_approved_today,
            human_approved_today=human_approved_today,
            rejection_rate=1.0 - stats["approval_rate"]
        )
    
    async def process_approval_batch(self, approvals: List[Dict[str, Any]]) -> Dict[str, int]:
        """Xử lý hàng loạt phê duyệt"""
        results = {"approved": 0, "rejected": 0, "failed": 0}
        
        for approval in approvals:
            try:
                request_id = approval["request_id"]
                action = approval["action"]  # "approve" or "reject"
                approver = approval.get("approver", "system")
                notes = approval.get("notes", "")
                
                if action == "approve":
                    success = await self.approval_system.approve_request(request_id, approver, notes)
                    if success:
                        results["approved"] += 1
                        await self._notify("content_approved", {
                            "request_id": request_id,
                            "approver": approver
                        })
                    else:
                        results["failed"] += 1
                        
                elif action == "reject":
                    success = await self.approval_system.reject_request(request_id, approver, notes)
                    if success:
                        results["rejected"] += 1
                        await self._notify("content_rejected", {
                            "request_id": request_id,
                            "approver": approver
                        })
                    else:
                        results["failed"] += 1
                        
            except Exception as e:
                logger.error(f"Failed to process approval {approval}: {e}")
                results["failed"] += 1
        
        return results
    
    async def cleanup_expired_requests(self) -> int:
        """Dọn dẹp yêu cầu hết hạn"""
        expired_count = await self.approval_system.cleanup_expired()
        
        if expired_count > 0:
            await self._notify("requests_expired", {
                "count": expired_count
            })
        
        return expired_count
    
    async def get_approval_summary(self) -> Dict[str, Any]:
        """Lấy tóm tắt phê duyệt"""
        stats = await self.get_queue_stats()
        approval_stats = await self.approval_system.get_approval_stats()
        
        return {
            "queue_stats": {
                "total_pending": stats.total_pending,
                "high_priority": stats.high_priority,
                "expired_soon": stats.expired_soon,
                "rejection_rate": stats.rejection_rate
            },
            "approval_stats": approval_stats,
            "system_status": {
                "enabled": self.approval_system.config.enabled,
                "auto_approve_threshold": self.approval_system.config.auto_approve_threshold,
                "max_pending": self.approval_system.config.max_pending_requests
            }
        }

# Factory functions
def get_approval_queue_manager(approval_system: ApprovalSystem) -> ApprovalQueueManager:
    """Lấy instance của ApprovalQueueManager"""
    return ApprovalQueueManager(approval_system)
