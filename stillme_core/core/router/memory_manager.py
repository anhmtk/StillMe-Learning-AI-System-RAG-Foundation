"""
Router Memory Manager - Decision History and Pattern Storage
==========================================================

This module provides memory management capabilities for the router system,
storing decision history, patterns, and enabling long-term learning.

Author: StillMe AI Framework
Version: 1.0.0
"""

import json
import logging
import sqlite3
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import StillMe core components
try:
    from ..observability.logger import get_logger
    from ..observability.metrics import MetricType, get_metrics_collector
    from ..observability.tracer import get_tracer
    from .intelligent_router import (  # type: ignore
        AgentType as RouterAgentType,
    )
    from .intelligent_router import (
        RoutingDecision as RouterRoutingDecision,
    )
    from .intelligent_router import (
        TaskComplexity as RouterTaskComplexity,
    )
    from .intelligent_router import (
        TaskType as RouterTaskType,
    )
except ImportError:
    # Fallback for standalone execution
    import sys

    sys.path.append(str(Path(__file__).parent.parent / "observability"))

try:
    from stillme_core.observability.logger import get_logger
except ImportError:
    pass

try:
    from stillme_core.observability.metrics import MetricType, get_metrics_collector
except ImportError:
    pass

try:
    from stillme_core.observability.tracer import get_tracer
except ImportError:
    pass

    # Mock the router imports for standalone execution
    class TaskComplexity(Enum):
        SIMPLE = "simple"
        MEDIUM = "medium"
        COMPLEX = "complex"
        CRITICAL = "critical"

    class TaskType(Enum):
        CODE_REVIEW = "code_review"
        BUG_FIX = "bug_fix"
        FEATURE_DEVELOPMENT = "feature_development"
        TESTING = "testing"
        DOCUMENTATION = "documentation"
        REFACTORING = "refactoring"
        DEPLOYMENT = "deployment"
        MONITORING = "monitoring"
        ANALYSIS = "analysis"
        GENERAL = "general"

    class AgentType(Enum):
        AGENTDEV = "agentdev"
        CODE_REVIEWER = "code_reviewer"
        TESTER = "tester"
        DOCUMENTER = "documenter"
        DEPLOYER = "deployer"
        ANALYST = "analyst"
        GENERAL = "general"

    class RoutingDecision:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)


# Initialize observability components safely
try:
    logger = get_logger(__name__)
    if logger is None:
        logger = logging.getLogger(__name__)
except (NameError, AttributeError, ImportError):
    logger = logging.getLogger(__name__)

try:
    metrics = get_metrics_collector()
    if metrics is None:
        metrics = None  # Will be handled in methods
except (NameError, AttributeError, ImportError):
    metrics = None

try:
    tracer = get_tracer()
    if tracer is None:
        tracer = None  # Will be handled in methods
except (NameError, AttributeError, ImportError):
    tracer = None


@dataclass
class RouterMemory:
    """Memory entry for router decisions"""

    memory_id: str
    timestamp: float
    request_hash: str
    task_type: str
    complexity: str
    selected_agent: str
    confidence: float
    success: bool
    duration: float
    user_satisfaction: Optional[float]
    context: Dict[str, Any]
    outcome: Dict[str, Any]


