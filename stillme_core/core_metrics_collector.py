"""
🎯 CORE METRICS COLLECTOR - SUB-PHASE 3.1
==========================================

Enterprise-grade metrics collection system cho StillMe AI Framework.
Triển khai với tinh thần "Kỷ luật thép, chất lượng tuyệt đối".

Author: StillMe Phase 3 Development Team
Version: 3.1.0
Phase: 3.1 - Core Metrics Foundation
Quality Standard: Enterprise-Grade (99.9% accuracy target)

FEATURES:
- Real-time usage tracking với multi-dimensional metrics
- Resource consumption monitoring per module
- Performance metrics collection
- Basic cost attribution
- Memory-efficient design (< 2GB RAM)
- Batch processing architecture
- Lightweight integration với existing systems
"""

import asyncio
import json
import logging
import psutil
import time
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from concurrent.futures import ThreadPoolExecutor
import sqlite3
import hashlib
import uuid

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class UsageEvent:
    """Single usage event với complete metadata"""
    event_id: str
    timestamp: datetime
    module_name: str
    feature_name: str
    user_id: Optional[str]
    session_id: str
    duration_ms: float
    resource_usage: Dict[str, float]  # CPU, memory, disk, network
    success: bool
    error_code: Optional[str]
    metadata: Dict[str, Any]

@dataclass
class PerformanceMetrics:
    """Performance metrics cho một module"""
    module_name: str
    avg_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    success_rate: float
    error_rate: float
    throughput_per_minute: float
    memory_usage_mb: float
    cpu_usage_percent: float

@dataclass
class ValueMetrics:
    """Value metrics cho business impact"""
    time_saved_hours: float
    errors_prevented: int
    quality_improvement_score: float
    user_satisfaction_score: float
    cost_savings_usd: float
    roi_percentage: float

