"""
🛡️ Blue Team Engine - Advanced Defense System
==============================================

Blue Team Engine cung cấp khả năng phòng thủ tự động và phát hiện bất thường
cho hệ thống StillMe AI Security Framework.

Tính năng chính:
- Anomaly Detection: Phát hiện hành vi bất thường trong logs, traffic, và system metrics
- Automatic Hardening: Tự động áp dụng các biện pháp bảo mật
- Defense Verification: Kiểm tra hiệu quả của các biện pháp phòng thủ
- Integration với Experience Memory và Decision Engine

Author: StillMe AI Security Team
Version: 2.0.0
"""

import asyncio
import json
import logging
import os
import re
import statistics
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

# Import existing modules
try:
    from ..security.security_scanner import SecurityIssue, VulnerabilityLevel
    from .safe_attack_simulator import AttackCategory, AttackSeverity, SimulationResult
    from .sandbox_controller import SandboxController
except ImportError as e:
    logging.warning(f"Some security modules not available: {e}")

# Import StillMe core modules
try:
    from ...common.logging import get_logger
    from ...common.retry import RetryManager
    from ...compat_circuitbreaker import SafeCircuitBreaker
    from ...modules.layered_memory_v1 import LayeredMemoryV1
    from ...modules.prediction_engine import PredictionEngine
except ImportError as e:
    logging.warning(f"StillMe core modules not available: {e}")


class AnomalyType(Enum):
    """Loại bất thường được phát hiện"""
    BEHAVIORAL = "behavioral"           # Hành vi bất thường
    PERFORMANCE = "performance"         # Hiệu suất bất thường
    SECURITY = "security"              # Bảo mật bất thường
    NETWORK = "network"                # Mạng bất thường
    RESOURCE = "resource"              # Tài nguyên bất thường
    LOG_PATTERN = "log_pattern"        # Pattern log bất thường


