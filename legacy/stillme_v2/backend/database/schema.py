"""
SQLAlchemy database schema for StillMe V2
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Proposal(Base):
    """Proposals table - what AI wants to learn"""

    __tablename__ = "proposals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    proposal_id = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    source_url = Column(String(1000))
    source_name = Column(String(200))
    category = Column(String(100), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="pending", index=True)
    quality_score = Column(Float, nullable=False, default=0.0)
    relevance_score = Column(Float, nullable=False, default=0.0)
    novelty_score = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    learned_at = Column(DateTime)


class LearningSession(Base):
    """Learning sessions table - daily learning records"""

    __tablename__ = "learning_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    date = Column(String(20), nullable=False, index=True)
    proposals_learned = Column(Integer, nullable=False, default=0)
    accuracy_delta = Column(Float, nullable=False, default=0.0)
    evolution_stage = Column(String(50), nullable=False)
    duration_minutes = Column(Integer, nullable=False, default=0)
    success = Column(Boolean, nullable=False, default=False)
    notes = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class DailyLearningStats(Base):
    """Daily learning statistics for historical analysis"""

    __tablename__ = "daily_learning_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(20), nullable=False, unique=True, index=True)  # YYYY-MM-DD format
    
    # Content metrics
    content_fetched = Column(Integer, nullable=False, default=0)
    content_sources = Column(Integer, nullable=False, default=0)
    
    # Learning metrics
    proposals_generated = Column(Integer, nullable=False, default=0)
    proposals_approved = Column(Integer, nullable=False, default=0)
    proposals_pending = Column(Integer, nullable=False, default=0)
    
    # Quality metrics
    avg_quality_score = Column(Float, nullable=False, default=0.0)
    avg_relevance_score = Column(Float, nullable=False, default=0.0)
    avg_novelty_score = Column(Float, nullable=False, default=0.0)
    
    # Learning efficiency
    learning_efficiency = Column(Float, nullable=False, default=0.0)  # proposals/content * 100
    
    # Evolution metrics
    evolution_stage = Column(String(50), nullable=False, default="infant")
    knowledge_items_added = Column(Integer, nullable=False, default=0)
    memory_items_added = Column(Integer, nullable=False, default=0)
    
    # Session metrics
    learning_sessions_count = Column(Integer, nullable=False, default=0)
    successful_sessions = Column(Integer, nullable=False, default=0)
    total_duration_minutes = Column(Integer, nullable=False, default=0)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)


class KnowledgeBase(Base):
    """Knowledge base table - what AI learned"""

    __tablename__ = "knowledge_base"

    id = Column(Integer, primary_key=True, autoincrement=True)
    knowledge_id = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String(500))
    category = Column(String(100), nullable=False, index=True)
    embedding = Column(Text)
    confidence = Column(Float, nullable=False, default=0.0)
    learned_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_accessed = Column(DateTime)
    access_count = Column(Integer, nullable=False, default=0)


class ChatSession(Base):
    """Chat sessions table - conversation history"""

    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_message_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    message_count = Column(Integer, nullable=False, default=0)


class ChatMessage(Base):
    """Chat messages table"""

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(String(100), unique=True, nullable=False, index=True)
    session_id = Column(String(100), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    model = Column(String(100))
    tokens_used = Column(Integer)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


def init_database(db_url: str = "sqlite:///data/stillme_v2.db"):
    """Initialize database and create all tables"""
    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    return engine, SessionLocal


def get_db_session():
    """Get database session"""
    import os
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_engine
    
    # Create database connection directly
    db_url = "sqlite:///data/stillme_v2.db"
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_direct_db_session():
    """Get database session directly (not generator)"""
    import os
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_engine
    
    # Create database connection directly
    db_url = "sqlite:///data/stillme_v2.db"
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    return SessionLocal()