"""
SQLAlchemy models for AgentDev persistence
=========================================

Database models using SQLAlchemy for persistent storage.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float, DateTime, 
    create_engine, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class FeedbackModel(Base):
    """Feedback database model"""
    __tablename__ = "feedback"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), nullable=False, index=True)
    feedback = Column(Text, nullable=False)
    session_id = Column(String(255), nullable=False, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    feedback_type = Column(String(50), nullable=False, default="neutral")
    context = Column(Text, nullable=True)  # JSON string
    
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
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    __table_args__ = (
        Index("idx_user_pref_key", "user_id", "preference_key", unique=True),
    )


class RuleModel(Base):
    """Rule database model"""
    __tablename__ = "rules"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_name = Column(String(255), nullable=False, unique=True, index=True)
    rule_definition = Column(Text, nullable=False)  # JSON string
    is_active = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    __table_args__ = (
        Index("idx_rule_active_priority", "is_active", "priority"),
    )


class LearnedSolutionModel(Base):
    """Learned solution database model"""
    __tablename__ = "learned_solutions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    error_type = Column(String(255), nullable=False, index=True)
    solution = Column(Text, nullable=False)
    success_rate = Column(Float, default=1.0, nullable=False)
    usage_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    last_used = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    __table_args__ = (
        Index("idx_learned_error_type", "error_type"),
        Index("idx_learned_success_rate", "success_rate"),
    )


class MetricModel(Base):
    """Metric database model"""
    __tablename__ = "metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_name = Column(String(255), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    metric_type = Column(String(50), nullable=False)  # "counter", "timer", "gauge"
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    context = Column(Text, nullable=True)  # JSON string
    
    __table_args__ = (
        Index("idx_metric_name_timestamp", "metric_name", "timestamp"),
        Index("idx_metric_type", "metric_type"),
    )


def create_database_engine(database_url: str = "sqlite:///agentdev.db"):
    """Create database engine and session factory"""
    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, SessionLocal


def create_memory_database():
    """Create in-memory SQLite database for testing"""
    return create_database_engine("sqlite:///:memory:")
