"""
🛡️ StillMe Resilience Manager
============================

Comprehensive resilience management system for AGI learning automation.
Orchestrates error handling, recovery strategies, and system resilience
to ensure robust AGI operation under various failure conditions.

Tính năng:
- System-wide resilience orchestration
- Intelligent failure prediction và prevention
- Adaptive recovery strategies
- Health monitoring và self-healing
- Graceful degradation management
- Resilience metrics và reporting
- AGI-specific resilience patterns

Author: StillMe AI Framework
Version: 2.0.0
Date: 2025-09-28
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import json

from .error_handler import (
    ErrorHandler, ErrorCategory, ErrorSeverity, 
    RetryPolicy, CircuitBreakerConfig, get_error_handler
)

logger = logging.getLogger(__name__)

class ResilienceLevel(Enum):
    """Resilience levels"""
    MINIMAL = "minimal"      # Basic error handling
    STANDARD = "standard"    # Standard resilience
    HIGH = "high"           # High resilience
    MAXIMUM = "maximum"     # Maximum resilience

class SystemHealth(Enum):
    """System health states"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    FAILED = "failed"

@dataclass
class ResilienceConfig:
    """Resilience configuration"""
    level: ResilienceLevel = ResilienceLevel.STANDARD
    enable_prediction: bool = True
    enable_self_healing: bool = True
    enable_graceful_degradation: bool = True
    health_check_interval: int = 30  # seconds
    prediction_window: int = 300     # seconds
    recovery_timeout: int = 60       # seconds
    max_concurrent_recoveries: int = 3
    enable_circuit_breakers: bool = True
    enable_retry_policies: bool = True
    enable_fallback_modes: bool = True

@dataclass
class HealthMetrics:
    """System health metrics"""
    timestamp: datetime
    overall_health: SystemHealth
    component_health: Dict[str, SystemHealth]
    error_rate: float
    recovery_rate: float
    uptime_percentage: float
    performance_degradation: float
    resource_utilization: Dict[str, float]
    resilience_score: float

@dataclass
class FailurePrediction:
    """Failure prediction result"""
    component: str
    predicted_failure_time: datetime
    confidence: float
    failure_type: str
    recommended_action: str
    severity: ErrorSeverity