class RouterMemoryManager:
    """
    Router Memory Manager for storing and retrieving decision history

    This class provides memory management capabilities for the router system,
    enabling long-term learning and pattern recognition.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Router Memory Manager"""
        self.config = config or {}
        self.logger = logger if logger is not None else logging.getLogger(__name__)
        self.metrics = metrics
        self.tracer = tracer

        # Database configuration
        self.db_path = self.config.get("db_path", "router_memory.db")
        self.max_memories = self.config.get("max_memories", 10000)

        # Initialize database
        self._init_database()

        # Performance tracking
        self.memory_metrics = {
            "total_memories": 0,
            "successful_retrievals": 0,
            "failed_retrievals": 0,
            "avg_retrieval_time": 0.0,
        }

        self.logger.info("🧠 Router Memory Manager initialized")

    def _init_database(self):
        """Initialize the SQLite database for memory storage"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Create memories table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS router_memories (
                        memory_id TEXT PRIMARY KEY,
                        timestamp REAL NOT NULL,
                        request_hash TEXT NOT NULL,
                        task_type TEXT NOT NULL,
                        complexity TEXT NOT NULL,
                        selected_agent TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        success INTEGER NOT NULL,
                        duration REAL NOT NULL,
                        user_satisfaction REAL,
                        context TEXT NOT NULL,
                        outcome TEXT NOT NULL,
                        created_at REAL DEFAULT (julianday('now'))
                    )
                """
                )

                # Create indexes for faster queries
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_task_type ON router_memories(task_type)
                """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_complexity ON router_memories(complexity)
                """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_selected_agent ON router_memories(selected_agent)
                """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_timestamp ON router_memories(timestamp)
                """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_success ON router_memories(success)
                """
                )

                conn.commit()

        except Exception as e:
            self.logger.error(f"Error initializing database: {e}")
            raise

    async def store_memory(
        self,
        request_hash: str,
        task_type: TaskType,
        complexity: TaskComplexity,
        selected_agent: AgentType,
        confidence: float,
        success: bool,
        duration: float,
        context: Optional[Dict[str, Any]] = None,
        outcome: Optional[Dict[str, Any]] = None,
        user_satisfaction: Optional[float] = None,
    ) -> str:
        """Store a router decision in memory"""
        memory_id = f"memory_{int(time.time() * 1000)}"

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO router_memories (
                        memory_id, timestamp, request_hash, task_type, complexity,
                        selected_agent, confidence, success, duration, user_satisfaction,
                        context, outcome
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        memory_id,
                        time.time(),
                        request_hash,
                        task_type.value,
                        complexity.value,
                        selected_agent.value,
                        confidence,
                        1 if success else 0,
                        duration,
                        user_satisfaction,
                        json.dumps(context or {}),
                        json.dumps(outcome or {}),
                    ),
                )

                conn.commit()

            self.memory_metrics["total_memories"] += 1
            self.logger.debug(f"Stored memory: {memory_id}")

            # Cleanup old memories if needed
            await self._cleanup_old_memories()

            return memory_id

        except Exception as e:
            self.logger.error(f"Error storing memory: {e}")
            raise

    async def retrieve_similar_memories(
        self, task_type: TaskType, complexity: TaskComplexity, limit: int = 10
    ) -> List[RouterMemory]:
        """Retrieve similar memories based on task type and complexity"""
        start_time = time.time()

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT memory_id, timestamp, request_hash, task_type, complexity,
                           selected_agent, confidence, success, duration, user_satisfaction,
                           context, outcome
                    FROM router_memories
                    WHERE task_type = ? AND complexity = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """,
                    (task_type.value, complexity.value, limit),
                )

                rows = cursor.fetchall()

                memories = []
                for row in rows:
                    memory = RouterMemory(
                        memory_id=row[0],
                        timestamp=row[1],
                        request_hash=row[2],
                        task_type=row[3],
                        complexity=row[4],
                        selected_agent=row[5],
                        confidence=row[6],
                        success=bool(row[7]),
                        duration=row[8],
                        user_satisfaction=row[9],
                        context=json.loads(row[10]),
                        outcome=json.loads(row[11]),
                    )
                    memories.append(memory)

                retrieval_time = time.time() - start_time
                self.memory_metrics["successful_retrievals"] += 1

                # Update average retrieval time
                total_retrievals = (
                    self.memory_metrics["successful_retrievals"]
                    + self.memory_metrics["failed_retrievals"]
                )
                current_avg = self.memory_metrics["avg_retrieval_time"]
                self.memory_metrics["avg_retrieval_time"] = (
                    current_avg * (total_retrievals - 1) + retrieval_time
                ) / total_retrievals

                return memories

        except Exception as e:
            self.memory_metrics["failed_retrievals"] += 1
            self.logger.error(f"Error retrieving memories: {e}")
            return []

    async def get_agent_performance_history(
        self, agent_type: AgentType, days: int = 30
    ) -> Dict[str, Any]:
        """Get performance history for a specific agent"""
        cutoff_time = time.time() - (days * 24 * 60 * 60)

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT success, duration, confidence, user_satisfaction
                    FROM router_memories
                    WHERE selected_agent = ? AND timestamp >= ?
                """,
                    (agent_type.value, cutoff_time),
                )

                rows = cursor.fetchall()

                if not rows:
                    return {
                        "total_tasks": 0,
                        "success_rate": 0.0,
                        "avg_duration": 0.0,
                        "avg_confidence": 0.0,
                        "avg_satisfaction": 0.0,
                    }

                total_tasks = len(rows)
                successful_tasks = sum(1 for row in rows if row[0])
                success_rate = successful_tasks / total_tasks
                avg_duration = sum(row[1] for row in rows) / total_tasks
                avg_confidence = sum(row[2] for row in rows) / total_tasks

                # Calculate average satisfaction (only for non-null values)
                satisfaction_values = [row[3] for row in rows if row[3] is not None]
                avg_satisfaction = (
                    sum(satisfaction_values) / len(satisfaction_values)
                    if satisfaction_values
                    else 0.0
                )

                return {
                    "total_tasks": total_tasks,
                    "success_rate": success_rate,
                    "avg_duration": avg_duration,
                    "avg_confidence": avg_confidence,
                    "avg_satisfaction": avg_satisfaction,
                }

        except Exception as e:
            self.logger.error(f"Error getting agent performance history: {e}")
            return {}

    async def get_task_type_statistics(
        self, days: int = 30
    ) -> Dict[str, Dict[str, Any]]:
        """Get statistics for different task types"""
        cutoff_time = time.time() - (days * 24 * 60 * 60)

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT task_type, success, duration, confidence
                    FROM router_memories
                    WHERE timestamp >= ?
                """,
                    (cutoff_time,),
                )

                rows = cursor.fetchall()

                # Group by task type
                task_stats = {}
                for row in rows:
                    task_type = row[0]
                    if task_type not in task_stats:
                        task_stats[task_type] = {
                            "total_tasks": 0,
                            "successful_tasks": 0,
                            "total_duration": 0.0,
                            "total_confidence": 0.0,
                        }

                    stats = task_stats[task_type]
                    stats["total_tasks"] += 1
                    if row[1]:  # success
                        stats["successful_tasks"] += 1
                    stats["total_duration"] += row[2]
                    stats["total_confidence"] += row[3]

                # Calculate averages
                for task_type, stats in task_stats.items():
                    if stats["total_tasks"] > 0:
                        stats["success_rate"] = (
                            stats["successful_tasks"] / stats["total_tasks"]
                        )
                        stats["avg_duration"] = (
                            stats["total_duration"] / stats["total_tasks"]
                        )
                        stats["avg_confidence"] = (
                            stats["total_confidence"] / stats["total_tasks"]
                        )
                    else:
                        stats["success_rate"] = 0.0
                        stats["avg_duration"] = 0.0
                        stats["avg_confidence"] = 0.0

                return task_stats

        except Exception as e:
            self.logger.error(f"Error getting task type statistics: {e}")
            return {}

    async def get_learning_insights(self) -> Dict[str, Any]:
        """Get insights for learning and improvement"""
        insights = {
            "best_performing_agents": [],
            "worst_performing_agents": [],
            "most_common_task_types": [],
            "success_trends": {},
            "recommendations": [],
        }

        try:
            # Get agent performance
            agent_performance = {}
            for agent_type in AgentType:
                perf = await self.get_agent_performance_history(agent_type, 30)
                if perf["total_tasks"] > 0:
                    agent_performance[agent_type.value] = perf

            # Sort agents by performance
            sorted_agents = sorted(
                agent_performance.items(),
                key=lambda x: x[1]["success_rate"],
                reverse=True,
            )

            if sorted_agents:
                insights["best_performing_agents"] = sorted_agents[:3]
                insights["worst_performing_agents"] = sorted_agents[-3:]

            # Get task type statistics
            task_stats = await self.get_task_type_statistics(30)
            if task_stats:
                sorted_tasks = sorted(
                    task_stats.items(), key=lambda x: x[1]["total_tasks"], reverse=True
                )
                insights["most_common_task_types"] = sorted_tasks[:5]

            # Generate recommendations
            recommendations = []

            # Check for low-performing agents
            for agent, perf in agent_performance.items():
                if perf["success_rate"] < 0.5 and perf["total_tasks"] > 5:
                    recommendations.append(
                        f"Consider improving {agent} performance (success rate: {perf['success_rate']:.1%})"
                    )

            # Check for high-duration tasks
            for task_type, stats in task_stats.items():
                if (
                    stats["avg_duration"] > 300 and stats["total_tasks"] > 3
                ):  # > 5 minutes
                    recommendations.append(
                        f"Consider optimizing {task_type} tasks (avg duration: {stats['avg_duration']:.1f}s)"
                    )

            insights["recommendations"] = recommendations

            return insights

        except Exception as e:
            self.logger.error(f"Error getting learning insights: {e}")
            return insights

    async def _cleanup_old_memories(self):
        """Clean up old memories to maintain database size"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Count current memories
                cursor.execute("SELECT COUNT(*) FROM router_memories")
                count = cursor.fetchone()[0]

                if count > self.max_memories:
                    # Delete oldest memories
                    delete_count = count - self.max_memories
                    cursor.execute(
                        """
                        DELETE FROM router_memories
                        WHERE memory_id IN (
                            SELECT memory_id FROM router_memories
                            ORDER BY timestamp ASC
                            LIMIT ?
                        )
                    """,
                        (delete_count,),
                    )

                    conn.commit()
                    self.logger.info(f"Cleaned up {delete_count} old memories")

        except Exception as e:
            self.logger.error(f"Error cleaning up old memories: {e}")

    def get_memory_metrics(self) -> Dict[str, Any]:
        """Get current memory metrics"""
        return self.memory_metrics.copy()

    async def export_memory_data(
        self, days: int = 30, limit: int = 1000
    ) -> Dict[str, Any]:
        """Export memory data for analysis"""
        cutoff_time = time.time() - (days * 24 * 60 * 60)

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT memory_id, timestamp, request_hash, task_type, complexity,
                           selected_agent, confidence, success, duration, user_satisfaction,
                           context, outcome
                    FROM router_memories
                    WHERE timestamp >= ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """,
                    (cutoff_time, limit),
                )

                rows = cursor.fetchall()

                memories = []
                for row in rows:
                    memory = {
                        "memory_id": row[0],
                        "timestamp": row[1],
                        "request_hash": row[2],
                        "task_type": row[3],
                        "complexity": row[4],
                        "selected_agent": row[5],
                        "confidence": row[6],
                        "success": bool(row[7]),
                        "duration": row[8],
                        "user_satisfaction": row[9],
                        "context": json.loads(row[10]),
                        "outcome": json.loads(row[11]),
                    }
                    memories.append(memory)

                return {
                    "memories": memories,
                    "total_count": len(memories),
                    "export_timestamp": time.time(),
                    "days_covered": days,
                }

        except Exception as e:
            self.logger.error(f"Error exporting memory data: {e}")
            return {"memories": [], "total_count": 0, "error": str(e)}

    async def clear_old_memories(self, days: int = 90):
        """Clear memories older than specified days"""
        cutoff_time = time.time() - (days * 24 * 60 * 60)

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    DELETE FROM router_memories
                    WHERE timestamp < ?
                """,
                    (cutoff_time,),
                )

                deleted_count = cursor.rowcount
                conn.commit()

                self.logger.info(
                    f"Cleared {deleted_count} memories older than {days} days"
                )
                return deleted_count

        except Exception as e:
            self.logger.error(f"Error clearing old memories: {e}")
            return 0


# Global memory manager instance
_memory_manager_instance: Optional[RouterMemoryManager] = None


def get_router_memory_manager(
    config: Optional[Dict[str, Any]] = None,
) -> RouterMemoryManager:
    """Get or create global RouterMemoryManager instance"""
    global _memory_manager_instance

    if _memory_manager_instance is None:
        _memory_manager_instance = RouterMemoryManager(config)

    return _memory_manager_instance


# Convenience functions for common operations
async def store_router_memory(
    request_hash: str,
    task_type: TaskType,
    complexity: TaskComplexity,
    selected_agent: AgentType,
    confidence: float,
    success: bool,
    duration: float,
    context: Optional[Dict[str, Any]] = None,
    outcome: Optional[Dict[str, Any]] = None,
    user_satisfaction: Optional[float] = None,
) -> str:
    """Convenience function to store router memory"""
    manager = get_router_memory_manager()
    return await manager.store_memory(
        request_hash,
        task_type,
        complexity,
        selected_agent,
        confidence,
        success,
        duration,
        context,
        outcome,
        user_satisfaction,
    )


async def get_similar_memories(
    task_type: TaskType, complexity: TaskComplexity, limit: int = 10
) -> List[RouterMemory]:
    """Convenience function to get similar memories"""
    manager = get_router_memory_manager()
    return await manager.retrieve_similar_memories(task_type, complexity, limit)