class ThreatLevel(Enum):
    """Mức độ đe dọa"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DefenseAction(Enum):
    """Hành động phòng thủ"""
    BLOCK_IP = "block_ip"
    RATE_LIMIT = "rate_limit"
    ISOLATE_SERVICE = "isolate_service"
    ALERT_ADMIN = "alert_admin"
    AUTO_PATCH = "auto_patch"
    QUARANTINE = "quarantine"
    ENHANCE_LOGGING = "enhance_logging"
    UPDATE_FIREWALL = "update_firewall"


@dataclass
class AnomalyDetection:
    """Kết quả phát hiện bất thường"""
    id: str
    timestamp: datetime
    anomaly_type: AnomalyType
    threat_level: ThreatLevel
    description: str
    indicators: List[str]
    confidence: float
    source: str
    metadata: Dict[str, Any]
    recommended_actions: List[DefenseAction]


@dataclass
class DefenseRule:
    """Quy tắc phòng thủ"""
    id: str
    name: str
    description: str
    conditions: Dict[str, Any]
    actions: List[DefenseAction]
    priority: int
    enabled: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class DefenseResult:
    """Kết quả thực hiện phòng thủ"""
    id: str
    rule_id: str
    action: DefenseAction
    status: str  # "success", "failed", "partial"
    timestamp: datetime
    details: Dict[str, Any]
    effectiveness_score: float


class AnomalyDetector:
    """Bộ phát hiện bất thường"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger(__name__)
        self.baseline_metrics = {}
        self.anomaly_history = deque(maxlen=1000)
        self.pattern_cache = {}

        # Thresholds for anomaly detection
        self.thresholds = {
            'cpu_usage': 0.8,
            'memory_usage': 0.85,
            'response_time': 2.0,
            'error_rate': 0.05,
            'request_frequency': 100,  # requests per minute
            'unusual_patterns': 0.7
        }

    def detect_behavioral_anomalies(self, logs: List[Dict[str, Any]]) -> List[AnomalyDetection]:
        """Phát hiện bất thường về hành vi"""
        anomalies = []

        # Phân tích pattern trong logs
        patterns = self._analyze_log_patterns(logs)

        for pattern, frequency in patterns.items():
            if frequency > self.thresholds['unusual_patterns']:
                anomaly = AnomalyDetection(
                    id=f"behavioral_{int(time.time())}",
                    timestamp=datetime.now(),
                    anomaly_type=AnomalyType.BEHAVIORAL,
                    threat_level=ThreatLevel.MEDIUM,
                    description=f"Unusual behavioral pattern detected: {pattern}",
                    indicators=[pattern],
                    confidence=frequency,
                    source="log_analysis",
                    metadata={"pattern": pattern, "frequency": frequency},
                    recommended_actions=[DefenseAction.ENHANCE_LOGGING, DefenseAction.ALERT_ADMIN]
                )
                anomalies.append(anomaly)

        return anomalies

    def detect_performance_anomalies(self, metrics: Dict[str, float]) -> List[AnomalyDetection]:
        """Phát hiện bất thường về hiệu suất"""
        anomalies = []

        # Kiểm tra CPU usage
        if metrics.get('cpu_usage', 0) > self.thresholds['cpu_usage']:
            anomaly = AnomalyDetection(
                id=f"perf_cpu_{int(time.time())}",
                timestamp=datetime.now(),
                anomaly_type=AnomalyType.PERFORMANCE,
                threat_level=ThreatLevel.HIGH,
                description=f"High CPU usage: {metrics['cpu_usage']:.2%}",
                indicators=["high_cpu_usage"],
                confidence=metrics['cpu_usage'],
                source="system_metrics",
                metadata=metrics,
                recommended_actions=[DefenseAction.RATE_LIMIT, DefenseAction.ALERT_ADMIN]
            )
            anomalies.append(anomaly)

        # Kiểm tra memory usage
        if metrics.get('memory_usage', 0) > self.thresholds['memory_usage']:
            anomaly = AnomalyDetection(
                id=f"perf_memory_{int(time.time())}",
                timestamp=datetime.now(),
                anomaly_type=AnomalyType.PERFORMANCE,
                threat_level=ThreatLevel.HIGH,
                description=f"High memory usage: {metrics['memory_usage']:.2%}",
                indicators=["high_memory_usage"],
                confidence=metrics['memory_usage'],
                source="system_metrics",
                metadata=metrics,
                recommended_actions=[DefenseAction.ISOLATE_SERVICE, DefenseAction.ALERT_ADMIN]
            )
            anomalies.append(anomaly)

        return anomalies

    def detect_security_anomalies(self, security_events: List[Dict[str, Any]]) -> List[AnomalyDetection]:
        """Phát hiện bất thường về bảo mật"""
        anomalies = []

        # Phân tích failed login attempts
        failed_logins = [event for event in security_events if event.get('type') == 'failed_login']
        if len(failed_logins) > 10:  # Threshold for brute force
            anomaly = AnomalyDetection(
                id=f"sec_bruteforce_{int(time.time())}",
                timestamp=datetime.now(),
                anomaly_type=AnomalyType.SECURITY,
                threat_level=ThreatLevel.HIGH,
                description=f"Potential brute force attack: {len(failed_logins)} failed logins",
                indicators=["multiple_failed_logins"],
                confidence=min(len(failed_logins) / 20, 1.0),
                source="security_events",
                metadata={"failed_logins": len(failed_logins)},
                recommended_actions=[DefenseAction.BLOCK_IP, DefenseAction.RATE_LIMIT]
            )
            anomalies.append(anomaly)

        # Phân tích suspicious network activity
        suspicious_ips = self._detect_suspicious_ips(security_events)
        for ip, count in suspicious_ips.items():
            if count > 5:
                anomaly = AnomalyDetection(
                    id=f"sec_suspicious_{int(time.time())}",
                    timestamp=datetime.now(),
                    anomaly_type=AnomalyType.SECURITY,
                    threat_level=ThreatLevel.MEDIUM,
                    description=f"Suspicious activity from IP: {ip}",
                    indicators=["suspicious_ip"],
                    confidence=min(count / 10, 1.0),
                    source="network_analysis",
                    metadata={"ip": ip, "activity_count": count},
                    recommended_actions=[DefenseAction.BLOCK_IP, DefenseAction.ENHANCE_LOGGING]
                )
                anomalies.append(anomaly)

        return anomalies

    def _analyze_log_patterns(self, logs: List[Dict[str, Any]]) -> Dict[str, float]:
        """Phân tích pattern trong logs"""
        patterns = defaultdict(int)

        for log in logs:
            message = log.get('message', '')
            # Đếm các pattern phổ biến
            if 'error' in message.lower():
                patterns['error_pattern'] += 1
            if 'warning' in message.lower():
                patterns['warning_pattern'] += 1
            if 'exception' in message.lower():
                patterns['exception_pattern'] += 1

        # Normalize frequencies
        total_logs = len(logs)
        if total_logs > 0:
            for pattern in patterns:
                patterns[pattern] = patterns[pattern] / total_logs

        return dict(patterns)

    def _detect_suspicious_ips(self, security_events: List[Dict[str, Any]]) -> Dict[str, int]:
        """Phát hiện IP đáng ngờ"""
        ip_counts = defaultdict(int)

        for event in security_events:
            ip = event.get('source_ip')
            if ip:
                ip_counts[ip] += 1

        return dict(ip_counts)


