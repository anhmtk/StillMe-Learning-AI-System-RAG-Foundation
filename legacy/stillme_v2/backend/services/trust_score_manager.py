"""
Trust Score Manager for StillMe V2
Manages dynamic trust scoring based on learning outcomes and performance
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class TrustScoreRecord:
    """Record of trust score changes for a source"""
    source_name: str
    old_score: float
    new_score: float
    reason: str
    timestamp: str
    learning_outcome: Optional[bool] = None

@dataclass
class SourcePerformance:
    """Performance metrics for a data source"""
    source_name: str
    total_proposals: int = 0
    successful_learnings: int = 0
    failed_learnings: int = 0
    avg_quality_score: float = 0.0
    last_updated: str = ""
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_proposals == 0:
            return 0.0
        return self.successful_learnings / self.total_proposals
    
    @property
    def trust_score(self) -> float:
        """Calculate current trust score based on performance"""
        base_score = 0.5
        success_bonus = self.success_rate * 0.3
        quality_bonus = self.avg_quality_score * 0.2
        
        return min(1.0, base_score + success_bonus + quality_bonus)

class TrustScoreManager:
    """Manages dynamic trust scoring for data sources"""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize Trust Score Manager"""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.performance_file = self.data_dir / "source_performance.json"
        self.trust_history_file = self.data_dir / "trust_history.json"
        
        # Load existing data
        self.source_performance = self._load_performance_data()
        self.trust_history = self._load_trust_history()
        
        # Trust score update parameters
        self.success_reward = 0.01
        self.failure_penalty = 0.005
        self.min_trust_score = 0.1
        self.max_trust_score = 1.0
        
        logger.info("Trust Score Manager initialized")
    
    def _load_performance_data(self) -> Dict[str, SourcePerformance]:
        """Load source performance data from file"""
        if not self.performance_file.exists():
            return {}
        
        try:
            with open(self.performance_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            performance = {}
            for source_name, perf_data in data.items():
                performance[source_name] = SourcePerformance(**perf_data)
            
            return performance
        except Exception as e:
            logger.error(f"Failed to load performance data: {e}")
            return {}
    
    def _load_trust_history(self) -> List[TrustScoreRecord]:
        """Load trust score history from file"""
        if not self.trust_history_file.exists():
            return []
        
        try:
            with open(self.trust_history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return [TrustScoreRecord(**record) for record in data]
        except Exception as e:
            logger.error(f"Failed to load trust history: {e}")
            return []
    
    def _save_performance_data(self):
        """Save source performance data to file"""
        try:
            data = {
                source_name: asdict(perf) 
                for source_name, perf in self.source_performance.items()
            }
            
            with open(self.performance_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Failed to save performance data: {e}")
    
    def _save_trust_history(self):
        """Save trust score history to file"""
        try:
            data = [asdict(record) for record in self.trust_history]
            
            with open(self.trust_history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Failed to save trust history: {e}")
    
    def get_trust_score(self, source_name: str) -> float:
        """Get current trust score for a source"""
        if source_name not in self.source_performance:
            # Initialize with default score
            self.source_performance[source_name] = SourcePerformance(
                source_name=source_name,
                last_updated=datetime.now().isoformat()
            )
            return 0.5  # Default trust score
        
        return self.source_performance[source_name].trust_score
    
    def update_performance(self, source_name: str, learning_outcome: bool, quality_score: float):
        """Update source performance based on learning outcome"""
        if source_name not in self.source_performance:
            self.source_performance[source_name] = SourcePerformance(
                source_name=source_name,
                last_updated=datetime.now().isoformat()
            )
        
        perf = self.source_performance[source_name]
        
        # Update metrics
        perf.total_proposals += 1
        if learning_outcome:
            perf.successful_learnings += 1
        else:
            perf.failed_learnings += 1
        
        # Update average quality score
        total_quality = perf.avg_quality_score * (perf.total_proposals - 1) + quality_score
        perf.avg_quality_score = total_quality / perf.total_proposals
        
        perf.last_updated = datetime.now().isoformat()
        
        # Record trust score change
        old_score = self.get_trust_score(source_name)
        new_score = perf.trust_score
        
        if abs(new_score - old_score) > 0.001:  # Only record significant changes
            record = TrustScoreRecord(
                source_name=source_name,
                old_score=old_score,
                new_score=new_score,
                reason=f"Performance update: {learning_outcome}",
                timestamp=datetime.now().isoformat(),
                learning_outcome=learning_outcome
            )
            self.trust_history.append(record)
            
            logger.info(f"Trust score updated for {source_name}: {old_score:.3f} → {new_score:.3f}")
        
        # Save data
        self._save_performance_data()
        self._save_trust_history()
    
    def get_performance_summary(self) -> Dict[str, Dict]:
        """Get performance summary for all sources"""
        summary = {}
        
        for source_name, perf in self.source_performance.items():
            summary[source_name] = {
                "trust_score": perf.trust_score,
                "success_rate": perf.success_rate,
                "total_proposals": perf.total_proposals,
                "avg_quality_score": perf.avg_quality_score,
                "last_updated": perf.last_updated
            }
        
        return summary
    
    def get_trust_history(self, source_name: Optional[str] = None, days: int = 30) -> List[TrustScoreRecord]:
        """Get trust score history for a source or all sources"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        if source_name:
            return [
                record for record in self.trust_history
                if record.source_name == source_name and 
                datetime.fromisoformat(record.timestamp) >= cutoff_date
            ]
        else:
            return [
                record for record in self.trust_history
                if datetime.fromisoformat(record.timestamp) >= cutoff_date
            ]
    
    def reset_source_performance(self, source_name: str):
        """Reset performance data for a source"""
        if source_name in self.source_performance:
            del self.source_performance[source_name]
            self._save_performance_data()
            logger.info(f"Reset performance data for {source_name}")
    
    def get_recommended_threshold(self, category: str) -> float:
        """Get recommended auto-approval threshold for a category"""
        # Domain-specific thresholds
        thresholds = {
            "ai_research": 0.9,
            "technology": 0.8,
            "general": 0.7,
            "weather": 0.6,
            "news": 0.75,
            "science": 0.85
        }
        
        return thresholds.get(category, 0.8)

# Global trust score manager instance
trust_score_manager = TrustScoreManager()