class ResilienceManager:
    """
    Comprehensive resilience management system for AGI
    """
    
    def __init__(self, config: ResilienceConfig = None):
        self.config = config or ResilienceConfig()
        self.logger = logging.getLogger(__name__)
        
        # Core components
        self.error_handler = get_error_handler()
        self.health_metrics_history: List[HealthMetrics] = []
        self.failure_predictions: List[FailurePrediction] = []
        
        # System state
        self.current_health = SystemHealth.HEALTHY
        self.component_states: Dict[str, SystemHealth] = {}
        self.active_recoveries: Dict[str, asyncio.Task] = {}
        self.degradation_modes: Dict[str, bool] = {}
        
        # Resilience strategies
        self.resilience_strategies: Dict[ResilienceLevel, List[Callable]] = {}
        self._setup_resilience_strategies()
        
        # Monitoring
        self.is_monitoring = False
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # Statistics
        self.stats = {
            'total_failures': 0,
            'successful_recoveries': 0,
            'failed_recoveries': 0,
            'predictions_made': 0,
            'accurate_predictions': 0,
            'system_uptime': 0,
            'last_failure': None,
            'last_recovery': None
        }
        
        # Initialize resilience system
        self._initialize_resilience_system()
    
    def _setup_resilience_strategies(self):
        """Setup resilience strategies by level"""
        self.resilience_strategies = {
            ResilienceLevel.MINIMAL: [
                self._basic_error_handling,
                self._simple_retry
            ],
            ResilienceLevel.STANDARD: [
                self._basic_error_handling,
                self._simple_retry,
                self._circuit_breakers,
                self._graceful_degradation
            ],
            ResilienceLevel.HIGH: [
                self._advanced_error_handling,
                self._intelligent_retry,
                self._circuit_breakers,
                self._graceful_degradation,
                self._failure_prediction,
                self._proactive_recovery
            ],
            ResilienceLevel.MAXIMUM: [
                self._advanced_error_handling,
                self._intelligent_retry,
                self._circuit_breakers,
                self._graceful_degradation,
                self._failure_prediction,
                self._proactive_recovery,
                self._self_healing,
                self._adaptive_resilience
            ]
        }
    
    def _initialize_resilience_system(self):
        """Initialize resilience system based on configuration"""
        self.logger.info(f"Initializing resilience system at {self.config.level.value} level")
        
        # Apply resilience strategies
        strategies = self.resilience_strategies.get(self.config.level, [])
        for strategy in strategies:
            try:
                strategy()
                self.logger.info(f"Applied resilience strategy: {strategy.__name__}")
            except Exception as e:
                self.logger.error(f"Failed to apply strategy {strategy.__name__}: {e}")
        
        # Initialize component states
        self._initialize_component_states()
        
        self.logger.info("Resilience system initialized successfully")
    
    def _initialize_component_states(self):
        """Initialize component health states"""
        components = [
            'learning_system', 'scheduler', 'resource_monitor',
            'performance_analyzer', 'dashboard', 'api_server'
        ]
        
        for component in components:
            self.component_states[component] = SystemHealth.HEALTHY
            self.degradation_modes[component] = False
    
    async def start_monitoring(self):
        """Start resilience monitoring"""
        if self.is_monitoring:
            self.logger.warning("Resilience monitoring already started")
            return
        
        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("Resilience monitoring started")
    
    async def stop_monitoring(self):
        """Stop resilience monitoring"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Resilience monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main resilience monitoring loop"""
        while self.is_monitoring:
            try:
                # Collect health metrics
                health_metrics = await self._collect_health_metrics()
                self.health_metrics_history.append(health_metrics)
                
                # Update system health
                self._update_system_health(health_metrics)
                
                # Predict failures if enabled
                if self.config.enable_prediction:
                    await self._predict_failures(health_metrics)
                
                # Perform proactive recovery if enabled
                if self.config.enable_self_healing:
                    await self._proactive_recovery_check(health_metrics)
                
                # Clean up old data
                self._cleanup_old_data()
                
                await asyncio.sleep(self.config.health_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in resilience monitoring loop: {e}")
                await asyncio.sleep(self.config.health_check_interval)
    
    async def _collect_health_metrics(self) -> HealthMetrics:
        """Collect system health metrics"""
        # Calculate error rate
        error_rate = self._calculate_error_rate()
        
        # Calculate recovery rate
        recovery_rate = self._calculate_recovery_rate()
        
        # Calculate uptime percentage
        uptime_percentage = self._calculate_uptime_percentage()
        
        # Calculate performance degradation
        performance_degradation = self._calculate_performance_degradation()
        
        # Get resource utilization
        resource_utilization = await self._get_resource_utilization()
        
        # Calculate resilience score
        resilience_score = self._calculate_resilience_score(
            error_rate, recovery_rate, uptime_percentage, performance_degradation
        )
        
        # Determine overall health
        overall_health = self._determine_overall_health(
            error_rate, recovery_rate, performance_degradation, resilience_score
        )
        
        return HealthMetrics(
            timestamp=datetime.now(),
            overall_health=overall_health,
            component_health=self.component_states.copy(),
            error_rate=error_rate,
            recovery_rate=recovery_rate,
            uptime_percentage=uptime_percentage,
            performance_degradation=performance_degradation,
            resource_utilization=resource_utilization,
            resilience_score=resilience_score
        )
    
    def _calculate_error_rate(self) -> float:
        """Calculate current error rate"""
        if not self.health_metrics_history:
            return 0.0
        
        # Calculate error rate over last 10 minutes
        cutoff_time = datetime.now() - timedelta(minutes=10)
        recent_metrics = [m for m in self.health_metrics_history if m.timestamp > cutoff_time]
        
        if not recent_metrics:
            return 0.0
        
        total_errors = sum(m.error_rate for m in recent_metrics)
        return total_errors / len(recent_metrics)
    
    def _calculate_recovery_rate(self) -> float:
        """Calculate recovery success rate"""
        if self.stats['total_failures'] == 0:
            return 1.0
        
        return self.stats['successful_recoveries'] / self.stats['total_failures']
    
    def _calculate_uptime_percentage(self) -> float:
        """Calculate system uptime percentage"""
        # Simplified calculation - in real implementation, track actual uptime
        if self.current_health == SystemHealth.FAILED:
            return 0.0
        elif self.current_health == SystemHealth.CRITICAL:
            return 0.5
        elif self.current_health == SystemHealth.DEGRADED:
            return 0.8
        else:
            return 1.0
    
    def _calculate_performance_degradation(self) -> float:
        """Calculate performance degradation"""
        if not self.health_metrics_history:
            return 0.0
        
        # Calculate average performance degradation over last hour
        cutoff_time = datetime.now() - timedelta(hours=1)
        recent_metrics = [m for m in self.health_metrics_history if m.timestamp > cutoff_time]
        
        if not recent_metrics:
            return 0.0
        
        total_degradation = sum(m.performance_degradation for m in recent_metrics)
        return total_degradation / len(recent_metrics)
    
    async def _get_resource_utilization(self) -> Dict[str, float]:
        """Get current resource utilization"""
        # This would integrate with the resource monitor
        return {
            'cpu': 0.0,
            'memory': 0.0,
            'disk': 0.0,
            'network': 0.0
        }
    
    def _calculate_resilience_score(self, error_rate: float, recovery_rate: float, 
                                  uptime_percentage: float, performance_degradation: float) -> float:
        """Calculate overall resilience score"""
        # Weighted combination of metrics
        weights = {
            'error_rate': 0.3,
            'recovery_rate': 0.3,
            'uptime': 0.2,
            'performance': 0.2
        }
        
        # Normalize metrics (lower is better for error_rate and performance_degradation)
        error_score = max(0, 1 - error_rate)
        performance_score = max(0, 1 - performance_degradation)
        
        resilience_score = (
            weights['error_rate'] * error_score +
            weights['recovery_rate'] * recovery_rate +
            weights['uptime'] * uptime_percentage +
            weights['performance'] * performance_score
        )
        
        return min(1.0, max(0.0, resilience_score))
    
    def _determine_overall_health(self, error_rate: float, recovery_rate: float,
                                performance_degradation: float, resilience_score: float) -> SystemHealth:
        """Determine overall system health"""
        if resilience_score < 0.3 or error_rate > 0.5:
            return SystemHealth.FAILED
        elif resilience_score < 0.6 or error_rate > 0.2 or performance_degradation > 0.5:
            return SystemHealth.CRITICAL
        elif resilience_score < 0.8 or error_rate > 0.1 or performance_degradation > 0.2:
            return SystemHealth.DEGRADED
        else:
            return SystemHealth.HEALTHY
    
    def _update_system_health(self, health_metrics: HealthMetrics):
        """Update system health state"""
        self.current_health = health_metrics.overall_health
        self.component_states.update(health_metrics.component_health)
        
        # Log health changes
        if health_metrics.overall_health != self.current_health:
            self.logger.info(f"System health changed to: {health_metrics.overall_health.value}")
    
    async def _predict_failures(self, health_metrics: HealthMetrics):
        """Predict potential failures"""
        predictions = []
        
        # Analyze trends in health metrics
        if len(self.health_metrics_history) >= 5:
            recent_metrics = self.health_metrics_history[-5:]
            
            # Check for degrading trends
            for component, health in health_metrics.component_health.items():
                if health == SystemHealth.DEGRADED:
                    # Predict potential failure
                    prediction = FailurePrediction(
                        component=component,
                        predicted_failure_time=datetime.now() + timedelta(minutes=30),
                        confidence=0.7,
                        failure_type="performance_degradation",
                        recommended_action="scale_down_operations",
                        severity=ErrorSeverity.MEDIUM
                    )
                    predictions.append(prediction)
        
        # Add predictions
        for prediction in predictions:
            self.failure_predictions.append(prediction)
            self.stats['predictions_made'] += 1
            self.logger.warning(f"Failure predicted for {prediction.component}: {prediction.recommended_action}")
    
    async def _proactive_recovery_check(self, health_metrics: HealthMetrics):
        """Check for proactive recovery opportunities"""
        # Check if any components need proactive recovery
        for component, health in health_metrics.component_health.items():
            if health in [SystemHealth.DEGRADED, SystemHealth.CRITICAL]:
                if component not in self.active_recoveries:
                    # Start proactive recovery
                    recovery_task = asyncio.create_task(
                        self._proactive_recovery(component, health)
                    )
                    self.active_recoveries[component] = recovery_task
    
    async def _proactive_recovery(self, component: str, health: SystemHealth):
        """Perform proactive recovery for component"""
        try:
            self.logger.info(f"Starting proactive recovery for {component}")
            
            # Implement component-specific recovery strategies
            if component == 'learning_system':
                await self._recover_learning_system()
            elif component == 'scheduler':
                await self._recover_scheduler()
            elif component == 'resource_monitor':
                await self._recover_resource_monitor()
            elif component == 'performance_analyzer':
                await self._recover_performance_analyzer()
            
            # Update component health
            self.component_states[component] = SystemHealth.HEALTHY
            self.stats['successful_recoveries'] += 1
            self.stats['last_recovery'] = datetime.now()
            
            self.logger.info(f"Proactive recovery completed for {component}")
            
        except Exception as e:
            self.logger.error(f"Proactive recovery failed for {component}: {e}")
            self.stats['failed_recoveries'] += 1
        finally:
            # Remove from active recoveries
            if component in self.active_recoveries:
                del self.active_recoveries[component]
    
    async def _recover_learning_system(self):
        """Recover learning system"""
        self.logger.info("Recovering learning system")
        # Implement learning system recovery
        await asyncio.sleep(1)  # Simulate recovery time
    
    async def _recover_scheduler(self):
        """Recover scheduler"""
        self.logger.info("Recovering scheduler")
        # Implement scheduler recovery
        await asyncio.sleep(1)  # Simulate recovery time
    
    async def _recover_resource_monitor(self):
        """Recover resource monitor"""
        self.logger.info("Recovering resource monitor")
        # Implement resource monitor recovery
        await asyncio.sleep(1)  # Simulate recovery time
    
    async def _recover_performance_analyzer(self):
        """Recover performance analyzer"""
        self.logger.info("Recovering performance analyzer")
        # Implement performance analyzer recovery
        await asyncio.sleep(1)  # Simulate recovery time
    
    def _cleanup_old_data(self):
        """Clean up old monitoring data"""
        # Keep only last 24 hours of health metrics
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.health_metrics_history = [
            m for m in self.health_metrics_history 
            if m.timestamp > cutoff_time
        ]
        
        # Keep only recent failure predictions
        cutoff_time = datetime.now() - timedelta(hours=1)
        self.failure_predictions = [
            p for p in self.failure_predictions 
            if p.predicted_failure_time > cutoff_time
        ]
    
    # Resilience strategies
    def _basic_error_handling(self):
        """Setup basic error handling"""
        self.logger.info("Setting up basic error handling")
        # Basic error handling is already initialized
    
    def _simple_retry(self):
        """Setup simple retry policies"""
        self.logger.info("Setting up simple retry policies")
        # Simple retry policies are already configured
    
    def _advanced_error_handling(self):
        """Setup advanced error handling"""
        self.logger.info("Setting up advanced error handling")
        # Advanced error handling strategies
    
    def _intelligent_retry(self):
        """Setup intelligent retry policies"""
        self.logger.info("Setting up intelligent retry policies")
        # Intelligent retry based on error type and context
    
    def _circuit_breakers(self):
        """Setup circuit breakers"""
        self.logger.info("Setting up circuit breakers")
        # Circuit breakers are already configured
    
    def _graceful_degradation(self):
        """Setup graceful degradation"""
        self.logger.info("Setting up graceful degradation")
        # Graceful degradation strategies
    
    def _failure_prediction(self):
        """Setup failure prediction"""
        self.logger.info("Setting up failure prediction")
        # Failure prediction is enabled in monitoring loop
    
    def _proactive_recovery(self):
        """Setup proactive recovery"""
        self.logger.info("Setting up proactive recovery")
        # Proactive recovery is enabled in monitoring loop
    
    def _self_healing(self):
        """Setup self-healing capabilities"""
        self.logger.info("Setting up self-healing capabilities")
        # Self-healing strategies
    
    def _adaptive_resilience(self):
        """Setup adaptive resilience"""
        self.logger.info("Setting up adaptive resilience")
        # Adaptive resilience based on system conditions
    
    async def handle_component_failure(self, component: str, error: Exception, context: Dict[str, Any] = None):
        """Handle component failure"""
        self.logger.error(f"Component failure detected: {component} - {error}")
        
        # Update statistics
        self.stats['total_failures'] += 1
        self.stats['last_failure'] = datetime.now()
        
        # Update component state
        self.component_states[component] = SystemHealth.FAILED
        
        # Attempt recovery
        try:
            await self._proactive_recovery(component, SystemHealth.FAILED)
        except Exception as recovery_error:
            self.logger.error(f"Recovery failed for {component}: {recovery_error}")
            self.stats['failed_recoveries'] += 1
    
    def get_resilience_status(self) -> Dict[str, Any]:
        """Get resilience system status"""
        return {
            'config': asdict(self.config),
            'current_health': self.current_health.value,
            'component_states': {k: v.value for k, v in self.component_states.items()},
            'degradation_modes': self.degradation_modes,
            'active_recoveries': list(self.active_recoveries.keys()),
            'statistics': self.stats,
            'recent_predictions': [asdict(p) for p in self.failure_predictions[-5:]],
            'health_metrics': asdict(self.health_metrics_history[-1]) if self.health_metrics_history else None,
            'monitoring_active': self.is_monitoring
        }
    
    def export_resilience_report(self, file_path: str):
        """Export resilience report"""
        try:
            report = {
                'export_timestamp': datetime.now().isoformat(),
                'resilience_status': self.get_resilience_status(),
                'health_metrics_history': [asdict(m) for m in self.health_metrics_history[-100:]],
                'failure_predictions': [asdict(p) for p in self.failure_predictions],
                'error_statistics': self.error_handler.get_error_statistics()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"Resilience report exported to {file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to export resilience report: {e}")

# Global resilience manager instance
_resilience_manager_instance: Optional[ResilienceManager] = None

def get_resilience_manager(config: ResilienceConfig = None) -> ResilienceManager:
    """Get global resilience manager instance"""
    global _resilience_manager_instance
    if _resilience_manager_instance is None:
        _resilience_manager_instance = ResilienceManager(config)
    return _resilience_manager_instance

async def initialize_resilience_system(config: ResilienceConfig = None) -> ResilienceManager:
    """Initialize resilience system"""
    manager = get_resilience_manager(config)
    await manager.start_monitoring()
    return manager
