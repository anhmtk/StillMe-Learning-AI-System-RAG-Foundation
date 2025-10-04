#!/usr/bin/env python3
# ruff: noqa: B010
"""
AgentDev Persistence Repository
===============================

CRUD operations for AgentDev database models.
"""

import json
from datetime import UTC, datetime, timedelta
from typing import Any  # Cải thiện imports

# THAY ĐỔI: Phải import các đối tượng SQLAlchemy rõ ràng hơn
from sqlalchemy import desc
from sqlalchemy.orm import Session, sessionmaker

from .models import (
    FeedbackModel,
    LearnedSolutionModel,
    MetricModel,
    RuleModel,
    UserPreferencesModel,
)


def get_session_factory(engine: Any):
    """Create a session factory for the given engine."""
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


# TYPE ANNOTATION GUIDANCE: Để tránh lỗi type checking, hãy:
# 1. Import đầy đủ các type từ SQLAlchemy: from sqlalchemy.orm import Query
# 2. Sử dụng type hints rõ ràng: def method() -> list[Model]:
# 3. Validate runtime trước khi cast: if isinstance(obj, ExpectedType): cast(ExpectedType, obj)
# 4. Tránh # type: ignore - thay bằng proper type annotations và runtime validation


class FeedbackRepo:
    """Repository for feedback operations"""

    # THAY ĐỔI: Khai báo rõ ràng kiểu Session
    def __init__(self, session: Session):
        self.session: Session = session

    def create_feedback(
        self, user_id: str, feedback: str, session_id: str | None = None
    ) -> FeedbackModel:
        """Create new feedback"""
        feedback_obj = FeedbackModel(
            user_id=user_id,
            feedback=feedback,
            session_id=session_id,
        )
        self.session.add(feedback_obj)
        self.session.commit()
        self.session.refresh(feedback_obj)
        return feedback_obj

    def get_feedback_by_user(
        self, user_id: str, limit: int = 100
    ) -> list[FeedbackModel]:  # THAY ĐỔI: Dùng List[Model]
        """Get feedback by user ID"""
        return (
            self.session.query(
                FeedbackModel
            )  # THAY ĐỔI: Giữ nguyên cách viết query truyền thống
            .filter(FeedbackModel.user_id == user_id)
            .order_by(desc(FeedbackModel.timestamp))
            .limit(limit)
            .all()
        )

    def get_feedback_by_session(
        self, session_id: str
    ) -> list[FeedbackModel]:  # THAY ĐỔI: Dùng List[Model]
        """Get feedback by session ID"""
        return (
            self.session.query(FeedbackModel)
            .filter(FeedbackModel.session_id == session_id)
            .order_by(desc(FeedbackModel.timestamp))
            .all()
        )

    def get_recent_feedback(
        self, hours: int = 24
    ) -> list[FeedbackModel]:  # THAY ĐỔI: Dùng List[Model]
        """Get recent feedback within specified hours"""
        # THAY ĐỔI: Sử dụng datetime.now(UTC) an toàn hơn, nhưng nên dùng datetime.utcnow() nếu model không hỗ trợ UTC
        cutoff_time = datetime.now(UTC) - timedelta(hours=hours)
        return (
            self.session.query(FeedbackModel)
            .filter(FeedbackModel.timestamp >= cutoff_time)
            .order_by(desc(FeedbackModel.timestamp))
            .all()
        )


