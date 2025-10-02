"""
Escalation Management for AgentDev Operations
============================================

Handles incident escalation and remediation planning.
"""

import logging
from datetime import datetime
from typing import Any

from .classifier import IssueClassifier, IssueSeverity
from .notifier import EmailNotifier, TelegramNotifier

logger = logging.getLogger(__name__)


class EscalationManager:
    """Manages incident escalation and remediation"""

    def __init__(self):
        self.email_notifier = EmailNotifier()
        self.telegram_notifier = TelegramNotifier()
        self.classifier = IssueClassifier()

    def handle_incident(self, patrol_result: dict[str, Any]) -> dict[str, Any]:
        """
        Handle incident based on patrol results

        Args:
            patrol_result: Results from patrol run

        Returns:
            Escalation result with actions taken
        """
        incidents = self._analyze_patrol_results(patrol_result)

        escalation_result = {
            "timestamp": datetime.now().isoformat(),
            "incidents_found": len(incidents),
            "escalations_sent": 0,
            "auto_fixes_applied": 0,
            "actions": []
        }

        for incident in incidents:
            action = self._process_incident(incident)
            escalation_result["actions"].append(action)

            if action["escalated"]:
                escalation_result["escalations_sent"] += 1
            if action["auto_fixed"]:
                escalation_result["auto_fixes_applied"] += 1

        return escalation_result

    def _analyze_patrol_results(self, patrol_result: dict[str, Any]) -> list[dict[str, Any]]:
        """Analyze patrol results and identify incidents"""
        incidents = []

        # Analyze ruff issues
        ruff_issues = patrol_result.get("ruff_issues", [])
        if ruff_issues:
            classified = self.classifier.batch_classify(ruff_issues)

            for severity, issues in classified.items():
                if issues:
                    incidents.append({
                        "type": "code_quality",
                        "severity": severity,
                        "issues": issues,
                        "count": len(issues)
                    })

        # Analyze pytest status
        pytest_status = patrol_result.get("pytest_status", "unknown")
        if pytest_status != "passed":
            incidents.append({
                "type": "test_failure",
                "severity": IssueSeverity.MAJOR.value,
                "status": pytest_status,
                "count": 1
            })

        # Analyze red-team results
        red_team_status = patrol_result.get("red_team_status", "not_available")
        if red_team_status == "high_risk":
            risk_score = patrol_result.get("red_team_risk_score", 0.0)
            incidents.append({
                "type": "security_risk",
                "severity": IssueSeverity.SECURITY.value,
                "risk_score": risk_score,
                "count": 1
            })

        return incidents

    def _process_incident(self, incident: dict[str, Any]) -> dict[str, Any]:
        """Process individual incident"""
        incident_type = incident["type"]
        severity = incident["severity"]

        action = {
            "incident_type": incident_type,
            "severity": severity,
            "escalated": False,
            "auto_fixed": False,
            "channels_used": []
        }

        # Determine if escalation is needed
        if severity in [IssueSeverity.MAJOR.value, IssueSeverity.SECURITY.value]:
            action["escalated"] = True

            # Send escalation notifications
            title, details, remediation = self._generate_incident_report(incident)

            # Send via email
            if self.email_notifier.send_incident_report(severity, title, details, remediation):
                action["channels_used"].append("email")

            # Send via Telegram
            if self.telegram_notifier.send_incident_report(severity, title, details, remediation):
                action["channels_used"].append("telegram")

        # Handle auto-fix for minor issues
        elif severity == IssueSeverity.MINOR.value and incident_type == "code_quality":
            action["auto_fixed"] = self._apply_auto_fixes(incident)

        return action

    def _generate_incident_report(self, incident: dict[str, Any]) -> tuple[str, str, str]:
        """Generate incident report in Vietnamese"""
        incident_type = incident["type"]
        incident["severity"]

        if incident_type == "code_quality":
            issues = incident["issues"]
            count = incident["count"]

            title = f"Lỗi chất lượng code ({count} lỗi)"
            details = f"Phát hiện {count} lỗi code quality:\n"
            for issue in issues[:5]:  # Show first 5 issues
                details += f"- {issue.get('file', 'unknown')}:{issue.get('line', 0)} - {issue.get('rule', 'unknown')}\n"
            if count > 5:
                details += f"... và {count - 5} lỗi khác\n"

            remediation = "1. Kiểm tra và sửa các lỗi code quality\n2. Chạy lại ruff check để xác nhận\n3. Commit các thay đổi nếu cần"

        elif incident_type == "test_failure":
            status = incident["status"]
            title = f"Lỗi kiểm thử ({status})"
            details = f"Pytest smoke test thất bại với trạng thái: {status}"
            remediation = "1. Kiểm tra log pytest để xác định nguyên nhân\n2. Sửa lỗi test hoặc cập nhật test case\n3. Chạy lại pytest để xác nhận"

        elif incident_type == "security_risk":
            risk_score = incident.get("risk_score", 0.0)
            title = f"Rủi ro bảo mật (Risk Score: {risk_score:.2f})"
            details = f"Red-team engine phát hiện rủi ro bảo mật với điểm số: {risk_score:.2f}"
            remediation = "1. Xem xét kỹ các phát hiện bảo mật\n2. Áp dụng các biện pháp khắc phục\n3. Chạy lại security scan để xác nhận"

        else:
            title = f"Sự cố không xác định ({incident_type})"
            details = f"Phát hiện sự cố loại: {incident_type}"
            remediation = "1. Kiểm tra log chi tiết\n2. Xác định nguyên nhân gốc\n3. Áp dụng biện pháp khắc phục phù hợp"

        return title, details, remediation

    def _apply_auto_fixes(self, incident: dict[str, Any]) -> bool:
        """Apply auto-fixes for minor issues"""
        try:
            issues = incident["issues"]
            if not issues:
                return False

            # Apply ruff auto-fix
            import subprocess
            result = subprocess.run(
                ["ruff", "check", "--fix", "stillme_ai", "tests"],
                capture_output=True,
                text=False,  # Capture raw bytes
                timeout=30
            )

            if result.returncode == 0:
                logger.info(f"Auto-fixed {len(issues)} minor issues")
                return True
            else:
                # Use safe decoding for stderr
                from stillme_core.utils.io_safe import safe_decode
                stderr_text = safe_decode(result.stderr) if result.stderr else ""
                logger.warning(f"Auto-fix failed: {stderr_text}")
                return False

        except Exception as e:
            logger.error(f"Auto-fix failed: {e}")
            return False
