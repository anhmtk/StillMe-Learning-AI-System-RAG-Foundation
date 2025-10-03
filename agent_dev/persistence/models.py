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
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

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
        Index('idx_feedback_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_feedback_session', 'session_id'),
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
        Index('idx_user_prefs_user_key', 'user_id', 'preference_key', unique=True),
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
    
    __table_args__ = (
        Index('idx_rules_active_priority', 'is_active', 'priority'),
    )


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
        Index('idx_learned_solutions_error_success', 'error_type', 'success_rate'),
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
        Index('idx_metrics_name_timestamp', 'metric_name', 'timestamp'),
        Index('idx_metrics_type_timestamp', 'metric_type', 'timestamp'),
    )


# Database engine and session factory
def create_database_engine(database_url: str = "sqlite:///agentdev.db"):
    """Create database engine"""
    return create_engine(database_url, echo=False)


def create_memory_database():
    """Create in-memory database for testing"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    return engine


def get_session_factory(engine: Any):
    """Get session factory"""
    return sessionmaker(bind=engine)