class UserPreferencesRepo:
    """Repository for user preferences operations"""

    def __init__(self, session: Session):
        self.session: Session = session  # THAY ĐỔI: Khai báo rõ ràng kiểu Session

    def set_preference(
        self, user_id: str, key: str, value: str
    ) -> UserPreferencesModel:
        """Set user preference"""
        existing: UserPreferencesModel | None = (  # THAY ĐỔI: Khai báo rõ kiểu
            self.session.query(UserPreferencesModel)
            .filter(UserPreferencesModel.user_id == user_id)
            .filter(UserPreferencesModel.preference_key == key)
            .first()
        )

        if existing:
            setattr(existing, "preference_value", value)
            setattr(existing, "updated_at", datetime.now(UTC))
            self.session.commit()
            return existing
        else:
            pref = UserPreferencesModel(
                user_id=user_id,
                preference_key=key,
                preference_value=value,
            )
            self.session.add(pref)
            self.session.commit()
            self.session.refresh(pref)
            return pref

    def get_preference(
        self, user_id: str, key: str
    ) -> str | None:  # THAY ĐỔI: Dùng Optional[str]
        """Get user preference"""
        pref: UserPreferencesModel | None = (  # THAY ĐỔI: Khai báo rõ kiểu
            self.session.query(UserPreferencesModel)
            .filter(UserPreferencesModel.user_id == user_id)
            .filter(UserPreferencesModel.preference_key == key)
            .first()
        )
        # THAY ĐỔI: Ép kiểu string an toàn hơn
        return str(pref.preference_value) if pref else None

    def get_all_preferences(
        self, user_id: str
    ) -> dict[str, str]:  # THAY ĐỔI: Dùng Dict[str, str]
        """Get all user preferences"""
        prefs: list[UserPreferencesModel] = (  # THAY ĐỔI: Khai báo rõ kiểu
            self.session.query(UserPreferencesModel)
            .filter(UserPreferencesModel.user_id == user_id)
            .all()
        )
        # THAY ĐỔI: Đảm bảo cả key và value đều là string
        return {str(pref.preference_key): str(pref.preference_value) for pref in prefs}


class RuleRepo:
    """Repository for rules operations"""

    def __init__(self, session: Session):
        self.session: Session = session

    def create_rule(
        self, rule_name: str, rule_definition: str, priority: int = 0
    ) -> RuleModel:
        """Create new rule"""
        rule = RuleModel(
            rule_name=rule_name,
            rule_definition=rule_definition,
            priority=priority,
        )
        self.session.add(rule)
        self.session.commit()
        self.session.refresh(rule)
        return rule

    def update_rule(
        self,
        rule_name: str,
        rule_definition: str,
        priority: int | None = None,
        is_active: bool | None = None,
    ) -> RuleModel | None:
        """Update existing rule"""
        rule: RuleModel | None = self.get_rule_by_name(rule_name)
        if rule:
            setattr(rule, "rule_definition", rule_definition)
            setattr(rule, "updated_at", datetime.now(UTC))
            if priority is not None:
                setattr(rule, "priority", priority)
            if is_active is not None:
                setattr(rule, "is_active", is_active)
            self.session.commit()
            return rule
        return None

    def get_rule_by_name(self, rule_name: str) -> RuleModel | None:
        """Get rule by name"""
        return (
            self.session.query(RuleModel)
            .filter(RuleModel.rule_name == rule_name)
            .first()
        )

    def get_active_rules(self) -> list[RuleModel]:
        """Get all active rules ordered by priority"""
        return (
            self.session.query(RuleModel)
            .filter(RuleModel.is_active)
            .order_by(desc(RuleModel.priority))
            .all()
        )

    def delete_rule(self, rule_name: str) -> bool:
        """Delete rule by name"""
        rule: RuleModel | None = self.get_rule_by_name(rule_name)
        if rule:
            self.session.delete(rule)
            self.session.commit()
            return True
        return False


