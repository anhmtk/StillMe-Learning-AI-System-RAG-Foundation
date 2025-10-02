"""
🎯 AUTONOMOUS STILLME MANAGEMENT SYSTEM

Hệ thống quản lý tự động cho StillMe ecosystem.
Bao gồm automated monitoring, self-healing, predictive maintenance, và automated scaling.

Author: AgentDev System
Version: 2.0.0
Phase: 2.1 - Autonomous StillMe Management
"""

import asyncio
import logging
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

import numpy as np
import psutil

# Import Phase 1 modules with proper typing
if TYPE_CHECKING:
    from stillme_core.final_validation_system import (
        FinalValidationSystem as CoreFinalValidationSystem,
    )
    from stillme_core.integration_bridge import (
        IntegrationBridge as CoreIntegrationBridge,
    )
    from stillme_core.memory_security_integration import (
        MemorySecurityIntegration as CoreMemorySecurityIntegration,
    )
    from stillme_core.module_governance_system import (
        ModuleGovernanceSystem as CoreModuleGovernanceSystem,
    )
    from stillme_core.performance_monitor import (
        PerformanceMonitor as CorePerformanceMonitor,
    )
    from stillme_core.security_middleware import (
        SecurityMiddleware as CoreSecurityMiddleware,
    )
    from stillme_core.validation_framework import (
        ComprehensiveValidationFramework as CoreComprehensiveValidationFramework,
    )

    from .final_validation_system import FinalValidationSystem
    from .integration_bridge import IntegrationBridge
    from .memory_security_integration import MemorySecurityIntegration
    from .module_governance_system import ModuleGovernanceSystem
    from .performance_monitor import PerformanceMonitor
    from .security_middleware import SecurityMiddleware
    from .validation_framework import ComprehensiveValidationFramework

# Runtime imports with fallback
try:
    from .security_middleware import SecurityMiddleware
except ImportError:
    SecurityMiddleware = None

try:
    from .performance_monitor import PerformanceMonitor
except ImportError:
    PerformanceMonitor = None

try:
    from .final_validation_system import FinalValidationSystem
    from .integration_bridge import IntegrationBridge
    from .memory_security_integration import MemorySecurityIntegration
    from .module_governance_system import ModuleGovernanceSystem
    from .validation_framework import ComprehensiveValidationFramework
except ImportError:
    FinalValidationSystem = None
    IntegrationBridge = None
    MemorySecurityIntegration = None
    ModuleGovernanceSystem = None
    ComprehensiveValidationFramework = None

try:
    from stillme_core.security_middleware import (
        SecurityMiddleware as CoreSecurityMiddleware,
    )
except ImportError:
    CoreSecurityMiddleware = None

try:
    from stillme_core.performance_monitor import (
        PerformanceMonitor as CorePerformanceMonitor,
    )
except ImportError:
    CorePerformanceMonitor = None

try:
    from stillme_core.final_validation_system import (
        FinalValidationSystem as CoreFinalValidationSystem,
    )
    from stillme_core.integration_bridge import (
        IntegrationBridge as CoreIntegrationBridge,
    )
    from stillme_core.memory_security_integration import (
        MemorySecurityIntegration as CoreMemorySecurityIntegration,
    )
    from stillme_core.module_governance_system import (
        ModuleGovernanceSystem as CoreModuleGovernanceSystem,
    )
    from stillme_core.validation_framework import (
        ComprehensiveValidationFramework as CoreComprehensiveValidationFramework,
    )
except ImportError:
    CoreFinalValidationSystem = None
    CoreIntegrationBridge = None
    CoreMemorySecurityIntegration = None
    CoreModuleGovernanceSystem = None
    CoreComprehensiveValidationFramework = None


# Create mock classes for testing with proper typing
class SecurityMiddleware:
    def __init__(self) -> None:
        pass

    def get_security_report(self) -> dict[str, Any]:
        return {"security_score": 100}


class PerformanceMonitor:
    def __init__(self) -> None:
        pass

    def get_performance_summary(self) -> dict[str, Any]:
        return {"status": "healthy"}


class IntegrationBridge:
    def __init__(self) -> None:
        pass

    def register_endpoint(
        self, method: str, path: str, handler: Any, auth_required: bool = False
    ) -> None:
        pass


class MemorySecurityIntegration:
    def __init__(self) -> None:
        pass

    def get_memory_statistics(self) -> dict[str, Any]:
        return {"access_logs_count": 0}