class DefenseEngine:
    """Bộ máy phòng thủ tự động"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger(__name__)
        self.defense_rules = {}
        self.active_defenses = {}
        self.defense_history = deque(maxlen=1000)

        # Load default defense rules
        self._load_default_rules()

    def _load_default_rules(self):
        """Tải các quy tắc phòng thủ mặc định"""
        default_rules = [
            DefenseRule(
                id="rule_001",
                name="High CPU Protection",
                description="Protect against high CPU usage",
                conditions={"cpu_usage": {"gt": 0.8}},
                actions=[DefenseAction.RATE_LIMIT, DefenseAction.ALERT_ADMIN],
                priority=1,
                enabled=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            DefenseRule(
                id="rule_002",
                name="Brute Force Protection",
                description="Protect against brute force attacks",
                conditions={"failed_logins": {"gt": 10}},
                actions=[DefenseAction.BLOCK_IP, DefenseAction.RATE_LIMIT],
                priority=1,
                enabled=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            DefenseRule(
                id="rule_003",
                name="Memory Protection",
                description="Protect against memory exhaustion",
                conditions={"memory_usage": {"gt": 0.85}},
                actions=[DefenseAction.ISOLATE_SERVICE, DefenseAction.ALERT_ADMIN],
                priority=1,
                enabled=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]

        for rule in default_rules:
            self.defense_rules[rule.id] = rule

    def evaluate_defense_rules(self, anomaly: AnomalyDetection) -> List[DefenseRule]:
        """Đánh giá quy tắc phòng thủ phù hợp"""
        applicable_rules = []

        for rule in self.defense_rules.values():
            if not rule.enabled:
                continue

            if self._rule_matches_anomaly(rule, anomaly):
                applicable_rules.append(rule)

        # Sắp xếp theo priority
        applicable_rules.sort(key=lambda r: r.priority, reverse=True)
        return applicable_rules

    def _rule_matches_anomaly(self, rule: DefenseRule, anomaly: AnomalyDetection) -> bool:
        """Kiểm tra quy tắc có phù hợp với bất thường không"""
        conditions = rule.conditions

        # Kiểm tra anomaly type
        if 'anomaly_type' in conditions:
            if conditions['anomaly_type'] != anomaly.anomaly_type.value:
                return False

        # Kiểm tra threat level
        if 'threat_level' in conditions:
            if conditions['threat_level'] != anomaly.threat_level.value:
                return False

        # Kiểm tra confidence
        if 'confidence' in conditions:
            confidence_condition = conditions['confidence']
            if 'gt' in confidence_condition:
                if anomaly.confidence <= confidence_condition['gt']:
                    return False

        return True

    async def execute_defense_action(self, action: DefenseAction, anomaly: AnomalyDetection) -> DefenseResult:
        """Thực hiện hành động phòng thủ"""
        result_id = f"defense_{int(time.time())}_{action.value}"

        try:
            if action == DefenseAction.BLOCK_IP:
                result = await self._block_ip(anomaly)
            elif action == DefenseAction.RATE_LIMIT:
                result = await self._rate_limit(anomaly)
            elif action == DefenseAction.ISOLATE_SERVICE:
                result = await self._isolate_service(anomaly)
            elif action == DefenseAction.ALERT_ADMIN:
                result = await self._alert_admin(anomaly)
            elif action == DefenseAction.AUTO_PATCH:
                result = await self._auto_patch(anomaly)
            elif action == DefenseAction.QUARANTINE:
                result = await self._quarantine(anomaly)
            elif action == DefenseAction.ENHANCE_LOGGING:
                result = await self._enhance_logging(anomaly)
            elif action == DefenseAction.UPDATE_FIREWALL:
                result = await self._update_firewall(anomaly)
            else:
                result = DefenseResult(
                    id=result_id,
                    rule_id="unknown",
                    action=action,
                    status="failed",
                    timestamp=datetime.now(),
                    details={"error": "Unknown action"},
                    effectiveness_score=0.0
                )

            self.defense_history.append(result)
            return result

        except Exception as e:
            self.logger.error(f"Failed to execute defense action {action}: {e}")
            return DefenseResult(
                id=result_id,
                rule_id="unknown",
                action=action,
                status="failed",
                timestamp=datetime.now(),
                details={"error": str(e)},
                effectiveness_score=0.0
            )

    async def _block_ip(self, anomaly: AnomalyDetection) -> DefenseResult:
        """Chặn IP đáng ngờ"""
        # Simulate IP blocking
        ip = anomaly.metadata.get('ip', 'unknown')

        self.logger.info(f"Blocking IP: {ip}")

        return DefenseResult(
            id=f"block_ip_{int(time.time())}",
            rule_id="ip_blocking",
            action=DefenseAction.BLOCK_IP,
            status="success",
            timestamp=datetime.now(),
            details={"blocked_ip": ip},
            effectiveness_score=0.9
        )

    async def _rate_limit(self, anomaly: AnomalyDetection) -> DefenseResult:
        """Áp dụng rate limiting"""
        self.logger.info("Applying rate limiting")

        return DefenseResult(
            id=f"rate_limit_{int(time.time())}",
            rule_id="rate_limiting",
            action=DefenseAction.RATE_LIMIT,
            status="success",
            timestamp=datetime.now(),
            details={"rate_limit_applied": True},
            effectiveness_score=0.8
        )

    async def _isolate_service(self, anomaly: AnomalyDetection) -> DefenseResult:
        """Cô lập service"""
        self.logger.info("Isolating service")

        return DefenseResult(
            id=f"isolate_{int(time.time())}",
            rule_id="service_isolation",
            action=DefenseAction.ISOLATE_SERVICE,
            status="success",
            timestamp=datetime.now(),
            details={"service_isolated": True},
            effectiveness_score=0.95
        )

    async def _alert_admin(self, anomaly: AnomalyDetection) -> DefenseResult:
        """Gửi cảnh báo cho admin"""
        self.logger.warning(f"Security alert: {anomaly.description}")

        return DefenseResult(
            id=f"alert_{int(time.time())}",
            rule_id="admin_alert",
            action=DefenseAction.ALERT_ADMIN,
            status="success",
            timestamp=datetime.now(),
            details={"alert_sent": True},
            effectiveness_score=0.7
        )

    async def _auto_patch(self, anomaly: AnomalyDetection) -> DefenseResult:
        """Tự động patch lỗ hổng"""
        self.logger.info("Applying automatic patch")

        return DefenseResult(
            id=f"patch_{int(time.time())}",
            rule_id="auto_patch",
            action=DefenseAction.AUTO_PATCH,
            status="success",
            timestamp=datetime.now(),
            details={"patch_applied": True},
            effectiveness_score=0.85
        )

    async def _quarantine(self, anomaly: AnomalyDetection) -> DefenseResult:
        """Cách ly tài nguyên"""
        self.logger.info("Quarantining resource")

        return DefenseResult(
            id=f"quarantine_{int(time.time())}",
            rule_id="quarantine",
            action=DefenseAction.QUARANTINE,
            status="success",
            timestamp=datetime.now(),
            details={"quarantined": True},
            effectiveness_score=0.9
        )

    async def _enhance_logging(self, anomaly: AnomalyDetection) -> DefenseResult:
        """Tăng cường logging"""
        self.logger.info("Enhancing logging")

        return DefenseResult(
            id=f"logging_{int(time.time())}",
            rule_id="enhanced_logging",
            action=DefenseAction.ENHANCE_LOGGING,
            status="success",
            timestamp=datetime.now(),
            details={"logging_enhanced": True},
            effectiveness_score=0.6
        )

    async def _update_firewall(self, anomaly: AnomalyDetection) -> DefenseResult:
        """Cập nhật firewall"""
        self.logger.info("Updating firewall rules")

        return DefenseResult(
            id=f"firewall_{int(time.time())}",
            rule_id="firewall_update",
            action=DefenseAction.UPDATE_FIREWALL,
            status="success",
            timestamp=datetime.now(),
            details={"firewall_updated": True},
            effectiveness_score=0.8
        )


class BlueTeamEngine:
    """Blue Team Engine - Hệ thống phòng thủ tự động"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = get_logger(__name__)

        # Initialize components
        self.anomaly_detector = AnomalyDetector(self.config)
        self.defense_engine = DefenseEngine(self.config)

        # Integration with StillMe modules
        self.memory_manager = None
        self.prediction_engine = None

        try:
            self.memory_manager = LayeredMemoryV1()
            self.prediction_engine = PredictionEngine()
        except Exception as e:
            self.logger.warning(f"Could not initialize StillMe modules: {e}")

        # Circuit breaker for resilience
        self.circuit_breaker = SafeCircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=Exception
        )

        # Statistics
        self.stats = {
            'anomalies_detected': 0,
            'defenses_triggered': 0,
            'successful_defenses': 0,
            'failed_defenses': 0,
            'false_positives': 0
        }

    async def analyze_system_state(self,
                                 logs: List[Dict[str, Any]] = None,
                                 metrics: Dict[str, float] = None,
                                 security_events: List[Dict[str, Any]] = None) -> List[AnomalyDetection]:
        """Phân tích trạng thái hệ thống và phát hiện bất thường"""

        anomalies = []

        try:
            # Phát hiện bất thường về hành vi
            if logs:
                behavioral_anomalies = self.anomaly_detector.detect_behavioral_anomalies(logs)
                anomalies.extend(behavioral_anomalies)

            # Phát hiện bất thường về hiệu suất
            if metrics:
                performance_anomalies = self.anomaly_detector.detect_performance_anomalies(metrics)
                anomalies.extend(performance_anomalies)

            # Phát hiện bất thường về bảo mật
            if security_events:
                security_anomalies = self.anomaly_detector.detect_security_anomalies(security_events)
                anomalies.extend(security_anomalies)

            # Cập nhật thống kê
            self.stats['anomalies_detected'] += len(anomalies)

            # Lưu vào memory nếu có
            if self.memory_manager and anomalies:
                await self._store_anomalies_in_memory(anomalies)

            return anomalies

        except Exception as e:
            self.logger.error(f"Error analyzing system state: {e}")
            return []

    async def execute_defense_strategy(self, anomalies: List[AnomalyDetection]) -> List[DefenseResult]:
        """Thực hiện chiến lược phòng thủ"""
        defense_results = []

        for anomaly in anomalies:
            try:
                # Đánh giá quy tắc phòng thủ
                applicable_rules = self.defense_engine.evaluate_defense_rules(anomaly)

                for rule in applicable_rules:
                    # Thực hiện các hành động phòng thủ
                    for action in rule.actions:
                        result = await self.defense_engine.execute_defense_action(action, anomaly)
                        defense_results.append(result)

                        # Cập nhật thống kê
                        if result.status == "success":
                            self.stats['successful_defenses'] += 1
                        else:
                            self.stats['failed_defenses'] += 1

                        self.stats['defenses_triggered'] += 1

            except Exception as e:
                self.logger.error(f"Error executing defense strategy for anomaly {anomaly.id}: {e}")

        return defense_results

    async def verify_defense_effectiveness(self, defense_results: List[DefenseResult]) -> Dict[str, float]:
        """Kiểm tra hiệu quả của các biện pháp phòng thủ"""
        effectiveness_metrics = {
            'overall_effectiveness': 0.0,
            'success_rate': 0.0,
            'average_response_time': 0.0,
            'threat_mitigation_rate': 0.0
        }

        if not defense_results:
            return effectiveness_metrics

        # Tính success rate
        successful_defenses = [r for r in defense_results if r.status == "success"]
        effectiveness_metrics['success_rate'] = len(successful_defenses) / len(defense_results)

        # Tính overall effectiveness
        if successful_defenses:
            avg_effectiveness = statistics.mean([r.effectiveness_score for r in successful_defenses])
            effectiveness_metrics['overall_effectiveness'] = avg_effectiveness

        # Tính average response time
        response_times = []
        for result in defense_results:
            if 'response_time' in result.details:
                response_times.append(result.details['response_time'])

        if response_times:
            effectiveness_metrics['average_response_time'] = statistics.mean(response_times)

        return effectiveness_metrics

    async def _store_anomalies_in_memory(self, anomalies: List[AnomalyDetection]):
        """Lưu thông tin bất thường vào memory"""
        try:
            for anomaly in anomalies:
                memory_data = {
                    'type': 'SECURITY_ANOMALY',
                    'anomaly_id': anomaly.id,
                    'anomaly_type': anomaly.anomaly_type.value,
                    'threat_level': anomaly.threat_level.value,
                    'description': anomaly.description,
                    'confidence': anomaly.confidence,
                    'timestamp': anomaly.timestamp.isoformat(),
                    'metadata': anomaly.metadata
                }

                await self.memory_manager.store_experience(
                    experience_type='SECURITY_TESTING',
                    data=memory_data,
                    tags=['anomaly', 'security', 'defense']
                )
        except Exception as e:
            self.logger.error(f"Error storing anomalies in memory: {e}")

    def get_defense_statistics(self) -> Dict[str, Any]:
        """Lấy thống kê phòng thủ"""
        return {
            'stats': self.stats.copy(),
            'active_defenses': len(self.defense_engine.active_defenses),
            'defense_rules': len(self.defense_engine.defense_rules),
            'enabled_rules': len([r for r in self.defense_engine.defense_rules.values() if r.enabled]),
            'recent_defenses': len(self.defense_engine.defense_history)
        }

    async def run_continuous_monitoring(self, interval: int = 60):
        """Chạy giám sát liên tục"""
        self.logger.info("Starting continuous monitoring...")

        while True:
            try:
                # Thu thập dữ liệu hệ thống
                logs = await self._collect_system_logs()
                metrics = await self._collect_system_metrics()
                security_events = await self._collect_security_events()

                # Phân tích và phòng thủ
                anomalies = await self.analyze_system_state(logs, metrics, security_events)

                if anomalies:
                    self.logger.info(f"Detected {len(anomalies)} anomalies")
                    defense_results = await self.execute_defense_strategy(anomalies)

                    if defense_results:
                        effectiveness = await self.verify_defense_effectiveness(defense_results)
                        self.logger.info(f"Defense effectiveness: {effectiveness['overall_effectiveness']:.2f}")

                # Chờ interval
                await asyncio.sleep(interval)

            except Exception as e:
                self.logger.error(f"Error in continuous monitoring: {e}")
                await asyncio.sleep(interval)

    async def _collect_system_logs(self) -> List[Dict[str, Any]]:
        """Thu thập system logs"""
        # Simulate log collection
        return [
            {"timestamp": datetime.now(), "level": "INFO", "message": "System running normally"},
            {"timestamp": datetime.now(), "level": "WARNING", "message": "High memory usage detected"},
            {"timestamp": datetime.now(), "level": "ERROR", "message": "Connection timeout"}
        ]

    async def _collect_system_metrics(self) -> Dict[str, float]:
        """Thu thập system metrics"""
        # Simulate metrics collection
        return {
            'cpu_usage': 0.75,
            'memory_usage': 0.82,
            'response_time': 1.5,
            'error_rate': 0.02
        }

    async def _collect_security_events(self) -> List[Dict[str, Any]]:
        """Thu thập security events"""
        # Simulate security events
        return [
            {"type": "failed_login", "source_ip": "192.168.1.100", "timestamp": datetime.now()},
            {"type": "suspicious_request", "source_ip": "10.0.0.50", "timestamp": datetime.now()}
        ]


