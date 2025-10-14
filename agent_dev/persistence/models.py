#!/usr/bin/env python3
"""
AgentDev Persistence Models
===========================

SQLModel/SQLAlchemy models for AgentDev database tables.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class FeedbackModel(Base):
    """Feedback database model"""

    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), nullable=False, index=True)
    feedback = Column(Text, nullable=False)
    session_id = Column(String(255), nullable=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    __table_args__ = (
        Index("idx_feedback_user_timestamp", "user_id", "timestamp"),
        Index("idx_feedback_session", "session_id"),
    )


class UserPreferencesModel(Base):
    """User preferences database model"""

    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), nullable=False, index=True)
    preference_key = Column(String(255), nullable=False)
    preference_value = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    __table_args__ = (
        Index("idx_user_prefs_user_key", "user_id", "preference_key", unique=True),
    )


class RuleModel(Base):
    """Rules database model"""

    __tablename__ = "rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_name = Column(String(255), nullable=False, unique=True, index=True)
    rule_definition = Column(Text, nullable=False)  # JSON string
    priority = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    __table_args__ = (Index("idx_rules_active_priority", "is_active", "priority"),)


class LearnedSolutionModel(Base):
    """Learned solutions database model"""

    __tablename__ = "learned_solutions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    error_type = Column(String(255), nullable=False, index=True)
    solution = Column(Text, nullable=False)
    success_rate: Column[float] = Column(Float, default=1.0, nullable=False)
    usage_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    last_used = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    __table_args__ = (
        Index("idx_learned_solutions_error_success", "error_type", "success_rate"),
    )


class MetricModel(Base):
    """Metrics database model"""

    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_name = Column(String(255), nullable=False, index=True)
    metric_value: Column[float] = Column(Float, nullable=False)
    metric_type = Column(String(50), nullable=False)  # "counter", "timer", "gauge"
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    context = Column(Text, nullable=True)  # JSON string

    __table_args__ = (
        Index("idx_metrics_name_timestamp", "metric_name", "timestamp"),
        Index("idx_metrics_type_timestamp", "metric_type", "timestamp"),
    )


class FeedbackEvent(Base):
    """Feedback events for self-improvement loop"""

    __tablename__ = "feedback_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    source = Column(String(100), nullable=False)  # "pytest", "pyright", "ruff"
    test_name = Column(String(255), nullable=True)
    error_sig = Column(Text, nullable=False)  # Error signature/pattern
    rule_applied = Column(String(100), nullable=True)
    outcome = Column(String(50), nullable=False)  # "success", "failure", "skipped"
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("idx_feedback_source_ts", "source", "ts"),
        Index("idx_feedback_rule_outcome", "rule_applied", "outcome"),
    )


class RuleDef(Base):
    """Rule definitions for auto-fixing"""

    __tablename__ = "rule_definitions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    version = Column(String(20), nullable=False, default="1.0")
    pattern_regex = Column(Text, nullable=False)
    fix_action = Column(String(100), nullable=False)
    severity = Column(
        String(20), nullable=False, default="medium"
    )  # low, medium, high, critical
    enabled = Column(Boolean, default=True, nullable=False)
    hits = Column(Integer, default=0, nullable=False)
    last_applied_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_rules_enabled_hits", "enabled", "hits"),
        Index("idx_rules_severity", "severity"),
    )


class MetricsDaily(Base):
    """Daily metrics for monitoring"""

    __tablename__ = "metrics_daily"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False, unique=True)
    pass_rate = Column(Float, nullable=False)
    fail_rate = Column(Float, nullable=False)
    coverage_overall = Column(Float, nullable=False)
    coverage_touched = Column(Float, nullable=False)
    mttr_min = Column(Float, nullable=True)  # Mean Time To Repair in minutes
    lint_errors = Column(Integer, default=0, nullable=False)
    pyright_errors = Column(Integer, default=0, nullable=False)

    __table_args__ = (Index("idx_metrics_daily_date", "date"),)


class PatchHistory(Base):
    """History of applied patches"""

    __tablename__ = "patch_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    files_changed = Column(Text, nullable=False)  # JSON list of files
    tests_failed_before = Column(Integer, nullable=False)
    tests_passed_after = Column(Integer, nullable=False)
    coverage_before = Column(Float, nullable=False)
    coverage_after = Column(Float, nullable=False)
    diff_hash = Column(String(64), nullable=False)  # SHA256 of diff

    __table_args__ = (
        Index("idx_patch_ts", "ts"),
        Index("idx_patch_hash", "diff_hash"),
    )


# Database engine and session factory
def create_database_engine(database_url: str = "sqlite:///agentdev.db"):
    """Create database engine"""
    return create_engine(database_url, echo=False)


def create_memory_database(db_path: str = ":memory:"):
    """Create database (in-memory or file-based)"""
    if db_path == ":memory:":
        engine = create_engine("sqlite:///:memory:", echo=False)
    elif db_path.startswith("sqlite:///"):
        # Already a full SQLite URL
        engine = create_engine(db_path, echo=False)
    else:
        # Just a file path, add sqlite:/// prefix
        # Ensure directory exists for file-based databases
        import os

        if not db_path.startswith(":memory:"):
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
        engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(engine)
    return engine


def get_session_factory(engine: Any):
    """Get session factory"""
    return sessionmaker(bind=engine)