#!/usr/bin/env python3
"""
StillMe AgentDev - Runtime Protection
Enterprise-grade runtime security monitoring and protection
"""

import asyncio
import json
import time
import psutil
import subprocess
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import aiofiles
from pathlib import Path
import hashlib
import re

class ThreatLevel(Enum):
    """Threat severity levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class SecurityEvent(Enum):
    """Security event types"""
    PROCESS_INJECTION = "process_injection"
    MEMORY_ANOMALY = "memory_anomaly"
    NETWORK_ANOMALY = "network_anomaly"
    FILE_ACCESS_VIOLATION = "file_access_violation"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    SUSPICIOUS_COMMAND = "suspicious_command"
    RESOURCE_ABUSE = "resource_abuse"
    CODE_INJECTION = "code_injection"

@dataclass
class SecurityAlert:
    """Security alert data structure"""
    alert_id: str
    event_type: SecurityEvent
    threat_level: ThreatLevel
    timestamp: float
    source: str
    description: str
    details: Dict[str, Any]
    mitigation_applied: bool = False
    false_positive: bool = False

@dataclass
class ProcessProfile:
    """Process security profile"""
    pid: int
    name: str
    cmdline: str
    memory_usage: float
    cpu_usage: float
    file_descriptors: int
    network_connections: int
    suspicious_score: float
    baseline_hash: str

class RuntimeProtection:
    """Enterprise runtime protection system"""

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.alerts: List[SecurityAlert] = []
        self.process_profiles: Dict[int, ProcessProfile] = {}
        self.baseline_processes: Dict[str, str] = {}
        self.suspicious_patterns = self._load_suspicious_patterns()
        self.monitoring_active = False
        self.alert_callbacks: List[Callable[[SecurityAlert], None]] = []
        self.lock = threading.RLock()

    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load runtime protection configuration"""
        if config_path:
            config_file = Path(config_path)
        else:
            config_file = Path("agent-dev/config/runtime_protection.yaml")

        if config_file.exists():
            import yaml
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        else:
            return {
                'monitoring': {
                    'process_monitoring': True,
                    'memory_monitoring': True,
                    'network_monitoring': True,
                    'file_monitoring': True,
                    'interval': 5.0
                },
                'thresholds': {
                    'memory_usage_percent': 80.0,
                    'cpu_usage_percent': 90.0,
                    'file_descriptors': 1000,
                    'network_connections': 100
                },
                'protection': {
                    'auto_mitigation': True,
                    'process_termination': False,
                    'network_blocking': False,
                    'file_quarantine': True
                }
            }

    def _load_suspicious_patterns(self) -> Dict[str, List[str]]:
        """Load suspicious command and behavior patterns"""
        return {
            'suspicious_commands': [
                r'rm\s+-rf\s+/',
                r'mkfs\.',
                r'dd\s+if=.*of=/dev/',
                r'chmod\s+777',
                r'wget\s+.*\|\s*sh',
                r'curl\s+.*\|\s*sh',
                r'nc\s+-l\s+-p',
                r'netcat\s+-l\s+-p',
                r'python\s+-c\s+.*exec',
                r'perl\s+-e\s+.*system',
                r'bash\s+-i\s+>&\s*/dev/tcp/',
                r'powershell\s+-enc',
                r'certutil\s+-decode',
                r'reg\s+add\s+.*HKLM',
                r'schtasks\s+/create'
            ],
            'suspicious_files': [
                r'\.exe$',
                r'\.bat$',
                r'\.cmd$',
                r'\.ps1$',
                r'\.sh$',
                r'\.py$',
                r'\.js$',
                r'\.vbs$'
            ],
            'suspicious_network': [
                r'192\.168\.',
                r'10\.',
                r'172\.(1[6-9]|2[0-9]|3[0-1])\.',
                r'localhost',
                r'127\.0\.0\.1'
            ]
        }

    def register_alert_callback(self, callback: Callable[[SecurityAlert], None]):
        """Register callback for security alerts"""
        self.alert_callbacks.append(callback)

    def _create_alert(self, event_type: SecurityEvent, threat_level: ThreatLevel,
                     source: str, description: str, details: Dict[str, Any]) -> SecurityAlert:
        """Create a security alert"""
        alert = SecurityAlert(
            alert_id=f"alert_{int(time.time())}_{hash(description) % 10000}",
            event_type=event_type,
            threat_level=threat_level,
            timestamp=time.time(),
            source=source,
            description=description,
            details=details
        )

        with self.lock:
            self.alerts.append(alert)

        # Notify callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                print(f"⚠️ Alert callback error: {e}")

        return alert

    def _analyze_process(self, process: psutil.Process) -> Optional[SecurityAlert]:
        """Analyze process for suspicious behavior"""
        try:
            # Get process information
            cmdline = ' '.join(process.cmdline())
            memory_info = process.memory_info()
            cpu_percent = process.cpu_percent()

            # Check for suspicious commands
            for pattern in self.suspicious_patterns['suspicious_commands']:
                if re.search(pattern, cmdline, re.IGNORECASE):
                    return self._create_alert(
                        event_type=SecurityEvent.SUSPICIOUS_COMMAND,
                        threat_level=ThreatLevel.HIGH,
                        source=f"process_{process.pid}",
                        description=f"Suspicious command detected: {cmdline}",
                        details={
                            'pid': process.pid,
                            'cmdline': cmdline,
                            'pattern': pattern,
                            'memory_usage': memory_info.rss,
                            'cpu_usage': cpu_percent
                        }
                    )

            # Check resource usage
            memory_percent = process.memory_percent()
            if memory_percent > self.config['thresholds']['memory_usage_percent']:
                return self._create_alert(
                    event_type=SecurityEvent.RESOURCE_ABUSE,
                    threat_level=ThreatLevel.MEDIUM,
                    source=f"process_{process.pid}",
                    description=f"High memory usage: {memory_percent:.1f}%",
                    details={
                        'pid': process.pid,
                        'name': process.name(),
                        'memory_percent': memory_percent,
                        'memory_rss': memory_info.rss,
                        'threshold': self.config['thresholds']['memory_usage_percent']
                    }
                )

            if cpu_percent > self.config['thresholds']['cpu_usage_percent']:
                return self._create_alert(
                    event_type=SecurityEvent.RESOURCE_ABUSE,
                    threat_level=ThreatLevel.MEDIUM,
                    source=f"process_{process.pid}",
                    description=f"High CPU usage: {cpu_percent:.1f}%",
                    details={
                        'pid': process.pid,
                        'name': process.name(),
                        'cpu_percent': cpu_percent,
                        'threshold': self.config['thresholds']['cpu_usage_percent']
                    }
                )

            # Check file descriptors
            try:
                num_fds = process.num_fds() if hasattr(process, 'num_fds') else len(process.open_files())
                if num_fds > self.config['thresholds']['file_descriptors']:
                    return self._create_alert(
                        event_type=SecurityEvent.RESOURCE_ABUSE,
                        threat_level=ThreatLevel.MEDIUM,
                        source=f"process_{process.pid}",
                        description=f"High file descriptor usage: {num_fds}",
                        details={
                            'pid': process.pid,
                            'name': process.name(),
                            'file_descriptors': num_fds,
                            'threshold': self.config['thresholds']['file_descriptors']
                        }
                    )
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass

            # Check network connections
            try:
                connections = process.connections()
                if len(connections) > self.config['thresholds']['network_connections']:
                    return self._create_alert(
                        event_type=SecurityEvent.NETWORK_ANOMALY,
                        threat_level=ThreatLevel.MEDIUM,
                        source=f"process_{process.pid}",
                        description=f"High network connections: {len(connections)}",
                        details={
                            'pid': process.pid,
                            'name': process.name(),
                            'connections': len(connections),
                            'threshold': self.config['thresholds']['network_connections']
                        }
                    )
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass

        except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
            pass

        return None

    def _monitor_processes(self):
        """Monitor running processes for security threats"""
        try:
            for process in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'cpu_percent']):
                try:
                    alert = self._analyze_process(process)
                    if alert:
                        print(f"🚨 Security Alert: {alert.description}")

                        # Apply mitigation if configured
                        if self.config['protection']['auto_mitigation']:
                            self._apply_mitigation(alert)

                except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
                    continue

        except Exception as e:
            print(f"⚠️ Process monitoring error: {e}")

    def _apply_mitigation(self, alert: SecurityAlert):
        """Apply security mitigation measures"""
        try:
            if alert.event_type == SecurityEvent.SUSPICIOUS_COMMAND:
                if self.config['protection']['process_termination']:
                    pid = alert.details.get('pid')
                    if pid:
                        try:
                            process = psutil.Process(pid)
                            process.terminate()
                            print(f"🛑 Terminated suspicious process: {pid}")
                        except (psutil.AccessDenied, psutil.NoSuchProcess):
                            pass

            elif alert.event_type == SecurityEvent.RESOURCE_ABUSE:
                # Log resource abuse for investigation
                print(f"📊 Resource abuse logged: {alert.description}")

            elif alert.event_type == SecurityEvent.NETWORK_ANOMALY:
                if self.config['protection']['network_blocking']:
                    print(f"🚫 Network anomaly detected: {alert.description}")
                    # TODO: Implement network blocking

            alert.mitigation_applied = True

        except Exception as e:
            print(f"⚠️ Mitigation error: {e}")

    def _monitor_memory(self):
        """Monitor system memory for anomalies"""
        try:
            memory = psutil.virtual_memory()

            if memory.percent > 90:
                self._create_alert(
                    event_type=SecurityEvent.MEMORY_ANOMALY,
                    threat_level=ThreatLevel.HIGH,
                    source="system_memory",
                    description=f"Critical memory usage: {memory.percent:.1f}%",
                    details={
                        'total': memory.total,
                        'available': memory.available,
                        'percent': memory.percent,
                        'used': memory.used
                    }
                )

        except Exception as e:
            print(f"⚠️ Memory monitoring error: {e}")

    def _monitor_network(self):
        """Monitor network activity for anomalies"""
        try:
            connections = psutil.net_connections()
            suspicious_connections = []

            for conn in connections:
                if conn.raddr and conn.raddr.ip:
                    # Check for suspicious IP patterns
                    for pattern in self.suspicious_patterns['suspicious_network']:
                        if re.search(pattern, conn.raddr.ip):
                            suspicious_connections.append(conn)

            if suspicious_connections:
                self._create_alert(
                    event_type=SecurityEvent.NETWORK_ANOMALY,
                    threat_level=ThreatLevel.MEDIUM,
                    source="network_monitor",
                    description=f"Suspicious network connections detected: {len(suspicious_connections)}",
                    details={
                        'suspicious_connections': [
                            {
                                'local': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
                                'remote': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                                'status': conn.status,
                                'pid': conn.pid
                            }
                            for conn in suspicious_connections
                        ]
                    }
                )

        except Exception as e:
            print(f"⚠️ Network monitoring error: {e}")

    async def start_monitoring(self):
        """Start runtime protection monitoring"""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        print("🛡️ Runtime Protection monitoring started")

        # Start monitoring loop
        while self.monitoring_active:
            try:
                if self.config['monitoring']['process_monitoring']:
                    self._monitor_processes()

                if self.config['monitoring']['memory_monitoring']:
                    self._monitor_memory()

                if self.config['monitoring']['network_monitoring']:
                    self._monitor_network()

                await asyncio.sleep(self.config['monitoring']['interval'])

            except Exception as e:
                print(f"⚠️ Monitoring loop error: {e}")
                await asyncio.sleep(5)

    def stop_monitoring(self):
        """Stop runtime protection monitoring"""
        self.monitoring_active = False
        print("🛑 Runtime Protection monitoring stopped")

    def get_security_report(self) -> Dict[str, Any]:
        """Get comprehensive security report"""
        with self.lock:
            total_alerts = len(self.alerts)
            alerts_by_level = {}
            alerts_by_type = {}

            for alert in self.alerts:
                # Count by threat level
                level = alert.threat_level.value
                alerts_by_level[level] = alerts_by_level.get(level, 0) + 1

                # Count by event type
                event_type = alert.event_type.value
                alerts_by_type[event_type] = alerts_by_type.get(event_type, 0) + 1

            return {
                'total_alerts': total_alerts,
                'alerts_by_level': alerts_by_level,
                'alerts_by_type': alerts_by_type,
                'monitoring_active': self.monitoring_active,
                'recent_alerts': [
                    {
                        'alert_id': alert.alert_id,
                        'event_type': alert.event_type.value,
                        'threat_level': alert.threat_level.value,
                        'timestamp': alert.timestamp,
                        'description': alert.description,
                        'mitigation_applied': alert.mitigation_applied
                    }
                    for alert in self.alerts[-10:]  # Last 10 alerts
                ]
            }

    async def export_alerts(self, file_path: str):
        """Export security alerts to file"""
        try:
            alerts_data = [asdict(alert) for alert in self.alerts]

            async with aiofiles.open(file_path, 'w') as f:
                await f.write(json.dumps(alerts_data, indent=2))

            print(f"📄 Security alerts exported to: {file_path}")

        except Exception as e:
            print(f"⚠️ Failed to export alerts: {e}")

# Global runtime protection instance
runtime_protection = RuntimeProtection()

# Convenience functions
async def start_runtime_protection():
    """Start runtime protection monitoring"""
    await runtime_protection.start_monitoring()

def stop_runtime_protection():
    """Stop runtime protection monitoring"""
    runtime_protection.stop_monitoring()

def register_security_alert_handler(handler: Callable[[SecurityAlert], None]):
    """Register security alert handler"""
    runtime_protection.register_alert_callback(handler)

def get_security_status() -> Dict[str, Any]:
    """Get current security status"""
    return runtime_protection.get_security_report()

if __name__ == "__main__":
    async def main():
        # Example usage
        protection = RuntimeProtection()

        # Register alert handler
        def alert_handler(alert: SecurityAlert):
            print(f"🚨 ALERT: {alert.threat_level.value} - {alert.description}")

        protection.register_alert_callback(alert_handler)

        # Start monitoring
        await protection.start_monitoring()

        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            protection.stop_monitoring()

    asyncio.run(main())
