"""
🤖 StillMe Learning Automation Service
=====================================

Background service để chạy learning automation với scheduler.
Tích hợp scheduler, resource monitoring, và learning system.

Tính năng:
- Background service với asyncio
- Tích hợp với LearningScheduler
- Resource monitoring và health checks
- Graceful shutdown và error recovery
- Service status và health endpoints

Author: StillMe AI Framework
Version: 2.0.0
Date: 2025-09-28
"""

import asyncio
import logging
import signal
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path
import json

from .scheduler import LearningScheduler, SchedulerConfig, get_learning_scheduler
from .evolutionary_learning_system import EvolutionaryLearningSystem, EvolutionaryConfig
from ..monitoring.resource_monitor import ResourceMonitor, ResourceThresholds, get_resource_monitor
from ..monitoring.performance_analyzer import PerformanceAnalyzer, PerformanceMetrics, get_performance_analyzer

logger = logging.getLogger(__name__)

@dataclass
class AutomationServiceConfig:
    """Cấu hình automation service"""
    enabled: bool = True
    scheduler_config: SchedulerConfig = None
    learning_config: EvolutionaryConfig = None
    resource_thresholds: ResourceThresholds = None
    health_check_interval: int = 60  # seconds
    max_restart_attempts: int = 3
    restart_delay: int = 30  # seconds
    log_level: str = "INFO"
    enable_metrics: bool = True
    metrics_export_interval: int = 3600  # 1 hour
    enable_resource_monitoring: bool = True
    enable_performance_analysis: bool = True
    resource_monitoring_interval: int = 10  # seconds
    performance_analysis_interval: int = 300  # 5 minutes

@dataclass
class ServiceStatus:
    """Trạng thái service"""
    running: bool = False
    start_time: Optional[datetime] = None
    last_health_check: Optional[datetime] = None
    restart_count: int = 0
    last_error: Optional[str] = None
    uptime_seconds: int = 0