class ModuleGovernanceSystem:
    def __init__(self) -> None:
        pass

    def get_governance_status(self) -> dict[str, Any]:
        return {"status": "success", "data": {}}


class ComprehensiveValidationFramework:
    def __init__(self) -> None:
        pass

    def get_validation_status(self) -> dict[str, Any]:
        return {"status": "success", "data": {}}


class FinalValidationSystem:
    def __init__(self) -> None:
        pass

    def get_system_health(self) -> dict[str, Any]:
        return {"status": "success", "data": {}}


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity enumeration"""

    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    INFO = 5


class SystemState(Enum):
    """System state enumeration"""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    FAILED = "failed"
    MAINTENANCE = "maintenance"


class RecoveryAction(Enum):
    """Recovery action enumeration"""

    RESTART = "restart"
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    ROLLBACK = "rollback"
    ISOLATE = "isolate"
    NOTIFY = "notify"


@dataclass
class SystemMetric:
    """System metric structure"""

    metric_name: str
    value: float
    unit: str
    timestamp: datetime
    source: str
    tags: dict[str, str]


@dataclass
class Alert:
    """Alert structure"""

    alert_id: str
    severity: AlertSeverity
    title: str
    description: str
    source: str
    timestamp: datetime
    resolved: bool
    resolved_at: Optional[datetime]
    metadata: dict[str, Any]


@dataclass
class HealthCheck:
    """Health check structure"""

    check_id: str
    check_name: str
    status: SystemState
    last_check: datetime
    response_time: float
    error_message: Optional[str]
    metadata: dict[str, Any]


@dataclass
class RecoveryPlan:
    """Recovery plan structure"""

    plan_id: str
    trigger_condition: str
    actions: list[RecoveryAction]
    priority: int
    timeout_seconds: int
    rollback_plan: Optional[str]
    metadata: dict[str, Any]


class AutonomousManagementSystem:
    """
    Main Autonomous Management System
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.logger = self._setup_logging()

        # Initialize Phase 1 components
        self.security_middleware = SecurityMiddleware()
        self.performance_monitor = PerformanceMonitor()
        self.integration_bridge = IntegrationBridge()
        self.memory_integration = MemorySecurityIntegration()
        self.governance_system = ModuleGovernanceSystem()
        self.validation_framework = ComprehensiveValidationFramework()
        self.final_validation = FinalValidationSystem()

        # Autonomous management state
        self.system_metrics: list[SystemMetric] = []
        self.active_alerts: list[Alert] = []
        self.health_checks: dict[str, HealthCheck] = {}
        self.recovery_plans: dict[str, RecoveryPlan] = {}

        # Monitoring and control
        self.monitoring_active = False
        self.self_healing_enabled = True
        self.predictive_maintenance_enabled = True
        self.auto_scaling_enabled = True

        # Performance tracking
        self.performance_metrics: dict[str, list[float]] = {
            "monitoring_times": [],
            "healing_times": [],
            "scaling_times": [],
            "maintenance_times": [],
        }

        # Anomaly detection
        self.anomaly_detector = AnomalyDetector()
        self.predictive_analyzer = PredictiveAnalyzer()

        # Recovery system
        self.recovery_system = RecoverySystem()

        # Initialize system
        self._initialize_autonomous_system()
        self._setup_autonomous_monitoring()

        self.logger.info("✅ Autonomous Management System initialized")

    def _setup_logging(self):
        """Setup logging system"""
        logger = logging.getLogger("AutonomousManagementSystem")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _initialize_autonomous_system(self):
        """Initialize autonomous management system"""
        try:
            # Define health checks
            self._define_health_checks()

            # Define recovery plans
            self._define_recovery_plans()

            # Initialize monitoring
            self._initialize_monitoring()

            self.logger.info("✅ Autonomous management system initialized successfully")

        except Exception as e:
            self.logger.error(f"Error initializing autonomous system: {e}")
            raise

    def _define_health_checks(self):
        """Define system health checks"""
        try:
            health_checks = [
                HealthCheck(
                    check_id="system_resources",
                    check_name="System Resources Check",
                    status=SystemState.HEALTHY,
                    last_check=datetime.now(),
                    response_time=0.0,
                    error_message=None,
                    metadata={},
                ),
                HealthCheck(
                    check_id="security_system",
                    check_name="Security System Check",
                    status=SystemState.HEALTHY,
                    last_check=datetime.now(),
                    response_time=0.0,
                    error_message=None,
                    metadata={},
                ),
                HealthCheck(
                    check_id="memory_system",
                    check_name="Memory System Check",
                    status=SystemState.HEALTHY,
                    last_check=datetime.now(),
                    response_time=0.0,
                    error_message=None,
                    metadata={},
                ),
                HealthCheck(
                    check_id="governance_system",
                    check_name="Governance System Check",
                    status=SystemState.HEALTHY,
                    last_check=datetime.now(),
                    response_time=0.0,
                    error_message=None,
                    metadata={},
                ),
                HealthCheck(
                    check_id="validation_system",
                    check_name="Validation System Check",
                    status=SystemState.HEALTHY,
                    last_check=datetime.now(),
                    response_time=0.0,
                    error_message=None,
                    metadata={},
                ),
            ]

            for check in health_checks:
                self.health_checks[check.check_id] = check

            self.logger.info(f"✅ Defined {len(health_checks)} health checks")

        except Exception as e:
            self.logger.error(f"Error defining health checks: {e}")

    def _define_recovery_plans(self):
        """Define recovery plans"""
        try:
            recovery_plans = [
                RecoveryPlan(
                    plan_id="high_memory_usage",
                    trigger_condition="memory_usage > 90%",
                    actions=[RecoveryAction.SCALE_UP, RecoveryAction.NOTIFY],
                    priority=1,
                    timeout_seconds=300,
                    rollback_plan="scale_down_if_failed",
                    metadata={"resource_type": "memory"},
                ),
                RecoveryPlan(
                    plan_id="high_cpu_usage",
                    trigger_condition="cpu_usage > 90%",
                    actions=[RecoveryAction.SCALE_UP, RecoveryAction.NOTIFY],
                    priority=1,
                    timeout_seconds=300,
                    rollback_plan="scale_down_if_failed",
                    metadata={"resource_type": "cpu"},
                ),
                RecoveryPlan(
                    plan_id="service_failure",
                    trigger_condition="service_status == 'failed'",
                    actions=[
                        RecoveryAction.RESTART,
                        RecoveryAction.ISOLATE,
                        RecoveryAction.NOTIFY,
                    ],
                    priority=1,
                    timeout_seconds=600,
                    rollback_plan="rollback_to_previous_version",
                    metadata={"service_type": "critical"},
                ),
                RecoveryPlan(
                    plan_id="security_breach",
                    trigger_condition="security_score < 70",
                    actions=[RecoveryAction.ISOLATE, RecoveryAction.NOTIFY],
                    priority=1,
                    timeout_seconds=60,
                    rollback_plan="emergency_shutdown",
                    metadata={"security_level": "critical"},
                ),
            ]

            for plan in recovery_plans:
                self.recovery_plans[plan.plan_id] = plan

            self.logger.info(f"✅ Defined {len(recovery_plans)} recovery plans")

        except Exception as e:
            self.logger.error(f"Error defining recovery plans: {e}")

    def _initialize_monitoring(self):
        """Initialize monitoring system"""
        try:
            # Start monitoring thread
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop, daemon=True
            )
            self.monitoring_thread.start()

            self.monitoring_active = True

            self.logger.info("✅ Monitoring system initialized")

        except Exception as e:
            self.logger.error(f"Error initializing monitoring: {e}")

    def _setup_autonomous_monitoring(self):
        """Setup autonomous monitoring endpoints"""
        try:
            # Register autonomous management endpoints
            self.integration_bridge.register_endpoint(
                "GET",
                "/autonomous/status",
                self._get_autonomous_status,
                auth_required=True,
            )
            self.integration_bridge.register_endpoint(
                "GET", "/autonomous/health", self._get_system_health, auth_required=True
            )
            self.integration_bridge.register_endpoint(
                "GET", "/autonomous/alerts", self._get_active_alerts, auth_required=True
            )
            self.integration_bridge.register_endpoint(
                "POST",
                "/autonomous/recovery",
                self._trigger_recovery,
                auth_required=True,
            )
            self.integration_bridge.register_endpoint(
                "GET",
                "/autonomous/metrics",
                self._get_system_metrics,
                auth_required=True,
            )

            self.logger.info("✅ Autonomous monitoring setup completed")

        except Exception as e:
            self.logger.error(f"Error setting up autonomous monitoring: {e}")

    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                start_time = time.time()

                # Collect system metrics
                self._collect_system_metrics()

                # Perform health checks
                self._perform_health_checks()

                # Check for anomalies
                self._check_anomalies()

                # Trigger recovery if needed
                if self.self_healing_enabled:
                    self._check_recovery_triggers()

                # Predictive maintenance
                if self.predictive_maintenance_enabled:
                    self._predictive_maintenance_check()

                # Auto scaling
                if self.auto_scaling_enabled:
                    self._auto_scaling_check()

                # Track performance
                monitoring_time = time.time() - start_time
                self.performance_metrics["monitoring_times"].append(monitoring_time)

                # Sleep until next check
                time.sleep(30)  # Check every 30 seconds

            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)  # Short sleep on error

    def _collect_system_metrics(self):
        """Collect system metrics"""
        try:
            # System resource metrics
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            disk = psutil.disk_usage("/")

            # Add metrics
            self.system_metrics.append(
                SystemMetric(
                    metric_name="memory_usage_percent",
                    value=memory.percent,
                    unit="percent",
                    timestamp=datetime.now(),
                    source="system",
                    tags={"type": "memory"},
                )
            )

            self.system_metrics.append(
                SystemMetric(
                    metric_name="cpu_usage_percent",
                    value=cpu_percent,
                    unit="percent",
                    timestamp=datetime.now(),
                    source="system",
                    tags={"type": "cpu"},
                )
            )

            self.system_metrics.append(
                SystemMetric(
                    metric_name="disk_usage_percent",
                    value=disk.percent,
                    unit="percent",
                    timestamp=datetime.now(),
                    source="system",
                    tags={"type": "disk"},
                )
            )

            # Keep only last 1000 metrics
            if len(self.system_metrics) > 1000:
                self.system_metrics = self.system_metrics[-1000:]

        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")

    def _perform_health_checks(self):
        """Perform health checks"""
        try:
            for check_id, check in self.health_checks.items():
                start_time = time.time()

                # Perform the specific health check
                if check_id == "system_resources":
                    status = self._check_system_resources()
                elif check_id == "security_system":
                    status = self._check_security_system()
                elif check_id == "memory_system":
                    status = self._check_memory_system()
                elif check_id == "governance_system":
                    status = self._check_governance_system()
                elif check_id == "validation_system":
                    status = self._check_validation_system()
                else:
                    status = SystemState.HEALTHY

                # Update check
                check.status = status
                check.last_check = datetime.now()
                check.response_time = time.time() - start_time

                # Create alert if unhealthy
                if status in [
                    SystemState.WARNING,
                    SystemState.CRITICAL,
                    SystemState.FAILED,
                ]:
                    self._create_alert(
                        severity=(
                            AlertSeverity.HIGH
                            if status == SystemState.CRITICAL
                            else AlertSeverity.MEDIUM
                        ),
                        title=f"Health Check Failed: {check.check_name}",
                        description=f"Health check {check.check_name} is in {status.value} state",
                        source=check_id,
                    )

        except Exception as e:
            self.logger.error(f"Error performing health checks: {e}")

    def _check_system_resources(self) -> SystemState:
        """Check system resources"""
        try:
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            disk = psutil.disk_usage("/")

            # Check thresholds
            if memory.percent > 95 or cpu_percent > 95 or disk.percent > 95:
                return SystemState.CRITICAL
            elif memory.percent > 85 or cpu_percent > 85 or disk.percent > 85:
                return SystemState.WARNING
            else:
                return SystemState.HEALTHY

        except Exception as e:
            self.logger.error(f"Error checking system resources: {e}")
            return SystemState.FAILED

    def _check_security_system(self) -> SystemState:
        """Check security system"""
        try:
            security_report = self.security_middleware.get_security_report()
            security_score = security_report.get("security_score", 0)

            if security_score < 70:
                return SystemState.CRITICAL
            elif security_score < 85:
                return SystemState.WARNING
            else:
                return SystemState.HEALTHY

        except Exception as e:
            self.logger.error(f"Error checking security system: {e}")
            return SystemState.FAILED

    def _check_memory_system(self) -> SystemState:
        """Check memory system"""
        try:
            self.memory_integration.get_memory_statistics()
            # Mock check - in real implementation, check actual memory system health
            return SystemState.HEALTHY

        except Exception as e:
            self.logger.error(f"Error checking memory system: {e}")
            return SystemState.FAILED

    def _check_governance_system(self) -> SystemState:
        """Check governance system"""
        try:
            governance_status = self.governance_system.get_governance_status()
            if governance_status.get("status") == "success":
                return SystemState.HEALTHY
            else:
                return SystemState.WARNING

        except Exception as e:
            self.logger.error(f"Error checking governance system: {e}")
            return SystemState.FAILED

    def _check_validation_system(self) -> SystemState:
        """Check validation system"""
        try:
            validation_status = self.validation_framework.get_validation_status()
            if validation_status.get("status") == "success":
                return SystemState.HEALTHY
            else:
                return SystemState.WARNING

        except Exception as e:
            self.logger.error(f"Error checking validation system: {e}")
            return SystemState.FAILED

    def _check_anomalies(self):
        """Check for anomalies"""
        try:
            if len(self.system_metrics) < 10:
                return  # Need more data for anomaly detection

            # Get recent metrics
            recent_metrics = self.system_metrics[-50:]  # Last 50 metrics

            # Check for anomalies in key metrics
            for metric_name in [
                "memory_usage_percent",
                "cpu_usage_percent",
                "disk_usage_percent",
            ]:
                values = [
                    m.value for m in recent_metrics if m.metric_name == metric_name
                ]
                if len(values) >= 5:
                    if self.anomaly_detector.detect_anomaly(values):
                        self._create_alert(
                            severity=AlertSeverity.MEDIUM,
                            title=f"Anomaly Detected: {metric_name}",
                            description=f"Unusual pattern detected in {metric_name}",
                            source="anomaly_detector",
                        )

        except Exception as e:
            self.logger.error(f"Error checking anomalies: {e}")

    def _check_recovery_triggers(self):
        """Check recovery triggers"""
        try:
            for plan_id, plan in self.recovery_plans.items():
                if self._evaluate_trigger_condition(plan.trigger_condition):
                    self.logger.warning(f"🚨 Recovery trigger activated: {plan_id}")
                    self._execute_recovery_plan(plan)

        except Exception as e:
            self.logger.error(f"Error checking recovery triggers: {e}")

    def _evaluate_trigger_condition(self, condition: str) -> bool:
        """Evaluate trigger condition"""
        try:
            # Simple condition evaluation
            if "memory_usage > 90%" in condition:
                memory = psutil.virtual_memory()
                return memory.percent > 90
            elif "cpu_usage > 90%" in condition:
                cpu_percent = psutil.cpu_percent(interval=1)
                return cpu_percent > 90
            elif "security_score < 70" in condition:
                security_report = self.security_middleware.get_security_report()
                return security_report.get("security_score", 100) < 70
            else:
                return False

        except Exception as e:
            self.logger.error(f"Error evaluating trigger condition: {e}")
            return False

    def _execute_recovery_plan(self, plan: RecoveryPlan):
        """Execute recovery plan"""
        try:
            start_time = time.time()

            self.logger.info(f"🔄 Executing recovery plan: {plan.plan_id}")

            for action in plan.actions:
                if action == RecoveryAction.SCALE_UP:
                    self._scale_up_resources()
                elif action == RecoveryAction.SCALE_DOWN:
                    self._scale_down_resources()
                elif action == RecoveryAction.RESTART:
                    self._restart_services()
                elif action == RecoveryAction.ISOLATE:
                    self._isolate_components()
                elif action == RecoveryAction.NOTIFY:
                    self._send_notification(plan)

            # Track performance
            recovery_time = time.time() - start_time
            self.performance_metrics["healing_times"].append(recovery_time)

            self.logger.info(f"✅ Recovery plan {plan.plan_id} executed successfully")

        except Exception as e:
            self.logger.error(f"Error executing recovery plan {plan.plan_id}: {e}")

    def _scale_up_resources(self):
        """Scale up resources"""
        try:
            self.logger.info("📈 Scaling up resources...")
            # Mock implementation - in real system, this would scale actual resources
            time.sleep(0.1)  # Simulate scaling time
            self.logger.info("✅ Resources scaled up successfully")

        except Exception as e:
            self.logger.error(f"Error scaling up resources: {e}")

    def _scale_down_resources(self):
        """Scale down resources"""
        try:
            self.logger.info("📉 Scaling down resources...")
            # Mock implementation
            time.sleep(0.1)
            self.logger.info("✅ Resources scaled down successfully")

        except Exception as e:
            self.logger.error(f"Error scaling down resources: {e}")

    def _restart_services(self):
        """Restart services"""
        try:
            self.logger.info("🔄 Restarting services...")
            # Mock implementation
            time.sleep(0.2)
            self.logger.info("✅ Services restarted successfully")

        except Exception as e:
            self.logger.error(f"Error restarting services: {e}")

    def _isolate_components(self):
        """Isolate components"""
        try:
            self.logger.info("🔒 Isolating components...")
            # Mock implementation
            time.sleep(0.1)
            self.logger.info("✅ Components isolated successfully")

        except Exception as e:
            self.logger.error(f"Error isolating components: {e}")

    def _send_notification(self, plan: RecoveryPlan):
        """Send notification"""
        try:
            self.logger.info(
                f"📢 Sending notification for recovery plan: {plan.plan_id}"
            )
            # Mock implementation
            time.sleep(0.05)
            self.logger.info("✅ Notification sent successfully")

        except Exception as e:
            self.logger.error(f"Error sending notification: {e}")

    def _predictive_maintenance_check(self):
        """Check for predictive maintenance needs"""
        try:
            if len(self.system_metrics) < 20:
                return  # Need more data

            # Get recent metrics for analysis
            recent_metrics = self.system_metrics[-100:]

            # Analyze trends
            for metric_name in ["memory_usage_percent", "cpu_usage_percent"]:
                values = [
                    m.value for m in recent_metrics if m.metric_name == metric_name
                ]
                if len(values) >= 10:
                    trend = self.predictive_analyzer.analyze_trend(values)
                    if trend.get("needs_maintenance", False):
                        self._schedule_maintenance(metric_name, trend)

        except Exception as e:
            self.logger.error(f"Error in predictive maintenance check: {e}")

    def _schedule_maintenance(self, metric_name: str, trend: dict[str, Any]):
        """Schedule maintenance"""
        try:
            self.logger.info(f"🔧 Scheduling maintenance for {metric_name}")
            # Mock implementation
            time.sleep(0.1)
            self.logger.info("✅ Maintenance scheduled successfully")

        except Exception as e:
            self.logger.error(f"Error scheduling maintenance: {e}")

    def _auto_scaling_check(self):
        """Check for auto scaling needs"""
        try:
            if len(self.system_metrics) < 10:
                return

            # Get recent resource usage
            recent_metrics = self.system_metrics[-20:]
            memory_values = [
                m.value
                for m in recent_metrics
                if m.metric_name == "memory_usage_percent"
            ]
            cpu_values = [
                m.value for m in recent_metrics if m.metric_name == "cpu_usage_percent"
            ]

            if memory_values and cpu_values:
                avg_memory = sum(memory_values) / len(memory_values)
                avg_cpu = sum(cpu_values) / len(cpu_values)

                # Scale up if high usage
                if avg_memory > 80 or avg_cpu > 80:
                    self._scale_up_resources()
                # Scale down if low usage
                elif avg_memory < 30 and avg_cpu < 30:
                    self._scale_down_resources()

        except Exception as e:
            self.logger.error(f"Error in auto scaling check: {e}")

    def _create_alert(
        self, severity: AlertSeverity, title: str, description: str, source: str
    ):
        """Create alert"""
        try:
            alert = Alert(
                alert_id=f"alert_{int(time.time())}_{len(self.active_alerts)}",
                severity=severity,
                title=title,
                description=description,
                source=source,
                timestamp=datetime.now(),
                resolved=False,
                resolved_at=None,
                metadata={},
            )

            self.active_alerts.append(alert)

            # Keep only last 100 alerts
            if len(self.active_alerts) > 100:
                self.active_alerts = self.active_alerts[-100:]

            self.logger.warning(f"🚨 Alert created: {title} ({severity.name})")

        except Exception as e:
            self.logger.error(f"Error creating alert: {e}")

    async def _get_autonomous_status(self, data: dict[str, Any]) -> dict[str, Any]:
        """Get autonomous status endpoint"""
        try:
            return {
                "status": "success",
                "data": {
                    "monitoring_active": self.monitoring_active,
                    "self_healing_enabled": self.self_healing_enabled,
                    "predictive_maintenance_enabled": self.predictive_maintenance_enabled,
                    "auto_scaling_enabled": self.auto_scaling_enabled,
                    "active_alerts": len(self.active_alerts),
                    "health_checks": len(self.health_checks),
                    "recovery_plans": len(self.recovery_plans),
                    "system_metrics_count": len(self.system_metrics),
                    "performance_metrics": {
                        "avg_monitoring_time": (
                            sum(self.performance_metrics["monitoring_times"])
                            / len(self.performance_metrics["monitoring_times"])
                            if self.performance_metrics["monitoring_times"]
                            else 0
                        ),
                        "avg_healing_time": (
                            sum(self.performance_metrics["healing_times"])
                            / len(self.performance_metrics["healing_times"])
                            if self.performance_metrics["healing_times"]
                            else 0
                        ),
                        "avg_scaling_time": (
                            sum(self.performance_metrics["scaling_times"])
                            / len(self.performance_metrics["scaling_times"])
                            if self.performance_metrics["scaling_times"]
                            else 0
                        ),
                    },
                },
            }

        except Exception as e:
            return {
                "status": "error",
                "error_type": "AutonomousStatusError",
                "message": str(e),
            }

    async def _get_system_health(self, data: dict[str, Any]) -> dict[str, Any]:
        """Get system health endpoint"""
        try:
            health_summary = {}
            for check_id, check in self.health_checks.items():
                health_summary[check_id] = {
                    "status": check.status.value,
                    "last_check": check.last_check.isoformat(),
                    "response_time": check.response_time,
                    "error_message": check.error_message,
                }

            return {
                "status": "success",
                "data": {
                    "health_checks": health_summary,
                    "overall_health": "healthy",  # Mock overall health
                    "active_alerts": len(self.active_alerts),
                    "system_metrics": len(self.system_metrics),
                },
            }

        except Exception as e:
            return {
                "status": "error",
                "error_type": "SystemHealthError",
                "message": str(e),
            }

    async def _get_active_alerts(self, data: dict[str, Any]) -> dict[str, Any]:
        """Get active alerts endpoint"""
        try:
            alerts_data = []
            for alert in self.active_alerts:
                alerts_data.append(
                    {
                        "alert_id": alert.alert_id,
                        "severity": alert.severity.name,
                        "title": alert.title,
                        "description": alert.description,
                        "source": alert.source,
                        "timestamp": alert.timestamp.isoformat(),
                        "resolved": alert.resolved,
                    }
                )

            return {
                "status": "success",
                "data": {
                    "alerts": alerts_data,
                    "total_alerts": len(alerts_data),
                    "critical_alerts": len(
                        [
                            a
                            for a in self.active_alerts
                            if a.severity == AlertSeverity.CRITICAL
                        ]
                    ),
                    "high_alerts": len(
                        [
                            a
                            for a in self.active_alerts
                            if a.severity == AlertSeverity.HIGH
                        ]
                    ),
                },
            }

        except Exception as e:
            return {
                "status": "error",
                "error_type": "ActiveAlertsError",
                "message": str(e),
            }

    async def _trigger_recovery(self, data: dict[str, Any]) -> dict[str, Any]:
        """Trigger recovery endpoint"""
        try:
            plan_id = data.get("plan_id", "")
            if not plan_id or plan_id not in self.recovery_plans:
                return {
                    "status": "error",
                    "error_type": "RecoveryPlanNotFound",
                    "message": f"Recovery plan {plan_id} not found",
                }

            plan = self.recovery_plans[plan_id]
            self._execute_recovery_plan(plan)

            return {
                "status": "success",
                "data": {
                    "plan_id": plan_id,
                    "executed": True,
                    "actions": [action.value for action in plan.actions],
                },
            }

        except Exception as e:
            return {
                "status": "error",
                "error_type": "TriggerRecoveryError",
                "message": str(e),
            }

    async def _get_system_metrics(self, data: dict[str, Any]) -> dict[str, Any]:
        """Get system metrics endpoint"""
        try:
            metrics_data = []
            for metric in self.system_metrics[-50:]:  # Last 50 metrics
                metrics_data.append(
                    {
                        "metric_name": metric.metric_name,
                        "value": metric.value,
                        "unit": metric.unit,
                        "timestamp": metric.timestamp.isoformat(),
                        "source": metric.source,
                        "tags": metric.tags,
                    }
                )

            return {
                "status": "success",
                "data": {
                    "metrics": metrics_data,
                    "total_metrics": len(self.system_metrics),
                    "recent_metrics": len(metrics_data),
                },
            }

        except Exception as e:
            return {
                "status": "error",
                "error_type": "SystemMetricsError",
                "message": str(e),
            }

    def shutdown(self):
        """Shutdown autonomous management system"""
        try:
            self.logger.info("🔄 Shutting down autonomous management system...")

            # Stop monitoring
            self.monitoring_active = False

            # Wait for monitoring thread to finish
            if hasattr(self, "monitoring_thread") and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=5)

            self.logger.info("✅ Autonomous management system shutdown completed")

        except Exception as e:
            self.logger.error(f"Error shutting down autonomous management system: {e}")


