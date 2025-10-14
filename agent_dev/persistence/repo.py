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
    FeedbackEvent,
    FeedbackModel,
    LearnedSolutionModel,
    MetricsDaily,
    MetricModel,
    PatchHistory,
    RuleDef,
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

    # Self-Improvement Loop CRUD methods

    def record_feedback(
        self,
        source: str,
        test_name: str | None,
        error_sig: str,
        rule_applied: str | None,
        outcome: str,
        notes: str | None = None,
    ) -> int:
        """Record feedback event"""
        feedback = FeedbackEvent(
            source=source,
            test_name=test_name,
            error_sig=error_sig,
            rule_applied=rule_applied,
            outcome=outcome,
            notes=notes,
        )
        self.session.add(feedback)
        self.session.commit()
        return feedback.id

    def record_metrics(
        self,
        date: datetime,
        pass_rate: float,
        fail_rate: float,
        coverage_overall: float,
        coverage_touched: float,
        mttr_min: float | None = None,
        lint_errors: int = 0,
        pyright_errors: int = 0,
    ) -> int:
        """Record daily metrics"""
        metrics = MetricsDaily(
            date=date,
            pass_rate=pass_rate,
            fail_rate=fail_rate,
            coverage_overall=coverage_overall,
            coverage_touched=coverage_touched,
            mttr_min=mttr_min,
            lint_errors=lint_errors,
            pyright_errors=pyright_errors,
        )
        self.session.add(metrics)
        self.session.commit()
        return metrics.id

    def record_patch(
        self,
        files_changed: list[str],
        tests_failed_before: int,
        tests_passed_after: int,
        coverage_before: float,
        coverage_after: float,
        diff_hash: str,
    ) -> int:
        """Record patch history"""
        patch = PatchHistory(
            files_changed=json.dumps(files_changed),
            tests_failed_before=tests_failed_before,
            tests_passed_after=tests_passed_after,
            coverage_before=coverage_before,
            coverage_after=coverage_after,
            diff_hash=diff_hash,
        )
        self.session.add(patch)
        self.session.commit()
        return patch.id

    def get_rules_by_priority(self) -> list[RuleDef]:
        """Get rules ordered by priority (hits * severity_weight)"""
        rules = self.session.query(RuleDef).filter(RuleDef.enabled == True).all()

        # Calculate priority scores
        severity_weights = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        for rule in rules:
            weight = severity_weights.get(rule.severity, 2)
            rule.priority_score = rule.hits * weight

        return sorted(rules, key=lambda r: r.priority_score, reverse=True)

    def update_rule_hits(self, rule_name: str, success: bool = True) -> None:
        """Update rule hit count and last applied timestamp"""
        rule = self.session.query(RuleDef).filter(RuleDef.name == rule_name).first()
        if rule:
            rule.hits += 1
            rule.last_applied_at = datetime.now(UTC)
            self.session.commit()

    def get_recent_metrics(self, days: int = 7) -> list[MetricsDaily]:
        """Get recent metrics for anomaly detection"""
        cutoff = datetime.now(UTC) - timedelta(days=days)
        return (
            self.session.query(MetricsDaily)
            .filter(MetricsDaily.date >= cutoff)
            .order_by(MetricsDaily.date.desc())
            .all()
        )


class AgentDevRepo:
    """Main repository class that combines all repos"""

    def __init__(self, engine: Any):
        self.engine = engine
        self.session_factory = get_session_factory(engine)
        self.session = self.session_factory()

        self.feedback_repo = FeedbackRepo(self.session)
        self.user_prefs_repo = UserPreferencesRepo(self.session)
        self.rule_repo = RuleRepo(self.session)
        self.learned_solution_repo = LearnedSolutionRepo(self.session)
        self.metric_repo = MetricRepo(self.session)

    # Delegate methods to appropriate repos
    def record_feedback(self, *args, **kwargs):
        return self.feedback_repo.record_feedback(*args, **kwargs)

    def record_metrics(self, *args, **kwargs):
        return self.metric_repo.record_metrics(*args, **kwargs)

    def record_patch(self, *args, **kwargs):
        return self.metric_repo.record_patch(*args, **kwargs)

    def get_rules_by_priority(self, *args, **kwargs):
        return self.rule_repo.get_rules_by_priority(*args, **kwargs)

    def update_rule_hits(self, *args, **kwargs):
        return self.rule_repo.update_rule(*args, **kwargs)

    def get_recent_metrics(self, *args, **kwargs):
        return self.metric_repo.get_recent_metrics(*args, **kwargs)