class LearningAutomationService:
    """
    Background service cho learning automation
    """
    
    def __init__(self, config: AutomationServiceConfig = None):
        self.config = config or AutomationServiceConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.scheduler: Optional[LearningScheduler] = None
        self.learning_system: Optional[EvolutionaryLearningSystem] = None
        self.resource_monitor: Optional[ResourceMonitor] = None
        self.performance_analyzer: Optional[PerformanceAnalyzer] = None
        
        # Service state
        self.status = ServiceStatus()
        self.shutdown_event = asyncio.Event()
        self.health_check_task: Optional[asyncio.Task] = None
        self.metrics_task: Optional[asyncio.Task] = None
        
        # Statistics
        self.stats = {
            'service_start_time': None,
            'total_training_sessions': 0,
            'successful_sessions': 0,
            'failed_sessions': 0,
            'skipped_sessions': 0,
            'last_training_time': None,
            'next_training_time': None,
            'average_session_duration': 0.0,
            'resource_checks_passed': 0,
            'resource_checks_failed': 0
        }
        
        # Setup logging
        self._setup_logging()
        
        # Setup signal handlers
        self._setup_signal_handlers()
    
    def _setup_logging(self):
        """Setup logging configuration"""
        log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Setup logger
        self.logger.setLevel(log_level)
        
        # Add console handler if not already present
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
    
    def _setup_signal_handlers(self):
        """Setup signal handlers cho graceful shutdown"""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            asyncio.create_task(self.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def initialize(self) -> bool:
        """Khởi tạo service"""
        try:
            self.logger.info("Initializing Learning Automation Service...")
            
            # Initialize learning system
            self.learning_system = EvolutionaryLearningSystem(
                self.config.learning_config or EvolutionaryConfig()
            )
            self.logger.info("Learning system initialized")
            
            # Initialize scheduler
            self.scheduler = get_learning_scheduler(
                self.config.scheduler_config or SchedulerConfig()
            )
            await self.scheduler.initialize()
            self.logger.info("Scheduler initialized")
            
            # Initialize resource monitoring
            if self.config.enable_resource_monitoring:
                self.resource_monitor = get_resource_monitor(
                    self.config.resource_thresholds or ResourceThresholds()
                )
                await self.resource_monitor.start_monitoring(
                    self.config.resource_monitoring_interval
                )
                self.logger.info("Resource monitoring initialized")
            
            # Initialize performance analysis
            if self.config.enable_performance_analysis:
                self.performance_analyzer = get_performance_analyzer()
                await self.performance_analyzer.start_analysis(
                    self.config.performance_analysis_interval
                )
                self.logger.info("Performance analysis initialized")
            
            # Schedule daily training if enabled
            if self.config.scheduler_config and self.config.scheduler_config.enabled:
                success = await self.scheduler.schedule_daily_training(
                    self._run_training_session
                )
                if success:
                    self.logger.info("Daily training scheduled")
                else:
                    self.logger.error("Failed to schedule daily training")
                    return False
            
            self.logger.info("Learning Automation Service initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize service: {e}")
            return False
    
    async def start(self) -> bool:
        """Bắt đầu service"""
        try:
            if not await self.initialize():
                return False
            
            self.logger.info("Starting Learning Automation Service...")
            
            # Start scheduler
            if self.scheduler:
                await self.scheduler.start()
            
            # Start background tasks
            self.health_check_task = asyncio.create_task(self._health_check_loop())
            
            if self.config.enable_metrics:
                self.metrics_task = asyncio.create_task(self._metrics_export_loop())
            
            # Update status
            self.status.running = True
            self.status.start_time = datetime.now()
            self.stats['service_start_time'] = self.status.start_time
            
            self.logger.info("Learning Automation Service started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start service: {e}")
            self.status.last_error = str(e)
            return False
    
    async def stop(self) -> bool:
        """Dừng service"""
        try:
            self.logger.info("Stopping Learning Automation Service...")
            
            # Signal shutdown
            self.shutdown_event.set()
            
            # Stop background tasks
            if self.health_check_task:
                self.health_check_task.cancel()
                try:
                    await self.health_check_task
                except asyncio.CancelledError:
                    pass
            
            if self.metrics_task:
                self.metrics_task.cancel()
                try:
                    await self.metrics_task
                except asyncio.CancelledError:
                    pass
            
            # Stop scheduler
            if self.scheduler:
                await self.scheduler.stop()
            
            # Stop resource monitoring
            if self.resource_monitor:
                await self.resource_monitor.stop_monitoring()
            
            # Stop performance analysis
            if self.performance_analyzer:
                await self.performance_analyzer.stop_analysis()
            
            # Update status
            self.status.running = False
            
            self.logger.info("Learning Automation Service stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop service: {e}")
            return False
    
    async def shutdown(self):
        """Graceful shutdown"""
        self.logger.info("Initiating graceful shutdown...")
        
        # Stop service
        await self.stop()
        
        # Export final metrics
        if self.config.enable_metrics:
            await self._export_metrics()
        
        self.logger.info("Graceful shutdown completed")
    
    async def _run_training_session(self, **kwargs) -> Dict[str, Any]:
        """
        Chạy training session với error handling và metrics
        """
        start_time = time.time()
        session_id = f"auto_training_{int(start_time)}"
        
        try:
            self.logger.info(f"Starting automated training session: {session_id}")
            
            if not self.learning_system:
                raise RuntimeError("Learning system not initialized")
            
            # Check resource availability
            if self.resource_monitor:
                can_start, reason = self.resource_monitor.can_start_learning_session()
                if not can_start:
                    self.logger.warning(f"Cannot start training session: {reason}")
                    return {
                        'session_id': session_id,
                        'status': 'skipped',
                        'reason': reason,
                        'duration': time.time() - start_time
                    }
                
                # Start tracking session
                self.resource_monitor.start_learning_session(session_id)
            
            # Run training session
            session = await self.learning_system.daily_learning_session()
            
            # Update statistics
            duration = time.time() - start_time
            self.stats['total_training_sessions'] += 1
            self.stats['successful_sessions'] += 1
            self.stats['last_training_time'] = datetime.now()
            self.stats['average_session_duration'] = (
                (self.stats['average_session_duration'] * (self.stats['total_training_sessions'] - 1) + duration) /
                self.stats['total_training_sessions']
            )
            
            # Record performance metrics
            if self.performance_analyzer:
                # Get current resource metrics
                resource_metrics = None
                if self.resource_monitor:
                    resource_metrics = self.resource_monitor.get_current_metrics()
                
                performance_metrics = PerformanceMetrics(
                    timestamp=datetime.now(),
                    session_id=session_id,
                    learning_stage=getattr(session, 'stage', 'unknown'),
                    response_time_ms=duration * 1000,
                    memory_usage_mb=resource_metrics.memory_used_mb if resource_metrics else 0,
                    cpu_usage_percent=resource_metrics.cpu_percent if resource_metrics else 0,
                    tokens_consumed=getattr(session, 'tokens_used', 0),
                    accuracy_score=getattr(session, 'accuracy', 0.8),
                    learning_rate=getattr(session, 'learning_rate', 0.1),
                    convergence_rate=getattr(session, 'convergence_rate', 0.5),
                    error_rate=getattr(session, 'error_rate', 0.1),
                    throughput_items_per_second=getattr(session, 'throughput', 1.0),
                    efficiency_score=getattr(session, 'efficiency', 0.7)
                )
                
                self.performance_analyzer.add_performance_metrics(performance_metrics)
            
            # End session tracking
            if self.resource_monitor:
                self.resource_monitor.end_learning_session(session_id)
            
            self.logger.info(f"Training session completed successfully in {duration:.2f} seconds")
            
            return {
                'session_id': session_id,
                'status': 'success',
                'duration': duration,
                'session': asdict(session) if hasattr(session, '__dataclass_fields__') else str(session)
            }
            
        except Exception as e:
            self.logger.error(f"Training session failed: {e}")
            
            # Update statistics
            self.stats['total_training_sessions'] += 1
            self.stats['failed_sessions'] += 1
            self.status.last_error = str(e)
            
            # End session tracking on failure
            if self.resource_monitor:
                self.resource_monitor.end_learning_session(session_id)
            
            return {
                'session_id': session_id,
                'status': 'failed',
                'error': str(e),
                'duration': time.time() - start_time
            }
    
    async def _health_check_loop(self):
        """Background health check loop"""
        while not self.shutdown_event.is_set():
            try:
                await self._perform_health_check()
                self.status.last_health_check = datetime.now()
                
                # Update uptime
                if self.status.start_time:
                    self.status.uptime_seconds = int(
                        (datetime.now() - self.status.start_time).total_seconds()
                    )
                
                await asyncio.sleep(self.config.health_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health check failed: {e}")
                await asyncio.sleep(self.config.health_check_interval)
    
    async def _perform_health_check(self):
        """Thực hiện health check"""
        try:
            # Check scheduler status
            if self.scheduler:
                scheduler_status = self.scheduler.get_status()
                if not scheduler_status.get('running', False):
                    self.logger.warning("Scheduler is not running")
            
            # Check learning system
            if self.learning_system:
                # Basic health check - just ensure it's initialized
                if not hasattr(self.learning_system, 'current_stage'):
                    self.logger.warning("Learning system appears unhealthy")
            
            # Check resource usage (basic)
            try:
                import psutil
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                
                if cpu_percent > 90:
                    self.logger.warning(f"High CPU usage: {cpu_percent:.1f}%")
                
                if memory.percent > 90:
                    self.logger.warning(f"High memory usage: {memory.percent:.1f}%")
                    
            except ImportError:
                pass  # psutil not available
            
            self.logger.debug("Health check passed")
            
        except Exception as e:
            self.logger.error(f"Health check error: {e}")
            raise
    
    async def _metrics_export_loop(self):
        """Background metrics export loop"""
        while not self.shutdown_event.is_set():
            try:
                await self._export_metrics()
                await asyncio.sleep(self.config.metrics_export_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Metrics export failed: {e}")
                await asyncio.sleep(self.config.metrics_export_interval)
    
    async def _export_metrics(self):
        """Export metrics to file"""
        try:
            metrics_data = {
                'timestamp': datetime.now().isoformat(),
                'service_status': asdict(self.status),
                'statistics': self.stats,
                'scheduler_status': self.scheduler.get_status() if self.scheduler else None,
                'learning_system_status': self.learning_system.get_learning_status() if self.learning_system else None
            }
            
            # Create metrics directory if not exists
            metrics_dir = Path("artifacts/metrics")
            metrics_dir.mkdir(parents=True, exist_ok=True)
            
            # Export to JSON
            metrics_file = metrics_dir / f"automation_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(metrics_file, 'w', encoding='utf-8') as f:
                json.dump(metrics_data, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.debug(f"Metrics exported to {metrics_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to export metrics: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Lấy trạng thái service"""
        return {
            'service': asdict(self.status),
            'statistics': self.stats,
            'scheduler': self.scheduler.get_status() if self.scheduler else None,
            'learning_system': self.learning_system.get_learning_status() if self.learning_system else None,
            'config': asdict(self.config)
        }
    
    async def restart(self) -> bool:
        """Restart service"""
        self.logger.info("Restarting service...")
        
        # Stop current service
        await self.stop()
        
        # Wait before restart
        await asyncio.sleep(self.config.restart_delay)
        
        # Update restart count
        self.status.restart_count += 1
        
        # Start service again
        return await self.start()

# Global service instance
_service_instance: Optional[LearningAutomationService] = None

def get_automation_service(config: AutomationServiceConfig = None) -> LearningAutomationService:
    """Get global automation service instance"""
    global _service_instance
    if _service_instance is None:
        _service_instance = LearningAutomationService(config)
    return _service_instance

async def run_automation_service(config: AutomationServiceConfig = None) -> bool:
    """Run automation service as main process"""
    service = get_automation_service(config)
    
    try:
        # Start service
        if not await service.start():
            return False
        
        # Keep running until shutdown
        await service.shutdown_event.wait()
        
        return True
        
    except KeyboardInterrupt:
        service.logger.info("Received keyboard interrupt")
        return True
    except Exception as e:
        service.logger.error(f"Service error: {e}")
        return False
    finally:
        await service.shutdown()