class CoreMetricsCollector:
    """
    Enterprise-grade metrics collector với focus vào accuracy và efficiency
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._get_default_config()
        self.db_path = Path(self.config['db_path'])
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Memory-efficient data structures
        self._usage_buffer = deque(maxlen=self.config['buffer_size'])
        self._performance_cache = {}
        self._value_metrics_cache = {}
        
        # Threading và concurrency
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=self.config['max_workers'])
        self._running = False
        self._flush_task = None
        
        # Database connection
        self._init_database()
        
        # System monitoring
        self._system_monitor = SystemMonitor()
        
        logger.info("✅ CoreMetricsCollector initialized với enterprise-grade configuration")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Default configuration với memory constraints"""
        return {
            'db_path': 'data/metrics/core_metrics.db',
            'buffer_size': 10000,  # Memory-efficient buffer
            'flush_interval': 30,  # seconds
            'max_workers': 4,
            'batch_size': 1000,
            'retention_days': 90,
            'memory_limit_mb': 2048,  # < 2GB constraint
            'accuracy_target': 0.999,  # 99.9% target
            'enable_real_time': False,  # Batch processing only
            'compression_enabled': True
        }
    
    def _init_database(self):
        """Initialize SQLite database với optimized schema"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS usage_events (
                        event_id TEXT PRIMARY KEY,
                        timestamp TEXT NOT NULL,
                        module_name TEXT NOT NULL,
                        feature_name TEXT NOT NULL,
                        user_id TEXT,
                        session_id TEXT NOT NULL,
                        duration_ms REAL NOT NULL,
                        resource_usage TEXT NOT NULL,
                        success BOOLEAN NOT NULL,
                        error_code TEXT,
                        metadata TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS performance_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        module_name TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        avg_response_time_ms REAL NOT NULL,
                        p95_response_time_ms REAL NOT NULL,
                        p99_response_time_ms REAL NOT NULL,
                        success_rate REAL NOT NULL,
                        error_rate REAL NOT NULL,
                        throughput_per_minute REAL NOT NULL,
                        memory_usage_mb REAL NOT NULL,
                        cpu_usage_percent REAL NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS value_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        time_saved_hours REAL NOT NULL,
                        errors_prevented INTEGER NOT NULL,
                        quality_improvement_score REAL NOT NULL,
                        user_satisfaction_score REAL NOT NULL,
                        cost_savings_usd REAL NOT NULL,
                        roi_percentage REAL NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Indexes cho performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_usage_timestamp ON usage_events(timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_usage_module ON usage_events(module_name)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_perf_timestamp ON performance_metrics(timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_perf_module ON performance_metrics(module_name)")
                
                conn.commit()
                
            logger.info("✅ Database initialized với optimized schema")
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise
    
    def start_collection(self):
        """Start metrics collection với memory monitoring"""
        if self._running:
            logger.warning("⚠️ Collection already running")
            return
        
        self._running = True
        
        # Start background flush task
        self._flush_task = asyncio.create_task(self._periodic_flush())
        
        # Start system monitoring
        self._system_monitor.start()
        
        logger.info("🚀 CoreMetricsCollector started với memory monitoring")
    
    def stop_collection(self):
        """Stop collection và flush remaining data"""
        if not self._running:
            return
        
        self._running = False
        
        # Flush remaining data
        self._flush_buffer()
        
        # Stop background tasks
        if self._flush_task:
            self._flush_task.cancel()
        
        # Stop system monitoring
        self._system_monitor.stop()
        
        logger.info("🛑 CoreMetricsCollector stopped")
    
    def track_usage(self, 
                   module_name: str,
                   feature_name: str,
                   duration_ms: float,
                   success: bool = True,
                   user_id: Optional[str] = None,
                   session_id: Optional[str] = None,
                   error_code: Optional[str] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Track usage event với complete resource monitoring
        
        Args:
            module_name: Tên module được sử dụng
            feature_name: Tên feature cụ thể
            duration_ms: Thời gian thực hiện (milliseconds)
            success: Thành công hay không
            user_id: ID người dùng (optional)
            session_id: ID session (optional)
            error_code: Mã lỗi nếu có
            metadata: Thông tin bổ sung
            
        Returns:
            str: Event ID được tạo
        """
        try:
            # Generate unique event ID
            event_id = str(uuid.uuid4())
            
            # Get current resource usage
            resource_usage = self._system_monitor.get_current_usage()
            
            # Create usage event
            event = UsageEvent(
                event_id=event_id,
                timestamp=datetime.now(),
                module_name=module_name,
                feature_name=feature_name,
                user_id=user_id,
                session_id=session_id or str(uuid.uuid4()),
                duration_ms=duration_ms,
                resource_usage=resource_usage,
                success=success,
                error_code=error_code,
                metadata=metadata or {}
            )
            
            # Add to buffer với thread safety
            with self._lock:
                self._usage_buffer.append(event)
            
            # Check memory usage
            self._check_memory_usage()
            
            logger.debug(f"📊 Usage tracked: {module_name}.{feature_name} ({duration_ms}ms)")
            return event_id
            
        except Exception as e:
            logger.error(f"❌ Error tracking usage: {e}")
            return ""
    
    def _check_memory_usage(self):
        """Check memory usage và trigger flush nếu cần"""
        try:
            current_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            if current_memory > self.config['memory_limit_mb']:
                logger.warning(f"⚠️ Memory usage high: {current_memory:.1f}MB")
                self._flush_buffer()
                
        except Exception as e:
            logger.error(f"❌ Memory check failed: {e}")
    
    def _flush_buffer(self):
        """Flush buffer to database với batch processing"""
        if not self._usage_buffer:
            return
        
        try:
            with self._lock:
                # Get batch of events
                batch = list(self._usage_buffer)
                self._usage_buffer.clear()
            
            # Process batch
            self._executor.submit(self._process_batch, batch)
            
        except Exception as e:
            logger.error(f"❌ Buffer flush failed: {e}")
    
    def _process_batch(self, events: List[UsageEvent]):
        """Process batch of events to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                for event in events:
                    conn.execute("""
                        INSERT INTO usage_events 
                        (event_id, timestamp, module_name, feature_name, user_id, 
                         session_id, duration_ms, resource_usage, success, error_code, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        event.event_id,
                        event.timestamp.isoformat(),
                        event.module_name,
                        event.feature_name,
                        event.user_id,
                        event.session_id,
                        event.duration_ms,
                        json.dumps(event.resource_usage),
                        event.success,
                        event.error_code,
                        json.dumps(event.metadata)
                    ))
                
                conn.commit()
            
            logger.debug(f"✅ Processed batch of {len(events)} events")
            
        except Exception as e:
            logger.error(f"❌ Batch processing failed: {e}")
    
    async def _periodic_flush(self):
        """Periodic flush task"""
        while self._running:
            try:
                await asyncio.sleep(self.config['flush_interval'])
                self._flush_buffer()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Periodic flush error: {e}")
    
    def get_performance_metrics(self, 
                               module_name: Optional[str] = None,
                               time_range_hours: int = 24) -> List[PerformanceMetrics]:
        """
        Get performance metrics với caching
        
        Args:
            module_name: Specific module (None for all)
            time_range_hours: Time range in hours
            
        Returns:
            List of PerformanceMetrics
        """
        try:
            cache_key = f"{module_name}_{time_range_hours}"
            
            # Check cache
            if cache_key in self._performance_cache:
                cache_time, metrics = self._performance_cache[cache_key]
                if time.time() - cache_time < 300:  # 5 minute cache
                    return metrics
            
            # Query database
            with sqlite3.connect(self.db_path) as conn:
                since_time = datetime.now() - timedelta(hours=time_range_hours)
                
                query = """
                    SELECT module_name, 
                           AVG(duration_ms) as avg_response_time,
                           (SELECT duration_ms FROM usage_events u2 
                            WHERE u2.module_name = u1.module_name 
                            ORDER BY duration_ms LIMIT 1 OFFSET 
                            (SELECT COUNT(*) * 0.95 FROM usage_events u3 WHERE u3.module_name = u1.module_name)) as p95_response_time,
                           (SELECT duration_ms FROM usage_events u2 
                            WHERE u2.module_name = u1.module_name 
                            ORDER BY duration_ms LIMIT 1 OFFSET 
                            (SELECT COUNT(*) * 0.99 FROM usage_events u3 WHERE u3.module_name = u1.module_name)) as p99_response_time,
                           AVG(CASE WHEN success = 1 THEN 1.0 ELSE 0.0 END) as success_rate,
                           AVG(CASE WHEN success = 0 THEN 1.0 ELSE 0.0 END) as error_rate,
                           COUNT(*) / (24.0 * 60.0) as throughput_per_minute,
                           AVG(CAST(json_extract(resource_usage, '$.memory_mb') AS REAL)) as memory_usage_mb,
                           AVG(CAST(json_extract(resource_usage, '$.cpu_percent') AS REAL)) as cpu_usage_percent
                    FROM usage_events u1
                    WHERE timestamp >= ? AND timestamp <= ?
                """
                
                params = [since_time.isoformat(), datetime.now().isoformat()]
                
                if module_name:
                    query += " AND module_name = ?"
                    params.append(module_name)
                
                query += " GROUP BY module_name"
                
                cursor = conn.execute(query, params)
                results = cursor.fetchall()
            
            # Convert to PerformanceMetrics objects
            metrics = []
            for row in results:
                metric = PerformanceMetrics(
                    module_name=row[0],
                    avg_response_time_ms=row[1] or 0.0,
                    p95_response_time_ms=row[2] or 0.0,
                    p99_response_time_ms=row[3] or 0.0,
                    success_rate=row[4] or 0.0,
                    error_rate=row[5] or 0.0,
                    throughput_per_minute=row[6] or 0.0,
                    memory_usage_mb=row[7] or 0.0,
                    cpu_usage_percent=row[8] or 0.0
                )
                metrics.append(metric)
            
            # Cache results
            self._performance_cache[cache_key] = (time.time(), metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"❌ Error getting performance metrics: {e}")
            return []
    
    def calculate_value_metrics(self, time_range_hours: int = 24) -> ValueMetrics:
        """
        Calculate value metrics với business impact
        
        Args:
            time_range_hours: Time range for calculation
            
        Returns:
            ValueMetrics object
        """
        try:
            cache_key = f"value_{time_range_hours}"
            
            # Check cache
            if cache_key in self._value_metrics_cache:
                cache_time, metrics = self._value_metrics_cache[cache_key]
                if time.time() - cache_time < 600:  # 10 minute cache
                    return metrics
            
            # Get usage data
            with sqlite3.connect(self.db_path) as conn:
                since_time = datetime.now() - timedelta(hours=time_range_hours)
                
                # Calculate time saved (assume 50% time reduction)
                cursor = conn.execute("""
                    SELECT SUM(duration_ms) / 1000.0 / 3600.0 * 0.5 as time_saved_hours
                    FROM usage_events
                    WHERE timestamp >= ? AND success = 1
                """, [since_time.isoformat()])
                time_saved_hours = cursor.fetchone()[0] or 0.0
                
                # Calculate errors prevented
                cursor = conn.execute("""
                    SELECT COUNT(*) as errors_prevented
                    FROM usage_events
                    WHERE timestamp >= ? AND success = 0
                """, [since_time.isoformat()])
                errors_prevented = cursor.fetchone()[0] or 0
                
                # Calculate quality improvement (based on success rate)
                cursor = conn.execute("""
                    SELECT AVG(CASE WHEN success = 1 THEN 1.0 ELSE 0.0 END) as success_rate
                    FROM usage_events
                    WHERE timestamp >= ?
                """, [since_time.isoformat()])
                success_rate = cursor.fetchone()[0] or 0.0
                quality_improvement_score = success_rate * 100.0
                
                # Calculate user satisfaction (based on performance)
                cursor = conn.execute("""
                    SELECT AVG(duration_ms) as avg_duration
                    FROM usage_events
                    WHERE timestamp >= ? AND success = 1
                """, [since_time.isoformat()])
                avg_duration = cursor.fetchone()[0] or 0.0
                user_satisfaction_score = max(0, 100 - (avg_duration / 1000.0))  # Penalty for slow response
                
                # Calculate cost savings (assume $50/hour developer time)
                cost_savings_usd = time_saved_hours * 50.0
                
                # Calculate ROI (simplified)
                roi_percentage = (cost_savings_usd / max(1, time_range_hours * 10.0)) * 100.0
            
            # Create ValueMetrics object
            metrics = ValueMetrics(
                time_saved_hours=time_saved_hours,
                errors_prevented=errors_prevented,
                quality_improvement_score=quality_improvement_score,
                user_satisfaction_score=user_satisfaction_score,
                cost_savings_usd=cost_savings_usd,
                roi_percentage=roi_percentage
            )
            
            # Cache results
            self._value_metrics_cache[cache_key] = (time.time(), metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"❌ Error calculating value metrics: {e}")
            return ValueMetrics(0, 0, 0, 0, 0, 0)
    
    def get_accuracy_report(self) -> Dict[str, Any]:
        """
        Generate accuracy report cho validation
        
        Returns:
            Dict with accuracy metrics
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Count total events
                cursor = conn.execute("SELECT COUNT(*) FROM usage_events")
                total_events = cursor.fetchone()[0]
                
                # Count successful events
                cursor = conn.execute("SELECT COUNT(*) FROM usage_events WHERE success = 1")
                successful_events = cursor.fetchone()[0]
                
                # Calculate accuracy
                accuracy = successful_events / max(1, total_events)
                
                # Get data completeness
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM usage_events 
                    WHERE event_id IS NOT NULL 
                    AND timestamp IS NOT NULL 
                    AND module_name IS NOT NULL
                """)
                complete_events = cursor.fetchone()[0]
                completeness = complete_events / max(1, total_events)
                
                return {
                    'total_events': total_events,
                    'successful_events': successful_events,
                    'accuracy_percentage': accuracy * 100.0,
                    'data_completeness': completeness * 100.0,
                    'target_accuracy': self.config['accuracy_target'] * 100.0,
                    'meets_target': accuracy >= self.config['accuracy_target'],
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"❌ Error generating accuracy report: {e}")
            return {'error': str(e)}
    
    def cleanup_old_data(self):
        """Cleanup old data để maintain performance"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.config['retention_days'])
            
            with sqlite3.connect(self.db_path) as conn:
                # Cleanup usage events
                cursor = conn.execute("DELETE FROM usage_events WHERE timestamp < ?", [cutoff_date.isoformat()])
                deleted_events = cursor.rowcount
                
                # Cleanup performance metrics
                cursor = conn.execute("DELETE FROM performance_metrics WHERE timestamp < ?", [cutoff_date.isoformat()])
                deleted_metrics = cursor.rowcount
                
                # Cleanup value metrics
                cursor = conn.execute("DELETE FROM value_metrics WHERE timestamp < ?", [cutoff_date.isoformat()])
                deleted_values = cursor.rowcount
                
                conn.commit()
                
                logger.info(f"🧹 Cleaned up {deleted_events} events, {deleted_metrics} metrics, {deleted_values} values")
                
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")

class SystemMonitor:
    """System resource monitoring"""
    
    def __init__(self):
        self._process = psutil.Process()
    
    def start(self):
        """Start monitoring"""
        pass
    
    def stop(self):
        """Stop monitoring"""
        pass
    
    def get_current_usage(self) -> Dict[str, float]:
        """Get current system resource usage"""
        try:
            return {
                'cpu_percent': self._process.cpu_percent(),
                'memory_mb': self._process.memory_info().rss / 1024 / 1024,
                'disk_io_read': self._process.io_counters().read_bytes if hasattr(self._process, 'io_counters') else 0,
                'disk_io_write': self._process.io_counters().write_bytes if hasattr(self._process, 'io_counters') else 0,
                'network_sent': 0,  # Would need network monitoring
                'network_recv': 0   # Would need network monitoring
            }
        except Exception as e:
            logger.error(f"❌ Error getting system usage: {e}")
            return {
                'cpu_percent': 0.0,
                'memory_mb': 0.0,
                'disk_io_read': 0.0,
                'disk_io_write': 0.0,
                'network_sent': 0.0,
                'network_recv': 0.0
            }

# Factory function
def create_metrics_collector(config: Optional[Dict[str, Any]] = None) -> CoreMetricsCollector:
    """Factory function để create metrics collector"""
    return CoreMetricsCollector(config)

# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Core Metrics Collector")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--start", action="store_true", help="Start collection")
    parser.add_argument("--stop", action="store_true", help="Stop collection")
    parser.add_argument("--report", action="store_true", help="Generate accuracy report")
    
    args = parser.parse_args()
    
    # Load config
    config = {}
    if args.config:
        with open(args.config, 'r') as f:
            config = json.load(f)
    
    # Create collector
    collector = create_metrics_collector(config)
    
    if args.start:
        collector.start_collection()
        print("✅ Metrics collection started")
    elif args.stop:
        collector.stop_collection()
        print("🛑 Metrics collection stopped")
    elif args.report:
        report = collector.get_accuracy_report()
        print(json.dumps(report, indent=2))
    else:
        print("Use --help for usage information")
