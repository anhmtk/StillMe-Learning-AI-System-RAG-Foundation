"""
StillMe Approval Queue
Human-in-the-loop approval system for content ingestion.
"""

import logging
import json
import yaml
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
import hashlib

from stillme_core.learning.parser.normalize import NormalizedContent
from stillme_core.learning.score.quality import QualityScore
from stillme_core.learning.gates.license_gate import LicenseDecision
from stillme_core.learning.risk.injection_scan import RiskAssessment

log = logging.getLogger(__name__)

@dataclass
class ApprovalItem:
    """Item in the approval queue."""
    id: str
    content: NormalizedContent
    quality_score: QualityScore
    license_decision: LicenseDecision
    risk_assessment: RiskAssessment
    novelty_score: float
    recommendation: str
    created_at: str
    status: str = "pending"  # pending, approved, rejected
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    rejection_reason: Optional[str] = None

class ApprovalQueue:
    """Manages approval queue for content ingestion."""
    
    def __init__(self, queue_file: str = "data/approval_queue.json", 
                 policy_file: str = "policies/learning_policy.yaml"):
        self.queue_file = Path(queue_file)
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)
        self.policy_file = Path(policy_file)
        
        # Load policy
        self.policy = self._load_policy()
        self.max_recommendations = self.policy.get('quotas', {}).get('max_recommendations_per_day', 5)
        
        # Load existing queue
        self.queue: List[ApprovalItem] = []
        self._load_queue()
        
        log.info(f"Approval queue initialized with {len(self.queue)} items")
    
    def _load_policy(self) -> Dict:
        """Load learning policy."""
        try:
            if self.policy_file.exists():
                with open(self.policy_file, 'r') as f:
                    return yaml.safe_load(f)
            else:
                return {'quotas': {'max_recommendations_per_day': 5}}
        except Exception as e:
            log.error(f"Failed to load policy: {e}")
            return {'quotas': {'max_recommendations_per_day': 5}}
    
    def _load_queue(self):
        """Load approval queue from file."""
        if self.queue_file.exists():
            try:
                with open(self.queue_file, 'r') as f:
                    data = json.load(f)
                
                self.queue = []
                for item_data in data.get('items', []):
                    # Reconstruct objects from dict data
                    content = NormalizedContent(**item_data['content'])
                    quality_score = QualityScore(**item_data['quality_score'])
                    license_decision = LicenseDecision(**item_data['license_decision'])
                    risk_assessment = RiskAssessment(**item_data['risk_assessment'])
                    
                    item = ApprovalItem(
                        id=item_data['id'],
                        content=content,
                        quality_score=quality_score,
                        license_decision=license_decision,
                        risk_assessment=risk_assessment,
                        novelty_score=item_data['novelty_score'],
                        recommendation=item_data['recommendation'],
                        created_at=item_data['created_at'],
                        status=item_data.get('status', 'pending'),
                        approved_by=item_data.get('approved_by'),
                        approved_at=item_data.get('approved_at'),
                        rejection_reason=item_data.get('rejection_reason')
                    )
                    self.queue.append(item)
                
                log.info(f"Loaded {len(self.queue)} items from approval queue")
            except Exception as e:
                log.error(f"Failed to load approval queue: {e}")
                self.queue = []
    
    def _save_queue(self):
        """Save approval queue to file."""
        try:
            data = {
                'items': [],
                'last_updated': datetime.now().isoformat()
            }
            
            for item in self.queue:
                item_data = {
                    'id': item.id,
                    'content': asdict(item.content),
                    'quality_score': asdict(item.quality_score),
                    'license_decision': asdict(item.license_decision),
                    'risk_assessment': asdict(item.risk_assessment),
                    'novelty_score': item.novelty_score,
                    'recommendation': item.recommendation,
                    'created_at': item.created_at,
                    'status': item.status,
                    'approved_by': item.approved_by,
                    'approved_at': item.approved_at,
                    'rejection_reason': item.rejection_reason
                }
                data['items'].append(item_data)
            
            with open(self.queue_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            log.info(f"Saved approval queue with {len(self.queue)} items")
        except Exception as e:
            log.error(f"Failed to save approval queue: {e}")
    
    def _generate_recommendation(self, content: NormalizedContent, 
                               quality_score: QualityScore,
                               license_decision: LicenseDecision,
                               risk_assessment: RiskAssessment,
                               novelty_score: float) -> str:
        """Generate human-readable recommendation."""
        reasons = []
        
        # Quality reasons
        if quality_score.overall_score >= 0.8:
            reasons.append("High quality content")
        elif quality_score.overall_score >= 0.6:
            reasons.append("Good quality content")
        else:
            reasons.append("Low quality content")
        
        # License reasons
        if license_decision.allowed:
            reasons.append("License approved")
        else:
            reasons.append("License issues")
        
        # Risk reasons
        if risk_assessment.safe:
            reasons.append("Low risk")
        else:
            reasons.append(f"Risk level: {risk_assessment.risk_level}")
        
        # Novelty reasons
        if novelty_score >= 0.7:
            reasons.append("Highly novel")
        elif novelty_score >= 0.4:
            reasons.append("Moderately novel")
        else:
            reasons.append("Low novelty")
        
        # Source reputation
        if content.domain == 'arxiv.org':
            reasons.append("Academic source")
        elif content.domain in ['openai.com', 'deepmind.com']:
            reasons.append("Industry leader")
        
        # Content type
        if content.content_type == 'research':
            reasons.append("Research content")
        elif content.content_type == 'blog':
            reasons.append("Blog content")
        
        # Overall recommendation
        if (quality_score.overall_score >= 0.7 and 
            license_decision.allowed and 
            risk_assessment.safe and 
            novelty_score >= 0.3):
            recommendation = "APPROVE - " + ", ".join(reasons)
        elif (quality_score.overall_score >= 0.5 and 
              license_decision.allowed and 
              risk_assessment.risk_level in ['low', 'medium']):
            recommendation = "REVIEW - " + ", ".join(reasons)
        else:
            recommendation = "REJECT - " + ", ".join(reasons)
        
        return recommendation
    
    def add_item(self, content: NormalizedContent,
                quality_score: QualityScore,
                license_decision: LicenseDecision,
                risk_assessment: RiskAssessment,
                novelty_score: float) -> str:
        """Add item to approval queue."""
        # Generate unique ID
        item_id = hashlib.md5(f"{content.url}{content.title}{datetime.now().isoformat()}".encode()).hexdigest()
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            content, quality_score, license_decision, risk_assessment, novelty_score
        )
        
        # Create approval item
        item = ApprovalItem(
            id=item_id,
            content=content,
            quality_score=quality_score,
            license_decision=license_decision,
            risk_assessment=risk_assessment,
            novelty_score=novelty_score,
            recommendation=recommendation,
            created_at=datetime.now().isoformat()
        )
        
        # Add to queue
        self.queue.append(item)
        
        # Save queue
        self._save_queue()
        
        log.info(f"Added item to approval queue: {item_id}")
        return item_id
    
    def get_pending_items(self, limit: Optional[int] = None) -> List[ApprovalItem]:
        """Get pending items from queue."""
        pending_items = [item for item in self.queue if item.status == "pending"]
        
        # Sort by quality score and novelty
        pending_items.sort(key=lambda x: (x.quality_score.overall_score, x.novelty_score), reverse=True)
        
        if limit:
            pending_items = pending_items[:limit]
        
        return pending_items
    
    def get_top_recommendations(self, limit: Optional[int] = None) -> List[ApprovalItem]:
        """Get top recommendations for human review."""
        if limit is None:
            limit = self.max_recommendations
        
        # Get pending items
        pending_items = self.get_pending_items()
        
        # Filter for high-quality, safe items
        top_items = []
        for item in pending_items:
            if (item.quality_score.overall_score >= 0.6 and
                item.license_decision.allowed and
                item.risk_assessment.safe and
                item.novelty_score >= 0.3):
                top_items.append(item)
        
        return top_items[:limit]
    
    def approve_item(self, item_id: str, approved_by: str) -> bool:
        """Approve an item in the queue."""
        for item in self.queue:
            if item.id == item_id and item.status == "pending":
                item.status = "approved"
                item.approved_by = approved_by
                item.approved_at = datetime.now().isoformat()
                
                self._save_queue()
                log.info(f"Approved item: {item_id} by {approved_by}")
                return True
        
        return False
    
    def reject_item(self, item_id: str, rejected_by: str, reason: str) -> bool:
        """Reject an item in the queue."""
        for item in self.queue:
            if item.id == item_id and item.status == "pending":
                item.status = "rejected"
                item.approved_by = rejected_by
                item.approved_at = datetime.now().isoformat()
                item.rejection_reason = reason
                
                self._save_queue()
                log.info(f"Rejected item: {item_id} by {rejected_by} - {reason}")
                return True
        
        return False
    
    def get_item(self, item_id: str) -> Optional[ApprovalItem]:
        """Get item by ID."""
        for item in self.queue:
            if item.id == item_id:
                return item
        return None
    
    def get_statistics(self) -> Dict:
        """Get approval queue statistics."""
        total_items = len(self.queue)
        pending_items = len([item for item in self.queue if item.status == "pending"])
        approved_items = len([item for item in self.queue if item.status == "approved"])
        rejected_items = len([item for item in self.queue if item.status == "rejected"])
        
        # Quality distribution
        quality_scores = [item.quality_score.overall_score for item in self.queue]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        # Risk distribution
        risk_levels = {}
        for item in self.queue:
            risk_level = item.risk_assessment.risk_level
            risk_levels[risk_level] = risk_levels.get(risk_level, 0) + 1
        
        return {
            'total_items': total_items,
            'pending_items': pending_items,
            'approved_items': approved_items,
            'rejected_items': rejected_items,
            'average_quality': round(avg_quality, 3),
            'risk_distribution': risk_levels,
            'max_recommendations_per_day': self.max_recommendations
        }
    
    def generate_markdown_report(self) -> str:
        """Generate markdown report of top recommendations."""
        top_items = self.get_top_recommendations()
        
        if not top_items:
            return "# Approval Queue Report\n\nNo items in approval queue.\n"
        
        report = f"# Approval Queue Report\n\n"
        report += f"**Generated:** {datetime.now().isoformat()}\n"
        report += f"**Items in queue:** {len(self.get_pending_items())}\n"
        report += f"**Top recommendations:** {len(top_items)}\n\n"
        
        for i, item in enumerate(top_items, 1):
            report += f"## {i}. {item.content.title}\n\n"
            report += f"**Source:** {item.content.source} ({item.content.domain})\n"
            report += f"**URL:** {item.content.url}\n"
            report += f"**Author:** {item.content.author or 'Unknown'}\n"
            report += f"**Published:** {item.content.published_date or 'Unknown'}\n"
            report += f"**License:** {item.content.license or 'Unknown'}\n\n"
            
            report += f"**Quality Score:** {item.quality_score.overall_score:.2f}\n"
            report += f"**Novelty Score:** {item.novelty_score:.2f}\n"
            report += f"**Risk Level:** {item.risk_assessment.risk_level}\n"
            report += f"**License Status:** {'✅ Allowed' if item.license_decision.allowed else '❌ Rejected'}\n\n"
            
            report += f"**Summary:** {item.content.summary[:200]}...\n\n"
            
            report += f"**Recommendation:** {item.recommendation}\n\n"
            
            report += f"**Item ID:** `{item.id}`\n\n"
            report += "---\n\n"
        
        return report

# Global approval queue instance
_approval_queue = None

def get_approval_queue() -> ApprovalQueue:
    """Get global approval queue instance."""
    global _approval_queue
    if _approval_queue is None:
        _approval_queue = ApprovalQueue()
    return _approval_queue

def add_to_approval_queue(content: NormalizedContent,
                         quality_score: QualityScore,
                         license_decision: LicenseDecision,
                         risk_assessment: RiskAssessment,
                         novelty_score: float) -> str:
    """Convenience function to add item to approval queue."""
    queue = get_approval_queue()
    return queue.add_item(content, quality_score, license_decision, risk_assessment, novelty_score)