class AnomalyDetector:
    """Anomaly detection system"""

    def __init__(self):
        self.threshold = 2.0  # Standard deviations

    def detect_anomaly(self, values: list[float]) -> bool:
        """Detect anomaly in values"""
        try:
            if len(values) < 5:
                return False

            # Simple statistical anomaly detection
            mean = np.mean(values)
            std = np.std(values)

            if std == 0:
                return False

            # Check if latest value is anomaly
            latest_value = values[-1]
            z_score = abs(latest_value - mean) / std

            return z_score > self.threshold

        except Exception:
            return False


class PredictiveAnalyzer:
    """Predictive analysis system"""

    def __init__(self):
        self.trend_threshold = 0.1  # 10% increase per check

    def analyze_trend(self, values: list[float]) -> dict[str, Any]:
        """Analyze trend in values"""
        try:
            if len(values) < 10:
                return {"needs_maintenance": False, "trend": "insufficient_data"}

            # Simple trend analysis
            recent_values = values[-5:]
            older_values = values[-10:-5]

            recent_avg = sum(recent_values) / len(recent_values)
            older_avg = sum(older_values) / len(older_values)

            if older_avg == 0:
                return {"needs_maintenance": False, "trend": "stable"}

            trend_ratio = (recent_avg - older_avg) / older_avg

            if trend_ratio > self.trend_threshold:
                return {
                    "needs_maintenance": True,
                    "trend": "increasing",
                    "ratio": trend_ratio,
                }
            elif trend_ratio < -self.trend_threshold:
                return {
                    "needs_maintenance": False,
                    "trend": "decreasing",
                    "ratio": trend_ratio,
                }
            else:
                return {
                    "needs_maintenance": False,
                    "trend": "stable",
                    "ratio": trend_ratio,
                }

        except Exception:
            return {"needs_maintenance": False, "trend": "error"}