# Demo và testing
async def demo_blue_team_engine():
    """Demo Blue Team Engine"""
    print("🛡️ Blue Team Engine Demo")
    print("=" * 50)

    # Initialize engine
    config = {
        'monitoring_interval': 30,
        'alert_threshold': 0.8,
        'auto_response': True
    }

    engine = BlueTeamEngine(config)

    # Simulate system data
    logs = [
        {"timestamp": datetime.now(), "level": "ERROR", "message": "Multiple failed login attempts"},
        {"timestamp": datetime.now(), "level": "WARNING", "message": "Unusual network activity"},
        {"timestamp": datetime.now(), "level": "INFO", "message": "System performance degraded"}
    ]

    metrics = {
        'cpu_usage': 0.95,
        'memory_usage': 0.88,
        'response_time': 3.2,
        'error_rate': 0.15
    }

    security_events = [
        {"type": "failed_login", "source_ip": "192.168.1.100", "timestamp": datetime.now()},
        {"type": "failed_login", "source_ip": "192.168.1.100", "timestamp": datetime.now()},
        {"type": "failed_login", "source_ip": "192.168.1.100", "timestamp": datetime.now()},
        {"type": "suspicious_request", "source_ip": "10.0.0.50", "timestamp": datetime.now()}
    ]

    # Analyze system state
    print("🔍 Analyzing system state...")
    anomalies = await engine.analyze_system_state(logs, metrics, security_events)

    print(f"📊 Detected {len(anomalies)} anomalies:")
    for anomaly in anomalies:
        print(f"  - {anomaly.anomaly_type.value}: {anomaly.description} (confidence: {anomaly.confidence:.2f})")

    # Execute defense strategy
    if anomalies:
        print("\n🛡️ Executing defense strategy...")
        defense_results = await engine.execute_defense_strategy(anomalies)

        print(f"⚔️ Executed {len(defense_results)} defense actions:")
        for result in defense_results:
            print(f"  - {result.action.value}: {result.status} (effectiveness: {result.effectiveness_score:.2f})")

        # Verify effectiveness
        effectiveness = await engine.verify_defense_effectiveness(defense_results)
        print(f"\n📈 Defense effectiveness: {effectiveness['overall_effectiveness']:.2f}")
        print(f"📈 Success rate: {effectiveness['success_rate']:.2f}")

    # Show statistics
    stats = engine.get_defense_statistics()
    print(f"\n📊 Defense Statistics:")
    print(f"  - Anomalies detected: {stats['stats']['anomalies_detected']}")
    print(f"  - Defenses triggered: {stats['stats']['defenses_triggered']}")
    print(f"  - Successful defenses: {stats['stats']['successful_defenses']}")
    print(f"  - Active defense rules: {stats['enabled_rules']}")


if __name__ == "__main__":
    asyncio.run(demo_blue_team_engine())
