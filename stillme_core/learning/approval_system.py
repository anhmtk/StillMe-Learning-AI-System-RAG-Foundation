"""
StillMe Learning Approval System
Hệ thống phê duyệt con người cho quá trình học tập của StillMe
"""

import asyncio
import json
import logging
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from uuid import uuid4

logger = logging.getLogger(__name__)

class ApprovalStatus(Enum):
    """Trạng thái phê duyệt"""
    PENDING = "pending"           # Chờ phê duyệt
    APPROVED = "approved"         # Đã phê duyệt
    REJECTED = "rejected"         # Từ chối
    EXPIRED = "expired"          # Hết hạn
    AUTO_APPROVED = "auto_approved"  # Tự động phê duyệt

class ContentType(Enum):
    """Loại nội dung học tập"""
    RSS_ARTICLE = "rss_article"
    PDF_DOCUMENT = "pdf_document"
    TEXT_DOCUMENT = "text_document"
    EXPERIENCE = "experience"
    KNOWLEDGE_UPDATE = "knowledge_update"
    SKILL_TEMPLATE = "skill_template"

class ApprovalPriority(Enum):
    """Mức độ ưu tiên"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ApprovalRequest:
    """Yêu cầu phê duyệt"""
    request_id: str
    content_type: ContentType
    title: str
    description: str
    source_url: Optional[str]
    content_preview: str  # 500 ký tự đầu
    quality_score: float  # 0.0 - 1.0
    risk_score: float     # 0.0 - 1.0
    priority: ApprovalPriority
    status: ApprovalStatus
    created_at: datetime
    expires_at: datetime
    metadata: Dict[str, Any]
    approver_notes: Optional[str] = None
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None

@dataclass
class ApprovalConfig:
    """Cấu hình hệ thống phê duyệt"""
    enabled: bool = True
    auto_approve_threshold: float = 0.9  # Tự động phê duyệt nếu quality > 0.9
    auto_reject_threshold: float = 0.3  # Tự động từ chối nếu risk > 0.7
    expiration_hours: int = 24           # Hết hạn sau 24h
    max_pending_requests: int = 50       # Tối đa 50 yêu cầu chờ
    require_human_approval: List[ContentType] = None  # Loại cần phê duyệt thủ công
    
    def __post_init__(self):
        if self.require_human_approval is None:
            self.require_human_approval = [
                ContentType.KNOWLEDGE_UPDATE,
                ContentType.SKILL_TEMPLATE
            ]

class ApprovalSystem:
    """Hệ thống phê duyệt học tập"""
    
    def __init__(self, config: ApprovalConfig = None, db_path: str = "data/approval.db"):
        self.config = config or ApprovalConfig()
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        
    def _init_database(self):
        """Khởi tạo database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS approval_requests (
                    request_id TEXT PRIMARY KEY,
                    content_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    source_url TEXT,
                    content_preview TEXT,
                    quality_score REAL NOT NULL,
                    risk_score REAL NOT NULL,
                    priority TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    metadata TEXT,
                    approver_notes TEXT,
                    approved_at TIMESTAMP,
                    approved_by TEXT
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_status ON approval_requests(status)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at ON approval_requests(created_at)
            """)
    
    async def submit_for_approval(
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
    ) -> str:
        """Gửi nội dung để phê duyệt"""
        
        if not self.config.enabled:
            logger.info("Approval system disabled, auto-approving")
            return await self._auto_approve(content_type, title, quality_score, risk_score)
        
        # Kiểm tra giới hạn
        pending_count = await self.get_pending_count()
        if pending_count >= self.config.max_pending_requests:
            logger.warning(f"Too many pending requests ({pending_count}), rejecting new request")
            return None
        
        # Tạo request
        request_id = str(uuid4())
        expires_at = datetime.now() + timedelta(hours=self.config.expiration_hours)
        
        request = ApprovalRequest(
            request_id=request_id,
            content_type=content_type,
            title=title,
            description=description,
            source_url=source_url,
            content_preview=content_preview[:500],
            quality_score=quality_score,
            risk_score=risk_score,
            priority=priority,
            status=ApprovalStatus.PENDING,
            created_at=datetime.now(),
            expires_at=expires_at,
            metadata=metadata or {}
        )
        
        # Lưu vào database
        await self._save_request(request)
        
        # Kiểm tra auto-approval
        if await self._should_auto_approve(request):
            await self.approve_request(request_id, "auto_approval", "Auto-approved based on quality/risk scores")
            return request_id
        
        logger.info(f"Approval request submitted: {request_id} ({content_type.value})")
        return request_id
    
    async def _should_auto_approve(self, request: ApprovalRequest) -> bool:
        """Kiểm tra có nên tự động phê duyệt không"""
        
        # Nếu loại nội dung cần phê duyệt thủ công
        if request.content_type in self.config.require_human_approval:
            return False
        
        # Auto-approve nếu quality cao và risk thấp
        if (request.quality_score >= self.config.auto_approve_threshold and 
            request.risk_score <= (1.0 - self.config.auto_approve_threshold)):
            return True
        
        # Auto-reject nếu risk quá cao
        if request.risk_score >= self.config.auto_reject_threshold:
            await self.reject_request(request.request_id, "auto_rejection", "Auto-rejected due to high risk score")
            return False
        
        return False
    
    async def _auto_approve(self, content_type: ContentType, title: str, quality_score: float, risk_score: float) -> str:
        """Tự động phê duyệt khi system disabled"""
        request_id = str(uuid4())
        request = ApprovalRequest(
            request_id=request_id,
            content_type=content_type,
            title=title,
            description="Auto-approved (system disabled)",
            content_preview="",
            quality_score=quality_score,
            risk_score=risk_score,
            priority=ApprovalPriority.LOW,
            status=ApprovalStatus.AUTO_APPROVED,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=1),
            metadata={"auto_approved": True}
        )
        await self._save_request(request)
        return request_id
    
    async def approve_request(self, request_id: str, approver: str, notes: str = None) -> bool:
        """Phê duyệt yêu cầu"""
        return await self._update_request_status(
            request_id, ApprovalStatus.APPROVED, approver, notes
        )
    
    async def reject_request(self, request_id: str, approver: str, notes: str = None) -> bool:
        """Từ chối yêu cầu"""
        return await self._update_request_status(
            request_id, ApprovalStatus.REJECTED, approver, notes
        )
    
    async def _update_request_status(
        self, 
        request_id: str, 
        status: ApprovalStatus, 
        approver: str, 
        notes: str = None
    ) -> bool:
        """Cập nhật trạng thái yêu cầu"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    UPDATE approval_requests 
                    SET status = ?, approver_notes = ?, approved_at = ?, approved_by = ?
                    WHERE request_id = ?
                """, (status.value, notes, datetime.now(), approver, request_id))
                
                if cursor.rowcount == 0:
                    logger.warning(f"Request {request_id} not found")
                    return False
                
                logger.info(f"Request {request_id} {status.value} by {approver}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update request {request_id}: {e}")
            return False
    
    async def _save_request(self, request: ApprovalRequest):
        """Lưu yêu cầu vào database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO approval_requests 
                (request_id, content_type, title, description, source_url, content_preview,
                 quality_score, risk_score, priority, status, created_at, expires_at, 
                 metadata, approver_notes, approved_at, approved_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                request.request_id, request.content_type.value, request.title,
                request.description, request.source_url, request.content_preview,
                request.quality_score, request.risk_score, request.priority.value,
                request.status.value, request.created_at, request.expires_at,
                json.dumps(request.metadata), request.approver_notes,
                request.approved_at, request.approved_by
            ))
    
    async def get_pending_requests(self, limit: int = 20) -> List[ApprovalRequest]:
        """Lấy danh sách yêu cầu chờ phê duyệt"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM approval_requests 
                WHERE status = ? 
                ORDER BY priority DESC, created_at ASC 
                LIMIT ?
            """, (ApprovalStatus.PENDING.value, limit))
            
            return [self._row_to_request(row) for row in cursor.fetchall()]
    
    async def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Lấy thông tin yêu cầu"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM approval_requests WHERE request_id = ?
            """, (request_id,))
            
            row = cursor.fetchone()
            return self._row_to_request(row) if row else None
    
    async def get_pending_count(self) -> int:
        """Đếm số yêu cầu chờ phê duyệt"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT COUNT(*) FROM approval_requests WHERE status = ?
            """, (ApprovalStatus.PENDING.value,))
            return cursor.fetchone()[0]
    
    async def cleanup_expired(self) -> int:
        """Dọn dẹp yêu cầu hết hạn"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                UPDATE approval_requests 
                SET status = ? 
                WHERE status = ? AND expires_at < ?
            """, (ApprovalStatus.EXPIRED.value, ApprovalStatus.PENDING.value, datetime.now()))
            
            expired_count = cursor.rowcount
            if expired_count > 0:
                logger.info(f"Expired {expired_count} requests")
            
            return expired_count
    
    def _row_to_request(self, row: sqlite3.Row) -> ApprovalRequest:
        """Chuyển đổi database row thành ApprovalRequest"""
        return ApprovalRequest(
            request_id=row['request_id'],
            content_type=ContentType(row['content_type']),
            title=row['title'],
            description=row['description'],
            source_url=row['source_url'],
            content_preview=row['content_preview'],
            quality_score=row['quality_score'],
            risk_score=row['risk_score'],
            priority=ApprovalPriority(row['priority']),
            status=ApprovalStatus(row['status']),
            created_at=datetime.fromisoformat(row['created_at']),
            expires_at=datetime.fromisoformat(row['expires_at']),
            metadata=json.loads(row['metadata'] or '{}'),
            approver_notes=row['approver_notes'],
            approved_at=datetime.fromisoformat(row['approved_at']) if row['approved_at'] else None,
            approved_by=row['approved_by']
        )
    
    async def get_approval_stats(self) -> Dict[str, Any]:
        """Lấy thống kê phê duyệt"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT status, COUNT(*) as count 
                FROM approval_requests 
                GROUP BY status
            """)
            
            stats = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Thêm thống kê theo loại nội dung
            cursor = conn.execute("""
                SELECT content_type, COUNT(*) as count 
                FROM approval_requests 
                GROUP BY content_type
            """)
            
            content_stats = {row[0]: row[1] for row in cursor.fetchall()}
            
            return {
                "status_counts": stats,
                "content_type_counts": content_stats,
                "total_requests": sum(stats.values()),
                "pending_count": stats.get(ApprovalStatus.PENDING.value, 0),
                "approval_rate": self._calculate_approval_rate(stats)
            }
    
    def _calculate_approval_rate(self, stats: Dict[str, int]) -> float:
        """Tính tỷ lệ phê duyệt"""
        total_processed = stats.get(ApprovalStatus.APPROVED.value, 0) + stats.get(ApprovalStatus.REJECTED.value, 0)
        if total_processed == 0:
            return 0.0
        return stats.get(ApprovalStatus.APPROVED.value, 0) / total_processed

# Factory functions
def get_approval_system(config: ApprovalConfig = None) -> ApprovalSystem:
    """Lấy instance của ApprovalSystem"""
    return ApprovalSystem(config)

async def initialize_approval_system(config: ApprovalConfig = None) -> ApprovalSystem:
    """Khởi tạo hệ thống phê duyệt"""
    system = ApprovalSystem(config)
    await system.cleanup_expired()  # Dọn dẹp yêu cầu hết hạn
    return system