class LearnedSolutionRepo:
    """Repository for learned solutions operations"""

    def __init__(self, session: Session):
        self.session: Session = session

    def create_solution(self, error_type: str, solution: str) -> LearnedSolutionModel:
        """Create new learned solution"""
        solution_obj = LearnedSolutionModel(
            error_type=error_type,
            solution=solution,
        )
        self.session.add(solution_obj)
        self.session.commit()
        self.session.refresh(solution_obj)
        return solution_obj

    def get_solutions_for_error(self, error_type: str) -> list[LearnedSolutionModel]:
        """Get solutions for specific error type"""
        return (
            self.session.query(LearnedSolutionModel)
            .filter(LearnedSolutionModel.error_type == error_type)
            .order_by(desc(LearnedSolutionModel.success_rate))
            .all()
        )

    def update_success_rate(
        self, solution_id: int, success: bool
    ) -> LearnedSolutionModel | None:
        """Update solution success rate"""
        solution: LearnedSolutionModel | None = (  # THAY ĐỔI: Khai báo rõ kiểu
            self.session.query(LearnedSolutionModel)
            .filter(LearnedSolutionModel.id == solution_id)
            .first()
        )

        if solution:
            # Update success rate using exponential moving average
            alpha = 0.1
            # THAY ĐỔI: Kiểm tra an toàn trước khi ép kiểu
            current_rate = float(getattr(solution, "success_rate", 1.0))
            new_rate = alpha * (1.0 if success else 0.0) + (1 - alpha) * current_rate
            setattr(solution, "success_rate", new_rate)

            # THAY ĐỔI: Kiểm tra an toàn trước khi ép kiểu
            current_count = int(getattr(solution, "usage_count", 0))
            setattr(solution, "usage_count", current_count + 1)
            setattr(solution, "last_used", datetime.now(UTC))
            self.session.commit()
            return solution
        return None

    def get_top_solutions(
        self, error_type: str, limit: int = 5
    ) -> list[LearnedSolutionModel]:
        """Get top solutions for error type"""
        return (
            self.session.query(LearnedSolutionModel)
            .filter(LearnedSolutionModel.error_type == error_type)
            .order_by(desc(LearnedSolutionModel.success_rate))
            .limit(limit)
            .all()
        )


class MetricRepo:
    """Repository for metrics operations"""

    def __init__(self, session: Session):
        self.session: Session = session

    def record_metric(
        self,
        name: str,
        value: float,
        metric_type: str,
        context: dict[str, Any] | None = None,
    ) -> MetricModel:
        """Record a metric"""
        metric = MetricModel(
            metric_name=name,
            metric_value=value,
            metric_type=metric_type,
            context=json.dumps(context) if context else None,
        )
        self.session.add(metric)
        self.session.commit()
        self.session.refresh(metric)
        return metric

    def get_metrics_by_name(self, name: str, limit: int = 100) -> list[MetricModel]:
        """Get metrics by name"""
        return (
            self.session.query(MetricModel)
            .filter(MetricModel.metric_name == name)
            .order_by(desc(MetricModel.timestamp))
            .limit(limit)
            .all()
        )

    def get_metrics_by_type(
        self, metric_type: str, limit: int = 100
    ) -> list[MetricModel]:
        """Get metrics by type"""
        return (
            self.session.query(MetricModel)
            .filter(MetricModel.metric_type == metric_type)
            .order_by(desc(MetricModel.timestamp))
            .limit(limit)
            .all()
        )

    def get_recent_metrics(self, hours: int = 24) -> list[MetricModel]:
        """Get recent metrics within specified hours"""
        cutoff_time = datetime.now(UTC) - timedelta(hours=hours)
        return (
            self.session.query(MetricModel)
            .filter(MetricModel.timestamp >= cutoff_time)
            .order_by(desc(MetricModel.timestamp))
            .all()
        )

    def get_metrics_summary(self, name: str | None = None) -> dict[str, Any]:
        """Get metrics summary"""
        query = self.session.query(MetricModel)
        if name:
            query = query.filter(MetricModel.metric_name == name)

        metrics: list[MetricModel] = query.all()
        if not metrics:
            return {"count": 0, "avg": 0.0, "min": 0.0, "max": 0.0}

        # THAY ĐỔI: Kiểm tra an toàn trước khi ép kiểu float
        values = [float(getattr(metric, "metric_value", 0.0)) for metric in metrics]
        return {
            "count": len(values),
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
        }
