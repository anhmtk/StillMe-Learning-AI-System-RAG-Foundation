"""
SQLAlchemy Models for StillMe Database
Unified models for PostgreSQL migration
"""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class KnowledgeItem(Base):
    """Knowledge items table (from knowledge_retention.db)"""
    __tablename__ = "knowledge_items"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=False)
    source = Column(String(500), nullable=False)
    knowledge_type = Column(String(100), nullable=False)
    confidence_score = Column(Float, default=0.0)
    retention_score = Column(Float, default=0.0)
    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(Text, default='{}')  # JSON string
    
    __table_args__ = (
        Index('idx_knowledge_source', 'source'),
        Index('idx_knowledge_type', 'knowledge_type'),
        Index('idx_knowledge_created', 'created_at'),
    )


class LearningSession(Base):
    """Learning sessions table (from knowledge_retention.db)"""
    __tablename__ = "learning_sessions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_type = Column(String(100), nullable=False)
    items_processed = Column(Integer, default=0)
    items_added = Column(Integer, default=0)
    items_filtered = Column(Integer, default=0)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(50), default='running')
    metadata = Column(Text, default='{}')  # JSON string
    
    __table_args__ = (
        Index('idx_session_type', 'session_type'),
        Index('idx_session_started', 'started_at'),
    )


class RSSFetchItem(Base):
    """RSS fetch items table (from rss_fetch_history.db)"""
    __tablename__ = "rss_fetch_items"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    cycle_id = Column(Integer, nullable=False)
    title = Column(String(500), nullable=False)
    source_url = Column(String(1000), nullable=False)
    link = Column(String(1000), nullable=True)
    summary = Column(Text, nullable=True)
    fetch_timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), nullable=False)  # Added to RAG, Filtered, Skipped, Failed, Error
    status_reason = Column(String(500), nullable=True)
    vector_id = Column(String(200), nullable=True)
    added_to_rag_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index('idx_rss_cycle', 'cycle_id'),
        Index('idx_rss_status', 'status'),
        Index('idx_rss_fetch_time', 'fetch_timestamp'),
        Index('idx_rss_link', 'link'),
    )


class RSSFetchCycle(Base):
    """RSS fetch cycles table (from rss_fetch_history.db)"""
    __tablename__ = "rss_fetch_cycles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    cycle_number = Column(Integer, nullable=False, unique=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(50), default='running')
    items_fetched = Column(Integer, default=0)
    items_added = Column(Integer, default=0)
    items_filtered = Column(Integer, default=0)
    
    __table_args__ = (
        Index('idx_cycle_number', 'cycle_number'),
        Index('idx_cycle_started', 'started_at'),
    )


class AccuracyScore(Base):
    """Accuracy scores table (from accuracy_scores.db)"""
    __tablename__ = "accuracy_scores"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    score = Column(Float, nullable=False)
    feedback = Column(Text, nullable=True)
    user_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_accuracy_score', 'score'),
        Index('idx_accuracy_created', 'created_at'),
        Index('idx_accuracy_user', 'user_id'),
    )


class ContinuumMemoryItem(Base):
    """Continuum memory items table (from continuum_memory.db)"""
    __tablename__ = "continuum_memory_items"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=False)
    tier = Column(String(10), nullable=False)  # L0, L1, L2, L3
    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(Text, default='{}')  # JSON string
    
    __table_args__ = (
        Index('idx_continuum_tier', 'tier'),
        Index('idx_continuum_accessed', 'last_accessed'),
    )

