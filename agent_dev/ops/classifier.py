"""
Issue Classification System for AgentDev Operations
==================================================

Classifies issues by severity and type for appropriate handling.
"""

import logging
from enum import Enum
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class IssueSeverity(Enum):
    """Issue severity levels"""
    MINOR = "MINOR"
    MAJOR = "MAJOR"
    SECURITY = "SECURITY"


class IssueClassifier:
    """Classifies issues by severity and type"""

    def __init__(self):
        self.minor_patterns = ["W293", "W291", "I001", "F401"]
        self.major_patterns = ["F821", "E999", "ImportError", "SyntaxError"]
        self.security_patterns = ["REDTEAM_RISK>=", "SECURITY_VIOLATION", "PII_LEAK"]

    def classify(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify an issue by severity and type
        
        Args:
            issue: Issue dictionary with keys like 'rule', 'message', 'file', 'line'
            
        Returns:
            Classification result with severity, reason, and handling instructions
        """
        rule = issue.get("rule", "")
        message = issue.get("message", "")
        file_path = issue.get("file", "")

        # Check for security issues first
        if self._is_security_issue(rule, message, file_path):
            return {
                "severity": IssueSeverity.SECURITY.value,
                "reason": "Security-related issue detected",
                "auto_fix": False,
                "escalate": True,
                "priority": 1
            }

        # Check for major issues
        if self._is_major_issue(rule, message, file_path):
            return {
                "severity": IssueSeverity.MAJOR.value,
                "reason": "Major issue affecting functionality",
                "auto_fix": False,
                "escalate": True,
                "priority": 2
            }

        # Check for minor issues
        if self._is_minor_issue(rule, message, file_path):
            return {
                "severity": IssueSeverity.MINOR.value,
                "reason": "Minor formatting or style issue",
                "auto_fix": True,
                "escalate": False,
                "priority": 3
            }

        # Default classification
        return {
            "severity": IssueSeverity.MINOR.value,
            "reason": "Unknown issue type",
            "auto_fix": False,
            "escalate": False,
            "priority": 4
        }

    def _is_security_issue(self, rule: str, message: str, file_path: str) -> bool:
        """Check if issue is security-related"""
        # Check rule patterns
        for pattern in self.security_patterns:
            if pattern in rule or pattern in message:
                return True

        # Check file path for security-sensitive files
        security_files = ["security", "auth", "password", "token", "key", "secret"]
        if any(sec_file in file_path.lower() for sec_file in security_files):
            if any(major in rule for major in self.major_patterns):
                return True

        return False

    def _is_major_issue(self, rule: str, message: str, file_path: str) -> bool:
        """Check if issue is major"""
        # Direct rule match
        if rule in self.major_patterns:
            return True

        # Check message content
        major_keywords = ["import", "syntax", "undefined", "not defined", "module not found"]
        if any(keyword in message.lower() for keyword in major_keywords):
            return True

        return False

    def _is_minor_issue(self, rule: str, message: str, file_path: str) -> bool:
        """Check if issue is minor"""
        return rule in self.minor_patterns

    def batch_classify(self, issues: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Classify a batch of issues
        
        Args:
            issues: List of issue dictionaries
            
        Returns:
            Dictionary with issues grouped by severity
        """
        classified = {
            IssueSeverity.SECURITY.value: [],
            IssueSeverity.MAJOR.value: [],
            IssueSeverity.MINOR.value: []
        }

        for issue in issues:
            classification = self.classify(issue)
            severity = classification["severity"]
            issue["classification"] = classification
            classified[severity].append(issue)

        return classified
