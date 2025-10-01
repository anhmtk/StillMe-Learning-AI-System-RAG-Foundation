"""
📊 StillMe Metrics Queries
=========================

Hệ thống query và phân tích metrics data.
Cung cấp SQL templates và analytics functions cho dashboard.

Tính năng:
- SQL query templates
- Analytics functions
- Performance optimization
- Data aggregation
- Trend analysis

Author: StillMe AI Framework
Version: 1.0.0
Date: 2025-09-28
"""

import json
import logging
import sqlite3
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

class MetricsQueries:
    """
    Metrics query và analytics system
    
    Cung cấp SQL templates và analytics functions
    cho learning dashboard và reporting.
    """

    def __init__(self, db_path: str = "data/metrics/metrics.db"):
        self.db_path = db_path
        self._ensure_db_exists()

        logger.info(f"MetricsQueries initialized with db: {db_path}")

    def _ensure_db_exists(self):
        """Ensure database exists"""
        if not Path(self.db_path).exists():
            logger.warning(f"Database {self.db_path} does not exist")

    def get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        return sqlite3.connect(self.db_path)

    def get_daily_summary(self, date: Optional[str] = None) -> Dict[str, Any]:
        """Get daily summary metrics"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        conn = self.get_connection()
        cursor = conn.cursor()

        # Get runs for the date
        cursor.execute("""
            SELECT COUNT(*) as total_runs,
                   SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_runs,
                   AVG(CASE WHEN success = 1 THEN 1.0 ELSE 0.0 END) as success_rate
            FROM runs 
            WHERE DATE(started_at) = ?
        """, (date,))

        run_stats = cursor.fetchone()

        # Get metrics summary
        cursor.execute("""
            SELECT m.name, 
                   COUNT(*) as count,
                   AVG(m.value) as avg_value,
                   MIN(m.value) as min_value,
                   MAX(m.value) as max_value
            FROM metrics m
            JOIN runs r ON m.run_id = r.id
            WHERE DATE(r.started_at) = ?
            GROUP BY m.name
        """, (date,))

        metrics_summary = {}
        for row in cursor.fetchall():
            name, count, avg_val, min_val, max_val = row
            metrics_summary[name] = {
                'count': count,
                'avg': avg_val,
                'min': min_val,
                'max': max_val
            }

        # Get errors summary
        cursor.execute("""
            SELECT COUNT(*) as total_errors,
                   type,
                   COUNT(*) as count
            FROM errors e
            JOIN runs r ON e.run_id = r.id
            WHERE DATE(r.started_at) = ?
            GROUP BY type
        """, (date,))

        errors_summary = {}
        total_errors = 0
        for row in cursor.fetchall():
            count, error_type, _ = row
            errors_summary[error_type] = count
            total_errors += count

        conn.close()

        return {
            'date': date,
            'runs': {
                'total': run_stats[0] if run_stats[0] else 0,
                'successful': run_stats[1] if run_stats[1] else 0,
                'success_rate': run_stats[2] if run_stats[2] else 0.0
            },
            'metrics': metrics_summary,
            'errors': {
                'total': total_errors,
                'by_type': errors_summary
            }
        }

    def get_learning_curve(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get learning curve data"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DATE(r.started_at) as date,
                   AVG(CASE WHEN m.name = 'learning_pass_rate' THEN m.value ELSE NULL END) as pass_rate,
                   AVG(CASE WHEN m.name = 'learning_accuracy' THEN m.value ELSE NULL END) as accuracy,
                   AVG(CASE WHEN m.name = 'self_assessment_score' THEN m.value ELSE NULL END) as self_assessment
            FROM runs r
            LEFT JOIN metrics m ON r.id = m.run_id
            WHERE r.started_at >= date('now', '-{} days')
            GROUP BY DATE(r.started_at)
            ORDER BY date
        """.format(days))

        learning_curve = []
        for row in cursor.fetchall():
            date, pass_rate, accuracy, self_assessment = row
            learning_curve.append({
                'date': date,
                'pass_rate': pass_rate or 0.0,
                'accuracy': accuracy or 0.0,
                'self_assessment': self_assessment or 0.0
            })

        conn.close()
        return learning_curve

    def get_performance_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get performance metrics"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Latency metrics
        cursor.execute("""
            SELECT m.tag,
                   AVG(m.value) as avg_latency,
                   MIN(m.value) as min_latency,
                   MAX(m.value) as max_latency
            FROM metrics m
            JOIN runs r ON m.run_id = r.id
            WHERE m.name = 'latency_ms' 
            AND r.started_at >= date('now', '-{} days')
            GROUP BY m.tag
        """.format(days))

        latency_metrics = {}
        for row in cursor.fetchall():
            tag, avg_lat, min_lat, max_lat = row
            latency_metrics[tag] = {
                'avg': avg_lat,
                'min': min_lat,
                'max': max_lat
            }

        # Memory usage
        cursor.execute("""
            SELECT AVG(m.value) as avg_memory,
                   MAX(m.value) as max_memory
            FROM metrics m
            JOIN runs r ON m.run_id = r.id
            WHERE m.name = 'memory_usage_mb'
            AND r.started_at >= date('now', '-{} days')
        """.format(days))

        memory_stats = cursor.fetchone()

        # CPU usage
        cursor.execute("""
            SELECT AVG(m.value) as avg_cpu,
                   MAX(m.value) as max_cpu
            FROM metrics m
            JOIN runs r ON m.run_id = r.id
            WHERE m.name = 'cpu_usage_percent'
            AND r.started_at >= date('now', '-{} days')
        """.format(days))

        cpu_stats = cursor.fetchone()

        conn.close()

        return {
            'latency': latency_metrics,
            'memory': {
                'avg_mb': memory_stats[0] if memory_stats[0] else 0.0,
                'max_mb': memory_stats[1] if memory_stats[1] else 0.0
            },
            'cpu': {
                'avg_percent': cpu_stats[0] if cpu_stats[0] else 0.0,
                'max_percent': cpu_stats[1] if cpu_stats[1] else 0.0
            }
        }

    def get_ingest_volume(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get ingest volume by source"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DATE(r.started_at) as date,
                   m.tag as source,
                   SUM(m.value) as total_items
            FROM metrics m
            JOIN runs r ON m.run_id = r.id
            WHERE m.name = 'ingested_items'
            AND r.started_at >= date('now', '-{} days')
            GROUP BY DATE(r.started_at), m.tag
            ORDER BY date, source
        """.format(days))

        ingest_data = []
        for row in cursor.fetchall():
            date, source, total_items = row
            ingest_data.append({
                'date': date,
                'source': source,
                'total_items': total_items
            })

        conn.close()
        return ingest_data

    def get_token_usage(self, days: int = 7) -> Dict[str, Any]:
        """Get token usage statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DATE(r.started_at) as date,
                   SUM(m.value) as total_tokens
            FROM metrics m
            JOIN runs r ON m.run_id = r.id
            WHERE m.name = 'tokens_used'
            AND r.started_at >= date('now', '-{} days')
            GROUP BY DATE(r.started_at)
            ORDER BY date
        """.format(days))

        token_usage = []
        total_tokens = 0
        for row in cursor.fetchall():
            date, daily_tokens = row
            token_usage.append({
                'date': date,
                'tokens': daily_tokens
            })
            total_tokens += daily_tokens

        # Get average tokens per day
        avg_tokens_per_day = total_tokens / len(token_usage) if token_usage else 0

        conn.close()

        return {
            'daily_usage': token_usage,
            'total_tokens': total_tokens,
            'avg_tokens_per_day': avg_tokens_per_day
        }

    def get_error_analysis(self, days: int = 7) -> Dict[str, Any]:
        """Get error analysis"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT e.type,
                   COUNT(*) as count,
                   DATE(e.ts) as date
            FROM errors e
            JOIN runs r ON e.run_id = r.id
            WHERE r.started_at >= date('now', '-{} days')
            GROUP BY e.type, DATE(e.ts)
            ORDER BY date, count DESC
        """.format(days))

        error_data = {}
        for row in cursor.fetchall():
            error_type, count, date = row
            if error_type not in error_data:
                error_data[error_type] = []
            error_data[error_type].append({
                'date': date,
                'count': count
            })

        # Get total errors
        cursor.execute("""
            SELECT COUNT(*) as total_errors
            FROM errors e
            JOIN runs r ON e.run_id = r.id
            WHERE r.started_at >= date('now', '-{} days')
        """.format(days))

        total_errors = cursor.fetchone()[0]

        conn.close()

        return {
            'total_errors': total_errors,
            'by_type': error_data
        }

    def get_evolution_progress(self) -> Dict[str, Any]:
        """Get evolution stage progress"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT m.value as stage,
                   COUNT(*) as count,
                   DATE(r.started_at) as date
            FROM metrics m
            JOIN runs r ON m.run_id = r.id
            WHERE m.name = 'evolution_stage'
            GROUP BY m.value, DATE(r.started_at)
            ORDER BY date, stage
        """)

        evolution_data = {}
        for row in cursor.fetchall():
            stage, count, date = row
            if stage not in evolution_data:
                evolution_data[stage] = []
            evolution_data[stage].append({
                'date': date,
                'count': count
            })

        conn.close()

        return evolution_data

    def get_approval_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get approval workflow metrics"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT m.tag as content_type,
                   AVG(m.value) as avg_approval_rate
            FROM metrics m
            JOIN runs r ON m.run_id = r.id
            WHERE m.name = 'approval_rate'
            AND r.started_at >= date('now', '-{} days')
            GROUP BY m.tag
        """.format(days))

        approval_rates = {}
        for row in cursor.fetchall():
            content_type, avg_rate = row
            approval_rates[content_type] = avg_rate

        # Get quality and risk scores
        cursor.execute("""
            SELECT m.name,
                   AVG(m.value) as avg_score
            FROM metrics m
            JOIN runs r ON m.run_id = r.id
            WHERE m.name IN ('quality_score', 'risk_score')
            AND r.started_at >= date('now', '-{} days')
            GROUP BY m.name
        """.format(days))

        quality_metrics = {}
        for row in cursor.fetchall():
            metric_name, avg_score = row
            quality_metrics[metric_name] = avg_score

        conn.close()

        return {
            'approval_rates': approval_rates,
            'quality_metrics': quality_metrics
        }

    def get_recent_sessions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent learning sessions"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT r.session_id,
                   r.started_at,
                   r.ended_at,
                   r.success,
                   r.stage,
                   r.notes,
                   COUNT(m.id) as metrics_count,
                   COUNT(e.id) as errors_count
            FROM runs r
            LEFT JOIN metrics m ON r.id = m.run_id
            LEFT JOIN errors e ON r.id = e.run_id
            GROUP BY r.id
            ORDER BY r.started_at DESC
            LIMIT ?
        """, (limit,))

        sessions = []
        for row in cursor.fetchall():
            session_id, started_at, ended_at, success, stage, notes, metrics_count, errors_count = row
            sessions.append({
                'session_id': session_id,
                'started_at': started_at,
                'ended_at': ended_at,
                'success': bool(success),
                'stage': stage,
                'notes': notes,
                'metrics_count': metrics_count,
                'errors_count': errors_count
            })

        conn.close()
        return sessions

    def get_metric_trends(self, metric_name: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get trend data for a specific metric"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DATE(r.started_at) as date,
                   AVG(m.value) as avg_value,
                   MIN(m.value) as min_value,
                   MAX(m.value) as max_value,
                   COUNT(*) as sample_count
            FROM metrics m
            JOIN runs r ON m.run_id = r.id
            WHERE m.name = ?
            AND r.started_at >= date('now', '-{} days')
            GROUP BY DATE(r.started_at)
            ORDER BY date
        """.format(days), (metric_name,))

        trends = []
        for row in cursor.fetchall():
            date, avg_val, min_val, max_val, sample_count = row
            trends.append({
                'date': date,
                'avg': avg_val,
                'min': min_val,
                'max': max_val,
                'samples': sample_count
            })

        conn.close()
        return trends

    def export_metrics_csv(self, output_path: str, days: int = 30):
        """Export metrics to CSV"""
        import csv

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT r.session_id,
                   r.started_at,
                   r.stage,
                   r.success,
                   m.name,
                   m.value,
                   m.unit,
                   m.tag,
                   m.ts
            FROM runs r
            JOIN metrics m ON r.id = m.run_id
            WHERE r.started_at >= date('now', '-{} days')
            ORDER BY r.started_at, m.name
        """.format(days))

        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['session_id', 'started_at', 'stage', 'success', 'metric_name', 'value', 'unit', 'tag', 'timestamp'])

            for row in cursor.fetchall():
                writer.writerow(row)

        conn.close()
        logger.info(f"Exported metrics to {output_path}")

# Global instance
_metrics_queries_instance: Optional[MetricsQueries] = None

def get_metrics_queries() -> MetricsQueries:
    """Get global metrics queries instance"""
    global _metrics_queries_instance
    if _metrics_queries_instance is None:
        _metrics_queries_instance = MetricsQueries()
    return _metrics_queries_instance

def initialize_metrics_queries(db_path: Optional[str] = None) -> MetricsQueries:
    """Initialize global metrics queries with db path"""
    global _metrics_queries_instance
    _metrics_queries_instance = MetricsQueries(db_path)
    return _metrics_queries_instance
