"""Secrecy Filter for StillMe Framework"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class SecrecyLevel(Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    SECRET = "secret"
    TOP_SECRET = "top_secret"

class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class FilterAction(Enum):
    ALLOW = "allow"
    REDACT = "redact"
    BLOCK = "block"
    ENCRYPT = "encrypt"

@dataclass
class SecrecyRule:
    """Secrecy rule record"""
    rule_id: str
    pattern: str
    secrecy_level: SecrecyLevel
    action: FilterAction
    description: str
    enabled: bool = True
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class FilterResult:
    """Filter result record"""
    result_id: str
    original_content: str
    filtered_content: str
    applied_rules: List[SecrecyRule]
    secrecy_level: SecrecyLevel
    action_taken: FilterAction
    timestamp: datetime
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class SecrecyFilter:
    """Secrecy filter for StillMe Framework"""
    
    def __init__(self):
        self.logger = logger
        self.rules: List[SecrecyRule] = []
        self.filter_results: List[FilterResult] = []
        self.default_secrecy_level = SecrecyLevel.PUBLIC
        self.logger.info("✅ SecrecyFilter initialized")
    
    def add_rule(self, 
                 pattern: str,
                 secrecy_level: SecrecyLevel,
                 action: FilterAction,
                 description: str,
                 enabled: bool = True) -> SecrecyRule:
        """Add a secrecy rule"""
        try:
            rule_id = f"rule_{len(self.rules) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            rule = SecrecyRule(
                rule_id=rule_id,
                pattern=pattern,
                secrecy_level=secrecy_level,
                action=action,
                description=description,
                enabled=enabled
            )
            
            self.rules.append(rule)
            self.logger.info(f"📝 Secrecy rule added: {description} (ID: {rule_id})")
            return rule
            
        except Exception as e:
            self.logger.error(f"❌ Failed to add secrecy rule: {e}")
            raise
    
    def filter_content(self, 
                      content: str,
                      target_secrecy_level: SecrecyLevel = None,
                      context: Dict[str, Any] = None) -> FilterResult:
        """Filter content based on secrecy rules"""
        try:
            if target_secrecy_level is None:
                target_secrecy_level = self.default_secrecy_level
            
            result_id = f"filter_{len(self.filter_results) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            filtered_content = content
            applied_rules = []
            highest_secrecy_level = SecrecyLevel.PUBLIC
            action_taken = FilterAction.ALLOW
            
            # Apply rules
            for rule in self.rules:
                if not rule.enabled:
                    continue
                
                # Check if rule pattern matches
                if re.search(rule.pattern, content, re.IGNORECASE):
                    applied_rules.append(rule)
                    
                    # Update highest secrecy level
                    if self._is_higher_secrecy_level(rule.secrecy_level, highest_secrecy_level):
                        highest_secrecy_level = rule.secrecy_level
                    
                    # Apply action
                    if rule.action == FilterAction.REDACT:
                        filtered_content = self._redact_content(filtered_content, rule.pattern)
                        action_taken = FilterAction.REDACT
                    elif rule.action == FilterAction.BLOCK:
                        filtered_content = "[CONTENT BLOCKED]"
                        action_taken = FilterAction.BLOCK
                        break  # Stop processing if content is blocked
                    elif rule.action == FilterAction.ENCRYPT:
                        filtered_content = self._encrypt_content(filtered_content, rule.pattern)
                        action_taken = FilterAction.ENCRYPT
            
            # Check if content meets target secrecy level
            if self._is_higher_secrecy_level(highest_secrecy_level, target_secrecy_level):
                if action_taken == FilterAction.ALLOW:
                    action_taken = FilterAction.REDACT
                    filtered_content = self._redact_sensitive_content(filtered_content)
            
            result = FilterResult(
                result_id=result_id,
                original_content=content,
                filtered_content=filtered_content,
                applied_rules=applied_rules,
                secrecy_level=highest_secrecy_level,
                action_taken=action_taken,
                timestamp=datetime.now(),
                metadata={
                    "target_secrecy_level": target_secrecy_level.value,
                    "context": context or {}
                }
            )
            
            self.filter_results.append(result)
            self.logger.info(f"🔒 Content filtered: {action_taken.value} (secrecy: {highest_secrecy_level.value})")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Failed to filter content: {e}")
            raise
    
    def _is_higher_secrecy_level(self, level1: SecrecyLevel, level2: SecrecyLevel) -> bool:
        """Check if level1 is higher than level2"""
        secrecy_order = {
            SecrecyLevel.PUBLIC: 0,
            SecrecyLevel.INTERNAL: 1,
            SecrecyLevel.CONFIDENTIAL: 2,
            SecrecyLevel.SECRET: 3,
            SecrecyLevel.TOP_SECRET: 4
        }
        return secrecy_order[level1] > secrecy_order[level2]
    
    def _redact_content(self, content: str, pattern: str) -> str:
        """Redact content matching pattern"""
        try:
            # Replace matches with [REDACTED]
            redacted_content = re.sub(pattern, "[REDACTED]", content, flags=re.IGNORECASE)
            return redacted_content
            
        except Exception as e:
            self.logger.error(f"❌ Failed to redact content: {e}")
            return content
    
    def _encrypt_content(self, content: str, pattern: str) -> str:
        """Encrypt content matching pattern"""
        try:
            # Simple encryption (in real implementation, use proper encryption)
            encrypted_content = re.sub(pattern, "[ENCRYPTED]", content, flags=re.IGNORECASE)
            return encrypted_content
            
        except Exception as e:
            self.logger.error(f"❌ Failed to encrypt content: {e}")
            return content
    
    def _redact_sensitive_content(self, content: str) -> str:
        """Redact sensitive content based on common patterns"""
        try:
            # Common sensitive patterns
            sensitive_patterns = [
                r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
                r'\b\d{4}-\d{4}-\d{4}-\d{4}\b',  # Credit card
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
                r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Phone
                r'\bpassword\s*[:=]\s*\w+\b',  # Password
                r'\bsecret\s*[:=]\s*\w+\b',  # Secret
                r'\bkey\s*[:=]\s*\w+\b',  # Key
                r'\btoken\s*[:=]\s*\w+\b'  # Token
            ]
            
            redacted_content = content
            for pattern in sensitive_patterns:
                redacted_content = re.sub(pattern, "[REDACTED]", redacted_content, flags=re.IGNORECASE)
            
            return redacted_content
            
        except Exception as e:
            self.logger.error(f"❌ Failed to redact sensitive content: {e}")
            return content
    
    def get_rules_by_secrecy_level(self, secrecy_level: SecrecyLevel) -> List[SecrecyRule]:
        """Get rules by secrecy level"""
        return [r for r in self.rules if r.secrecy_level == secrecy_level]
    
    def get_rules_by_action(self, action: FilterAction) -> List[SecrecyRule]:
        """Get rules by action"""
        return [r for r in self.rules if r.action == action]
    
    def get_enabled_rules(self) -> List[SecrecyRule]:
        """Get enabled rules"""
        return [r for r in self.rules if r.enabled]
    
    def get_filter_summary(self) -> Dict[str, Any]:
        """Get filter summary"""
        try:
            total_rules = len(self.rules)
            enabled_rules = len(self.get_enabled_rules())
            total_filters = len(self.filter_results)
            
            rules_by_secrecy_level = {}
            rules_by_action = {}
            filters_by_action = {}
            
            for rule in self.rules:
                # By secrecy level
                level_key = rule.secrecy_level.value
                rules_by_secrecy_level[level_key] = rules_by_secrecy_level.get(level_key, 0) + 1
                
                # By action
                action_key = rule.action.value
                rules_by_action[action_key] = rules_by_action.get(action_key, 0) + 1
            
            for result in self.filter_results:
                action_key = result.action_taken.value
                filters_by_action[action_key] = filters_by_action.get(action_key, 0) + 1
            
            return {
                "total_rules": total_rules,
                "enabled_rules": enabled_rules,
                "total_filters": total_filters,
                "rules_by_secrecy_level": rules_by_secrecy_level,
                "rules_by_action": rules_by_action,
                "filters_by_action": filters_by_action,
                "default_secrecy_level": self.default_secrecy_level.value,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get filter summary: {e}")
            return {"error": str(e)}
    
    def clear_rules(self):
        """Clear all rules"""
        self.rules.clear()
        self.logger.info("🧹 All secrecy rules cleared")
    
    def clear_filter_results(self):
        """Clear all filter results"""
        self.filter_results.clear()
        self.logger.info("🧹 All filter results cleared")

# Global secrecy filter instance
_secrecy_filter_instance = None

def get_default_filter() -> SecrecyFilter:
    """Get default secrecy filter instance"""
    global _secrecy_filter_instance
    if _secrecy_filter_instance is None:
        _secrecy_filter_instance = SecrecyFilter()
    return _secrecy_filter_instance
