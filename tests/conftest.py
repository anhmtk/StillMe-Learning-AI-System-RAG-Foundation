#!/usr/bin/env python3
"""
Standardized test infrastructure for AgentDev
"""

import os
import random
import tempfile

import numpy as np
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Quan trọng: import models để đăng ký vào metadata
from agent_dev.persistence.models import (
    Base,
)  # noqa: F401


@pytest.fixture(scope="session")
def db_url():
    """Create temporary SQLite database for test session"""
    fd, path = tempfile.mkstemp(prefix="agentdev_", suffix=".db")
    os.close(fd)
    return f"sqlite:///{path}"


@pytest.fixture(scope="session")
def engine(db_url):
    """Create SQLAlchemy engine with proper SQLite configuration"""
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False},  # Allow multiple threads
        pool_pre_ping=True,
        echo=False,  # Set to True for SQL debugging
    )
    Base.metadata.create_all(engine)
    yield engine
    # Cleanup
    try:
        Base.metadata.drop_all(engine)
        os.unlink(db_url.replace("sqlite:///", ""))
    except Exception:
        pass


@pytest.fixture()
def session(engine):
    """Create database session for each test"""
    with Session(engine, expire_on_commit=False) as s:
        yield s


@pytest.fixture(autouse=True)
def set_random_seeds():
    """Set deterministic random seeds for all tests"""
    random.seed(42)
    np.random.seed(42)


@pytest.fixture
def mock_agentdev(session):
    """Create AgentDev instance with real database session"""
    from agent_dev.core.agentdev import AgentDev
    from agent_dev.monitoring.metrics import MetricsCollector
    from agent_dev.persistence.repo import FeedbackRepo, MetricRepo, RuleRepo
    from agent_dev.rules.engine import RuleEngine

    # Create repos with real session
    feedback_repo = FeedbackRepo(session)
    rule_repo = RuleRepo(session)
    metric_repo = MetricRepo(session)

    # Create rule engine and monitor
    rule_engine = RuleEngine(rule_repo=rule_repo)
    monitor = MetricsCollector(metric_repo=metric_repo)

    # Create AgentDev with real components
    agent = AgentDev()
    agent.feedback_repo = feedback_repo
    agent.rule_repo = rule_repo
    agent.metric_repo = metric_repo
    agent.rule_engine = rule_engine
    agent.monitor = monitor

    return agent