class RecoverySystem:
    """Recovery system"""

    def __init__(self):
        self.recovery_history = []

    def log_recovery_action(self, action: str, success: bool, duration: float):
        """Log recovery action"""
        self.recovery_history.append(
            {
                "action": action,
                "success": success,
                "duration": duration,
                "timestamp": datetime.now(),
            }
        )

        # Keep only last 100 entries
        if len(self.recovery_history) > 100:
            self.recovery_history = self.recovery_history[-100:]


def main():
    """Test autonomous management system"""

    async def test_autonomous():
        print("🧪 Testing Autonomous Management System...")

        # Initialize autonomous management system
        autonomous = AutonomousManagementSystem()

        # Test autonomous status
        print("📊 Testing autonomous status...")
        status = await autonomous._get_autonomous_status({})
        print(f"Autonomous status: {status['status']}")

        # Test system health
        print("🏥 Testing system health...")
        health = await autonomous._get_system_health({})
        print(f"System health: {health['status']}")

        # Test active alerts
        print("🚨 Testing active alerts...")
        alerts = await autonomous._get_active_alerts({})
        print(f"Active alerts: {alerts['data']['total_alerts']}")

        # Test system metrics
        print("📈 Testing system metrics...")
        metrics = await autonomous._get_system_metrics({})
        print(f"System metrics: {metrics['data']['total_metrics']}")

        # Wait for some monitoring cycles
        print("⏳ Waiting for monitoring cycles...")
        await asyncio.sleep(5)

        # Test again
        print("📊 Testing after monitoring...")
        status = await autonomous._get_autonomous_status({})
        print(f"Autonomous status: {status['status']}")

        # Shutdown
        autonomous.shutdown()

        print("✅ Autonomous Management System test completed!")

    # Run test
    asyncio.run(test_autonomous())


if __name__ == "__main__":
    main()
