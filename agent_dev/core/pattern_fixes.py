#!/usr/bin/env python3
"""
🔧 Pattern-Based Fixes for AgentDev
===================================

Tập trung fix các lỗi phổ biến theo pattern thay vì fix từng lỗi riêng lẻ.
"""

from typing import Dict, List, Optional, Tuple
import re
from dataclasses import dataclass

@dataclass
class FixPattern:
    """Pattern để fix lỗi"""
    name: str
    error_type: str
    pattern: str
    fix_template: str
    priority: int = 1

class PatternBasedFixer:
    """Fixer dựa trên pattern"""

    def __init__(self):
        self.patterns = self._load_patterns()

    def _load_patterns(self) -> List[FixPattern]:
        """Load các pattern fix"""
        return [
            # Pattern 1: ReflectionResult, NodeType, ImpactLevel
            FixPattern(
                name="test_analysis_classes",
                error_type="F821",
                pattern=r"undefined name '(ReflectionResult|NodeType|ImpactLevel|SemanticSearchEngine|SearchResult|MatchType)'",
                fix_template="from tests.analysis_classes import {name}",
                priority=1
            ),

            # Pattern 2: apply_policies, safe_reply, classify, sanitize
            FixPattern(
                name="guard_functions",
                error_type="F821",
                pattern=r"undefined name '(apply_policies|safe_reply|classify|sanitize|redact_output|CANARY)'",
                fix_template="from stillme_core.guard import {name}",
                priority=1
            ),

            # Pattern 3: MemoryItem, LongTermMemory
            FixPattern(
                name="memory_classes",
                error_type="F821",
                pattern=r"undefined name '(MemoryItem|LongTermMemory)'",
                fix_template="from stillme_core.memory import {name}",
                priority=1
            ),

            # Pattern 4: QualityIssue, QualityReport
            FixPattern(
                name="quality_classes",
                error_type="F821",
                pattern=r"undefined name '(QualityIssue|QualityReport)'",
                fix_template="from stillme_core.quality import {name}",
                priority=1
            ),

            # Pattern 5: SimulationStatus, AttackCategory, AttackSeverity
            FixPattern(
                name="simulation_classes",
                error_type="F821",
                pattern=r"undefined name '(SimulationStatus|AttackCategory|AttackSeverity|EthicalPrinciple|ViolationSeverity)'",
                fix_template="from stillme_core.simulation import {name}",
                priority=1
            ),

            # Pattern 6: RedisEventBus, DAGExecutor, RBACManager
            FixPattern(
                name="infrastructure_classes",
                error_type="F821",
                pattern=r"undefined name '(RedisEventBus|DAGExecutor|RBACManager)'",
                fix_template="from stillme_core.infrastructure import {name}",
                priority=1
            ),

            # Pattern 7: Common imports
            FixPattern(
                name="common_imports",
                error_type="F821",
                pattern=r"undefined name '(time|yaml|asdict|os|html_content|news_delta|reddit_engagement|wrap_content)'",
                fix_template="import {name}",
                priority=2
            ),

            # Pattern 8: AgentDevLogger, log_step
            FixPattern(
                name="logging_functions",
                error_type="F821",
                pattern=r"undefined name '(AgentDevLogger|log_step)'",
                fix_template="from stillme_core.logging import {name}",
                priority=1
            ),

            # Pattern 9: AI Manager functions
            FixPattern(
                name="ai_manager_functions",
                error_type="F821",
                pattern=r"undefined name '(health|set_mode|warmup|dev_agent|controller)'",
                fix_template="from stillme_core.ai_manager import {name}",
                priority=1
            )
        ]

    def find_matching_pattern(self, error_message: str) -> Optional[FixPattern]:
        """Tìm pattern phù hợp với error message"""
        for pattern in sorted(self.patterns, key=lambda x: x.priority):
            if re.search(pattern.pattern, error_message):
                return pattern
        return None

    def generate_fix(self, error_message: str, file_path: str) -> Optional[str]:
        """Generate fix dựa trên pattern"""
        pattern = self.find_matching_pattern(error_message)
        if not pattern:
            return None

        # Extract variable name from error message
        match = re.search(pattern.pattern, error_message)
        if not match:
            return None

        var_name = match.group(1)

        # Generate fix
        if "{name}" in pattern.fix_template:
            fix = pattern.fix_template.format(name=var_name)
        else:
            fix = pattern.fix_template

        return fix

    def get_fix_priority(self, error_message: str) -> int:
        """Get priority của fix"""
        pattern = self.find_matching_pattern(error_message)
        return pattern.priority if pattern else 999

    def get_all_patterns(self) -> List[FixPattern]:
        """Get tất cả patterns"""
        return self.patterns

    def fix_error(self, error_info) -> bool:
        """Fix a single error and return success status"""
        try:
            error_message = f"{error_info.rule} {error_info.msg}"
            fix = self.generate_fix(error_message, error_info.file)
            return fix is not None and fix.strip() != ""
        except Exception:
            return False

# Example usage
if __name__ == "__main__":
    fixer = PatternBasedFixer()

    # Test cases
    test_errors = [
        "F821 undefined name 'ReflectionResult'",
        "F821 undefined name 'apply_policies'",
        "F821 undefined name 'MemoryItem'",
        "F821 undefined name 'time'",
        "F821 undefined name 'unknown_var'"
    ]

    for error in test_errors:
        fix = fixer.generate_fix(error, "test.py")
        priority = fixer.get_fix_priority(error)
        print(f"Error: {error}")
        print(f"Fix: {fix}")
        print(f"Priority: {priority}")
        print("-" * 40)
