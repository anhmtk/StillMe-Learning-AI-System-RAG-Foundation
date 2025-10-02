"""Security Manager for StillMe Framework"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SecurityEvent(Enum):
    LOGIN_ATTEMPT = "login_attempt"
    PERMISSION_DENIED = "permission_denied"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    DATA_BREACH = "data_breach"
    SYSTEM_COMPROMISE = "system_compromise"

@dataclass
class SecurityIncident:
    """Security incident record"""
    incident_id: str
    event_type: SecurityEvent
    security_level: SecurityLevel
    description: str
    source_ip: Optional[str] = None
    user_id: Optional[str] = None
    timestamp: datetime = None
    resolved: bool = False
    resolution: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}

class SecurityManager:
    """Security manager for StillMe Framework"""

    def __init__(self):
        self.logger = logger
        self.incidents: List[SecurityIncident] = []
        self.security_policies = self._initialize_security_policies()
        self.logger.info("✅ SecurityManager initialized")

    def _initialize_security_policies(self) -> Dict[str, Any]:
        """Initialize security policies"""
        return {
            "max_login_attempts": 5,
            "lockout_duration": 300,  # 5 minutes
            "session_timeout": 3600,  # 1 hour
            "password_min_length": 8,
            "require_2fa": False,
            "audit_logging": True,
            "encryption_required": True,
            "data_retention_days": 90
        }

    def log_security_event(self,
                          event_type: SecurityEvent,
                          description: str,
                          security_level: SecurityLevel = SecurityLevel.MEDIUM,
                          source_ip: Optional[str] = None,
                          user_id: Optional[str] = None,
                          metadata: Dict[str, Any] = None) -> SecurityIncident:
        """Log a security event"""
        try:
            incident_id = f"incident_{len(self.incidents) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            incident = SecurityIncident(
                incident_id=incident_id,
                event_type=event_type,
                security_level=security_level,
                description=description,
                source_ip=source_ip,
                user_id=user_id,
                timestamp=datetime.now(),
                metadata=metadata or {}
            )

            self.incidents.append(incident)

            # Log the incident
            level_icon = "🔒" if security_level == SecurityLevel.CRITICAL else "⚠️"
            self.logger.warning(f"{level_icon} Security incident: {event_type.value} - {description}")

            # Check if immediate action is required
            if security_level == SecurityLevel.CRITICAL:
                self._handle_critical_incident(incident)

            return incident

        except Exception as e:
            self.logger.error(f"❌ Failed to log security event: {e}")
            raise

    def _handle_critical_incident(self, incident: SecurityIncident):
        """Handle critical security incidents"""
        try:
            self.logger.critical(f"🚨 CRITICAL SECURITY INCIDENT: {incident.incident_id}")

            # In a real implementation, this would:
            # 1. Send alerts to security team
            # 2. Activate incident response procedures
            # 3. Implement emergency security measures
            # 4. Notify relevant stakeholders

            # For now, we'll just log the critical incident
            self.logger.critical(f"Critical incident details: {incident.description}")

        except Exception as e:
            self.logger.error(f"❌ Failed to handle critical incident: {e}")

    def check_security_policy(self, policy_name: str, value: Any) -> bool:
        """Check if a value complies with security policy"""
        try:
            if policy_name not in self.security_policies:
                self.logger.warning(f"⚠️ Unknown security policy: {policy_name}")
                return True  # Allow unknown policies to pass

            policy_value = self.security_policies[policy_name]

            if policy_name == "password_min_length":
                return len(str(value)) >= policy_value
            elif policy_name == "max_login_attempts":
                return int(value) <= policy_value
            elif policy_name == "session_timeout":
                return int(value) <= policy_value
            elif policy_name == "data_retention_days":
                return int(value) <= policy_value
            else:
                # For boolean policies
                return bool(value) == bool(policy_value)

        except Exception as e:
            self.logger.error(f"❌ Failed to check security policy: {e}")
            return False

    def update_security_policy(self, policy_name: str, value: Any):
        """Update a security policy"""
        try:
            if policy_name in self.security_policies:
                old_value = self.security_policies[policy_name]
                self.security_policies[policy_name] = value
                self.logger.info(f"📝 Security policy updated: {policy_name} = {value} (was {old_value})")
            else:
                self.security_policies[policy_name] = value
                self.logger.info(f"📝 New security policy added: {policy_name} = {value}")

        except Exception as e:
            self.logger.error(f"❌ Failed to update security policy: {e}")
            raise

    def get_incidents_by_type(self, event_type: SecurityEvent) -> List[SecurityIncident]:
        """Get incidents by event type"""
        return [i for i in self.incidents if i.event_type == event_type]

    def get_incidents_by_level(self, security_level: SecurityLevel) -> List[SecurityIncident]:
        """Get incidents by security level"""
        return [i for i in self.incidents if i.security_level == security_level]

    def get_unresolved_incidents(self) -> List[SecurityIncident]:
        """Get unresolved incidents"""
        return [i for i in self.incidents if not i.resolved]

    def resolve_incident(self, incident_id: str, resolution: str) -> bool:
        """Resolve a security incident"""
        try:
            for incident in self.incidents:
                if incident.incident_id == incident_id:
                    incident.resolved = True
                    incident.resolution = resolution
                    self.logger.info(f"✅ Security incident resolved: {incident_id}")
                    return True

            self.logger.warning(f"⚠️ Security incident not found: {incident_id}")
            return False

        except Exception as e:
            self.logger.error(f"❌ Failed to resolve incident: {e}")
            return False

    def get_security_summary(self) -> Dict[str, Any]:
        """Get security summary"""
        try:
            total_incidents = len(self.incidents)
            unresolved_incidents = len(self.get_unresolved_incidents())
            resolved_incidents = total_incidents - unresolved_incidents

            incidents_by_type = {}
            incidents_by_level = {}

            for incident in self.incidents:
                # By type
                type_key = incident.event_type.value
                incidents_by_type[type_key] = incidents_by_type.get(type_key, 0) + 1

                # By level
                level_key = incident.security_level.value
                incidents_by_level[level_key] = incidents_by_level.get(level_key, 0) + 1

            # Calculate security score
            security_score = (resolved_incidents / max(1, total_incidents)) * 100

            return {
                "total_incidents": total_incidents,
                "unresolved_incidents": unresolved_incidents,
                "resolved_incidents": resolved_incidents,
                "security_score": security_score,
                "incidents_by_type": incidents_by_type,
                "incidents_by_level": incidents_by_level,
                "security_policies": self.security_policies,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"❌ Failed to get security summary: {e}")
            return {"error": str(e)}

    def clear_incidents(self):
        """Clear all incidents"""
        self.incidents.clear()
        self.logger.info("🧹 All security incidents cleared")
