"""
Repository classes for AgentDev persistence
==========================================

CRUD operations for database models.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc

from .models import (
    FeedbackModel,
    UserPreferencesModel,
    RuleModel,
    LearnedSolutionModel,
    MetricModel,
)


class FeedbackRepo:
    """Repository for feedback operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, user_id: str, feedback: str, session_id: str, 
               feedback_type: str = "neutral", context: Optional[str] = None) -> FeedbackModel:
        """Create new feedback record"""
        feedback_obj = FeedbackModel(
            user_id=user_id,
            feedback=feedback,
            session_id=session_id,
            feedback_type=feedback_type,
            context=context,
            timestamp=datetime.now(timezone.utc)
        )
        self.session.add(feedback_obj)
        self.session.commit()
        self.session.refresh(feedback_obj)
        return feedback_obj
    
    def get_by_user(self, user_id: str, limit: int = 100) -> List[FeedbackModel]:
        """Get feedback by user ID"""
        return self.session.query(FeedbackModel)\
            .filter(FeedbackModel.user_id == user_id)\
            .order_by(desc(FeedbackModel.timestamp))\
            .limit(limit)\
            .all()
    
    def get_by_session(self, session_id: str) -> List[FeedbackModel]:
        """Get feedback by session ID"""
        return self.session.query(FeedbackModel)\
            .filter(FeedbackModel.session_id == session_id)\
            .order_by(desc(FeedbackModel.timestamp))\
            .all()
    
    def get_recent(self, hours: int = 24, limit: int = 100) -> List[FeedbackModel]:
        """Get recent feedback within specified hours"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        return self.session.query(FeedbackModel)\
            .filter(FeedbackModel.timestamp >= cutoff_time)\
            .order_by(desc(FeedbackModel.timestamp))\
            .limit(limit)\
            .all()


class UserPreferencesRepo:
    """Repository for user preferences operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def set_preference(self, user_id: str, key: str, value: str) -> UserPreferencesModel:
        """Set user preference"""
        existing = self.session.query(UserPreferencesModel)\
            .filter(UserPreferencesModel.user_id == user_id)\
            .filter(UserPreferencesModel.preference_key == key)\
            .first()
        
        if existing:
            setattr(existing, 'preference_value', value)
            setattr(existing, 'updated_at', datetime.now(timezone.utc))
            self.session.commit()
            return existing
        else:
            pref = UserPreferencesModel(
                user_id=user_id,
                preference_key=key,
                preference_value=value,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            self.session.add(pref)
            self.session.commit()
            self.session.refresh(pref)
            return pref
    
    def get_preference(self, user_id: str, key: str) -> Optional[str]:
        """Get user preference value"""
        pref = self.session.query(UserPreferencesModel)\
            .filter(UserPreferencesModel.user_id == user_id)\
            .filter(UserPreferencesModel.preference_key == key)\
            .first()
        return str(pref.preference_value) if pref else None
    
    def get_all_preferences(self, user_id: str) -> Dict[str, str]:
        """Get all user preferences"""
        prefs = self.session.query(UserPreferencesModel)\
            .filter(UserPreferencesModel.user_id == user_id)\
            .all()
        return {str(pref.preference_key): str(pref.preference_value) for pref in prefs}


class RuleRepo:
    """Repository for rule operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_rule(self, rule_name: str, rule_definition: str, 
                   priority: int = 0, is_active: bool = True) -> RuleModel:
        """Create new rule"""
        rule = RuleModel(
            rule_name=rule_name,
            rule_definition=rule_definition,
            priority=priority,
            is_active=is_active,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        self.session.add(rule)
        self.session.commit()
        self.session.refresh(rule)
        return rule
    
    def get_active_rules(self) -> List[RuleModel]:
        """Get all active rules ordered by priority"""
        return self.session.query(RuleModel)\
            .filter(RuleModel.is_active == True)\
            .order_by(asc(RuleModel.priority))\
            .all()
    
    def get_rule_by_name(self, rule_name: str) -> Optional[RuleModel]:
        """Get rule by name"""
        return self.session.query(RuleModel)\
            .filter(RuleModel.rule_name == rule_name)\
            .first()
    
    def update_rule(self, rule_name: str, rule_definition: str, 
                   priority: Optional[int] = None, is_active: Optional[bool] = None) -> Optional[RuleModel]:
        """Update existing rule"""
        rule = self.get_rule_by_name(rule_name)
        if rule:
            setattr(rule, 'rule_definition', rule_definition)
            setattr(rule, 'updated_at', datetime.now(timezone.utc))
            if priority is not None:
                setattr(rule, 'priority', priority)
            if is_active is not None:
                setattr(rule, 'is_active', is_active)
            self.session.commit()
            return rule
        return None


class LearnedSolutionRepo:
    """Repository for learned solutions operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def record_solution(self, error_type: str, solution: str, 
                       success_rate: float = 1.0) -> LearnedSolutionModel:
        """Record a learned solution"""
        solution_obj = LearnedSolutionModel(
            error_type=error_type,
            solution=solution,
            success_rate=success_rate,
            usage_count=1,
            created_at=datetime.now(timezone.utc),
            last_used=datetime.now(timezone.utc)
        )
        self.session.add(solution_obj)
        self.session.commit()
        self.session.refresh(solution_obj)
        return solution_obj
    
    def get_solutions_for_error(self, error_type: str) -> List[LearnedSolutionModel]:
        """Get solutions for specific error type"""
        return self.session.query(LearnedSolutionModel)\
            .filter(LearnedSolutionModel.error_type == error_type)\
            .order_by(desc(getattr(LearnedSolutionModel, 'success_rate')))\
            .all()
    
    def update_success_rate(self, solution_id: int, success: bool) -> Optional[LearnedSolutionModel]:
        """Update solution success rate"""
        solution = self.session.query(LearnedSolutionModel)\
            .filter(LearnedSolutionModel.id == solution_id)\
            .first()
        
        if solution:
            # Update success rate using exponential moving average
            alpha = 0.1
            current_rate = float(getattr(solution, 'success_rate', 1.0))
            new_rate = alpha * (1.0 if success else 0.0) + (1 - alpha) * current_rate
            setattr(solution, 'success_rate', new_rate)
            current_count = int(getattr(solution, 'usage_count', 0))
            setattr(solution, 'usage_count', current_count + 1)
            setattr(solution, 'last_used', datetime.now(timezone.utc))
            self.session.commit()
            return solution
        return None


class MetricRepo:
    """Repository for metrics operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def record_metric(self, metric_name: str, metric_value: float, 
                     metric_type: str, context: Optional[str] = None) -> MetricModel:
        """Record a metric"""
        metric = MetricModel(
            metric_name=metric_name,
            metric_value=metric_value,
            metric_type=metric_type,
            context=context,
            timestamp=datetime.now(timezone.utc)
        )
        self.session.add(metric)
        self.session.commit()
        self.session.refresh(metric)
        return metric
    
    def get_metrics_by_name(self, metric_name: str, hours: int = 24) -> List[MetricModel]:
        """Get metrics by name within specified hours"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        return self.session.query(MetricModel)\
            .filter(MetricModel.metric_name == metric_name)\
            .filter(MetricModel.timestamp >= cutoff_time)\
            .order_by(asc(MetricModel.timestamp))\
            .all()
    
    def get_metrics_summary(self, hours: int = 24) -> Dict[str, Dict[str, Any]]:
        """Get metrics summary for specified hours"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        metrics = self.session.query(MetricModel)\
            .filter(MetricModel.timestamp >= cutoff_time)\
            .all()
        
        summary: Dict[str, Dict[str, Any]] = {}
        for metric in metrics:
            metric_name = str(metric.metric_name)
            if metric_name not in summary:
                summary[metric_name] = {
                    "count": 0,
                    "total": 0.0,
                    "min": float('inf'),
                    "max": float('-inf'),
                    "type": str(metric.metric_type)
                }
            
            stats = summary[metric_name]
            stats["count"] += 1
            metric_value = float(getattr(metric, 'metric_value', 0.0))
            stats["total"] += metric_value
            stats["min"] = min(stats["min"], metric_value)
            stats["max"] = max(stats["max"], metric_value)
        
        # Calculate averages
        for _, stats in summary.items():
            if stats["count"] > 0:
                stats["avg"] = stats["total"] / stats["count"]
            else:
                stats["avg"] = 0.0
        
        return summary
