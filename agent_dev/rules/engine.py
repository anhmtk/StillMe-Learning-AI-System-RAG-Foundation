"""
Rule Engine for AgentDev
=======================

Rule validation and compliance checking engine.
"""

import json
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

from ..persistence.repo import RuleRepo
from ..persistence.models import create_memory_database, create_database_engine


@dataclass
class RuleEvalResult:
    """Result of rule evaluation"""
    compliant: bool
    rule_name: str
    message: str
    action_type: str
    metadata: Optional[Dict[str, Any]] = None


class RuleEngine:
    """Rule engine for compliance checking"""
    
    def __init__(self, database_url: str = "sqlite:///:memory:"):
        """Initialize rule engine with database"""
        engine, SessionLocal = create_memory_database() if database_url == "sqlite:///:memory:" else create_database_engine(database_url)
        self.SessionLocal = SessionLocal
        self.rules: List[Dict[str, Any]] = []
        self._load_rules()
    
    def _load_rules(self) -> None:
        """Load rules from database"""
        session = self.SessionLocal()
        try:
            rule_repo = RuleRepo(session)
            active_rules = rule_repo.get_active_rules()
            self.rules = []
            for rule in active_rules:
                try:
                    rule_def = json.loads(rule.rule_definition)
                    rule_def["rule_name"] = rule.rule_name
                    rule_def["priority"] = rule.priority
                    self.rules.append(rule_def)
                except json.JSONDecodeError:
                    continue
            # Sort by priority
            self.rules.sort(key=lambda r: r.get("priority", 0))
        finally:
            session.close()
    
    def _evaluate_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate a single condition against context"""
        field = condition["field"]
        operator = condition["operator"]
        value = condition["value"]
        
        # Get field value from context (support dot notation)
        field_value = self._get_nested_value(context, field)
        
        # Apply operator
        if operator == "equals":
            return field_value == value
        elif operator == "not_equals":
            return field_value != value
        elif operator == "contains":
            return str(value) in str(field_value)
        elif operator == "not_contains":
            return str(value) not in str(field_value)
        elif operator == "matches":
            return bool(re.search(str(value), str(field_value)))
        elif operator == "not_matches":
            return not bool(re.search(str(value), str(field_value)))
        elif operator == "in":
            return field_value in value if isinstance(value, list) else False
        elif operator == "not_in":
            return field_value not in value if isinstance(value, list) else True
        elif operator == "greater_than":
            try:
                return float(field_value) > float(value)
            except (ValueError, TypeError):
                return False
        elif operator == "less_than":
            try:
                return float(field_value) < float(value)
            except (ValueError, TypeError):
                return False
        else:
            return False
    
    def _get_nested_value(self, context: Dict[str, Any], field: str) -> Any:
        """Get nested value from context using dot notation"""
        keys = field.split(".")
        value = context
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value
    
    def _evaluate_rule(self, rule: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate a rule against context"""
        conditions = rule.get("conditions", [])
        if not conditions:
            return False
        
        # All conditions must be true (AND logic)
        for condition in conditions:
            if not self._evaluate_condition(condition, context):
                return False
        return True
    
    def check_compliance(self, action: str, context: Dict[str, Any]) -> RuleEvalResult:
        """Check compliance for an action against all rules"""
        # Add action to context
        context_with_action = context.copy()
        context_with_action["action"] = action
        
        # Check each rule in priority order
        for rule in self.rules:
            if self._evaluate_rule(rule, context_with_action):
                action_def = rule.get("action", {})
                return RuleEvalResult(
                    compliant=False,
                    rule_name=rule["rule_name"],
                    message=action_def.get("message", "Rule violation"),
                    action_type=action_def.get("type", "block"),
                    metadata=action_def.get("metadata")
                )
        
        # No rules matched, action is compliant
        return RuleEvalResult(
            compliant=True,
            rule_name="",
            message="Action is compliant",
            action_type="allow"
        )
    
    def add_rule(self, rule_definition: Dict[str, Any], priority: int = 0) -> bool:
        """Add a new rule to the engine"""
        try:
            # Validate rule structure
            if not self._validate_rule_structure(rule_definition):
                return False
            
            # Add to database
            session = self.SessionLocal()
            try:
                rule_repo = RuleRepo(session)
                rule_repo.create_rule(
                    rule_name=rule_definition["rule_name"],
                    rule_definition=json.dumps(rule_definition),
                    priority=priority
                )
                # Reload rules
                self._load_rules()
                return True
            finally:
                session.close()
        except Exception:
            return False
    
    def _validate_rule_structure(self, rule: Dict[str, Any]) -> bool:
        """Validate rule structure"""
        required_fields = ["rule_name", "description", "conditions", "action"]
        for field in required_fields:
            if field not in rule:
                return False
        
        # Validate conditions
        conditions = rule.get("conditions", [])
        if not isinstance(conditions, list) or not conditions:
            return False
        
        for condition in conditions:
            if not isinstance(condition, dict):
                return False
            required_condition_fields = ["field", "operator", "value"]
            for field in required_condition_fields:
                if field not in condition:
                    return False
        
        # Validate action
        action = rule.get("action", {})
        if not isinstance(action, dict):
            return False
        if "type" not in action or "message" not in action:
            return False
        
        return True


def load_rules(database_url: str = "sqlite:///:memory:") -> List[Dict[str, Any]]:
    """Load rules from database"""
    engine, SessionLocal = create_memory_database() if database_url == "sqlite:///:memory:" else create_database_engine(database_url)
    session = SessionLocal()
    try:
        rule_repo = RuleRepo(session)
        active_rules = rule_repo.get_active_rules()
        rules = []
        for rule in active_rules:
            try:
                rule_def = json.loads(rule.rule_definition)
                rule_def["rule_name"] = rule.rule_name
                rule_def["priority"] = rule.priority
                rules.append(rule_def)
            except json.JSONDecodeError:
                continue
        return sorted(rules, key=lambda r: r.get("priority", 0))
    finally:
        session.close()


def validate_rule(rule_definition: Dict[str, Any]) -> bool:
    """Validate rule definition against schema"""
    engine = RuleEngine()
    return engine._validate_rule_structure(rule_definition)


def check_compliance(action: str, context: Dict[str, Any], 
                    database_url: str = "sqlite:///:memory:") -> RuleEvalResult:
    """Check compliance for an action"""
    engine = RuleEngine(database_url)
    return engine.check_compliance(action, context)
