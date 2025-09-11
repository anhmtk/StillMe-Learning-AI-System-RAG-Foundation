#!/usr/bin/env python3
"""
AgentDev Advanced - Business Logic Analysis
SAFETY: Read-only analysis, no code modifications
"""

import os
import re
import json
import ast
from pathlib import Path
from typing import Dict, List, Any, Set, Optional
from dataclasses import dataclass
from enum import Enum

class HumanInputType(Enum):
    """Types of human input requirements"""
    MANUAL_APPROVAL = "manual_approval"
    USER_CONFIRMATION = "user_confirmation"
    PARAMETER_INPUT = "parameter_input"
    DECISION_MAKING = "decision_making"
    ERROR_HANDLING = "error_handling"
    CONFIGURATION = "configuration"

class ComplexityLevel(Enum):
    """Complexity levels for business logic"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class BusinessRule:
    """Represents a business rule requiring human input"""
    name: str
    file_path: str
    line_number: int
    rule_type: HumanInputType
    complexity: ComplexityLevel
    description: str
    current_implementation: str
    automation_potential: float  # 0.0 to 1.0
    risks: List[str]
    dependencies: List[str]
    test_coverage: bool

@dataclass
class DecisionPattern:
    """Represents a decision-making pattern"""
    pattern_name: str
    frequency: int
    complexity: ComplexityLevel
    automation_feasibility: float
    examples: List[str]
    common_triggers: List[str]

class BusinessLogicAnalyzer:
    """Analyzes business logic requiring human input"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.business_rules = []
        self.decision_patterns = {}
        self.human_input_indicators = {
            "manual_approval": [
                r"human.*approval", r"manual.*approval", r"require.*approval",
                r"wait.*for.*user", r"user.*confirm", r"admin.*approve"
            ],
            "user_confirmation": [
                r"confirm.*action", r"are.*you.*sure", r"proceed.*with",
                r"continue.*operation", r"user.*input", r"interactive.*prompt"
            ],
            "parameter_input": [
                r"input.*parameter", r"user.*provide", r"config.*value",
                r"setting.*required", r"parameter.*missing", r"config.*not.*found"
            ],
            "decision_making": [
                r"decision.*required", r"choose.*option", r"select.*strategy",
                r"determine.*action", r"evaluate.*options", r"make.*choice"
            ],
            "error_handling": [
                r"error.*handling", r"exception.*caught", r"fallback.*required",
                r"recovery.*action", r"manual.*intervention", r"escalate.*to.*human"
            ],
            "configuration": [
                r"config.*required", r"setup.*needed", r"initialization.*required",
                r"environment.*variable", r"api.*key.*required", r"credentials.*needed"
            ]
        }
        
    def analyze_business_logic(self) -> Dict[str, Any]:
        """Main analysis function"""
        print("🔍 Starting business logic analysis...")
        
        # Safety check: Ensure read-only mode
        if not self.project_root.exists():
            raise FileNotFoundError(f"Project root not found: {self.project_root}")
        
        # Analyze different types of business logic
        self._analyze_agent_dev_logic()
        self._analyze_safety_guard_logic()
        self._analyze_decision_engine_logic()
        self._analyze_api_server_logic()
        
        # Identify decision patterns
        self._identify_decision_patterns()
        
        # Generate recommendations
        recommendations = self._generate_automation_recommendations()
        
        return {
            "analysis_timestamp": "2025-09-09T23:46:15Z",
            "total_business_rules": len(self.business_rules),
            "business_rules": [
                {
                    "name": rule.name,
                    "file_path": rule.file_path,
                    "line_number": rule.line_number,
                    "rule_type": rule.rule_type.value,
                    "complexity": rule.complexity.value,
                    "description": rule.description,
                    "current_implementation": rule.current_implementation,
                    "automation_potential": rule.automation_potential,
                    "risks": rule.risks,
                    "dependencies": rule.dependencies,
                    "test_coverage": rule.test_coverage
                }
                for rule in self.business_rules
            ],
            "decision_patterns": {
                pattern_name: {
                    "frequency": pattern.frequency,
                    "complexity": pattern.complexity.value,
                    "automation_feasibility": pattern.automation_feasibility,
                    "examples": pattern.examples,
                    "common_triggers": pattern.common_triggers
                }
                for pattern_name, pattern in self.decision_patterns.items()
            },
            "automation_recommendations": recommendations,
            "summary": self._generate_summary()
        }
    
    def _analyze_agent_dev_logic(self):
        """Analyze AgentDev business logic"""
        print("📋 Analyzing AgentDev business logic...")
        
        agent_dev_file = self.project_root / "agent_dev.py"
        if agent_dev_file.exists():
            content = agent_dev_file.read_text(encoding='utf-8')
            self._extract_business_rules_from_content(
                content, str(agent_dev_file), "AgentDev"
            )
    
    def _analyze_safety_guard_logic(self):
        """Analyze safety guard business logic"""
        print("🛡️ Analyzing safety guard business logic...")
        
        safety_guard_file = self.project_root / "stillme_core" / "safety_guard.py"
        if safety_guard_file.exists():
            content = safety_guard_file.read_text(encoding='utf-8')
            self._extract_business_rules_from_content(
                content, str(safety_guard_file), "SafetyGuard"
            )
    
    def _analyze_decision_engine_logic(self):
        """Analyze decision engine business logic"""
        print("🧠 Analyzing decision engine business logic...")
        
        decision_engine_file = self.project_root / "stillme_core" / "decision_making" / "decision_engine.py"
        if decision_engine_file.exists():
            content = decision_engine_file.read_text(encoding='utf-8')
            self._extract_business_rules_from_content(
                content, str(decision_engine_file), "DecisionEngine"
            )
    
    def _analyze_api_server_logic(self):
        """Analyze API server business logic"""
        print("🌐 Analyzing API server business logic...")
        
        api_server_file = self.project_root / "api_server.py"
        if api_server_file.exists():
            content = api_server_file.read_text(encoding='utf-8')
            self._extract_business_rules_from_content(
                content, str(api_server_file), "APIServer"
            )
    
    def _extract_business_rules_from_content(self, content: str, file_path: str, module_name: str):
        """Extract business rules from file content"""
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line_lower = line.lower()
            
            # Check for human input indicators
            for input_type, patterns in self.human_input_indicators.items():
                for pattern in patterns:
                    if re.search(pattern, line_lower):
                        rule = self._create_business_rule(
                            line, line_num, file_path, input_type, module_name
                        )
                        if rule:
                            self.business_rules.append(rule)
                        break
    
    def _create_business_rule(self, line: str, line_num: int, file_path: str, 
                            input_type: str, module_name: str) -> Optional[BusinessRule]:
        """Create a business rule from a line of code"""
        try:
            # Determine complexity based on line content
            complexity = self._assess_complexity(line)
            
            # Determine automation potential
            automation_potential = self._assess_automation_potential(line, input_type)
            
            # Identify risks
            risks = self._identify_risks(line, input_type)
            
            # Find dependencies
            dependencies = self._find_dependencies(line)
            
            # Check test coverage (simplified)
            test_coverage = self._check_test_coverage(file_path, line_num)
            
            return BusinessRule(
                name=f"{module_name}_{input_type}_{line_num}",
                file_path=file_path,
                line_number=line_num,
                rule_type=HumanInputType(input_type),
                complexity=complexity,
                description=self._generate_description(line, input_type),
                current_implementation=line.strip(),
                automation_potential=automation_potential,
                risks=risks,
                dependencies=dependencies,
                test_coverage=test_coverage
            )
        except Exception as e:
            print(f"⚠️ Warning: Could not create business rule for line {line_num}: {e}")
            return None
    
    def _assess_complexity(self, line: str) -> ComplexityLevel:
        """Assess complexity of a business rule"""
        complexity_indicators = {
            ComplexityLevel.CRITICAL: [
                r"security", r"authentication", r"authorization", r"encryption",
                r"delete.*data", r"drop.*table", r"system.*shutdown"
            ],
            ComplexityLevel.HIGH: [
                r"decision.*tree", r"multi.*step", r"conditional.*logic",
                r"error.*handling", r"exception.*handling", r"fallback"
            ],
            ComplexityLevel.MEDIUM: [
                r"validation", r"check.*condition", r"if.*else", r"switch.*case",
                r"parameter.*check", r"input.*validation"
            ],
            ComplexityLevel.LOW: [
                r"simple.*check", r"basic.*validation", r"default.*value",
                r"configuration", r"setting"
            ]
        }
        
        line_lower = line.lower()
        for level, patterns in complexity_indicators.items():
            for pattern in patterns:
                if re.search(pattern, line_lower):
                    return level
        
        return ComplexityLevel.LOW
    
    def _assess_automation_potential(self, line: str, input_type: str) -> float:
        """Assess automation potential (0.0 to 1.0)"""
        base_potential = {
            "configuration": 0.9,
            "parameter_input": 0.8,
            "user_confirmation": 0.6,
            "decision_making": 0.4,
            "error_handling": 0.3,
            "manual_approval": 0.2
        }
        
        potential = base_potential.get(input_type, 0.5)
        
        # Adjust based on line content
        line_lower = line.lower()
        if "security" in line_lower or "critical" in line_lower:
            potential *= 0.5  # Reduce automation potential for security-critical code
        elif "simple" in line_lower or "basic" in line_lower:
            potential *= 1.2  # Increase for simple cases
        
        return min(1.0, max(0.0, potential))
    
    def _identify_risks(self, line: str, input_type: str) -> List[str]:
        """Identify risks associated with automating this rule"""
        risks = []
        line_lower = line.lower()
        
        if "security" in line_lower:
            risks.append("Security vulnerability if automated incorrectly")
        if "delete" in line_lower or "remove" in line_lower:
            risks.append("Data loss risk")
        if "critical" in line_lower:
            risks.append("Critical system impact")
        if "user" in line_lower and "input" in line_lower:
            risks.append("User experience degradation")
        
        # Type-specific risks
        if input_type == "manual_approval":
            risks.append("Bypassing important human oversight")
        elif input_type == "error_handling":
            risks.append("Inadequate error recovery")
        
        return risks
    
    def _find_dependencies(self, line: str) -> List[str]:
        """Find dependencies for this business rule"""
        dependencies = []
        
        # Look for function calls, imports, etc.
        if "import" in line:
            dependencies.append("External module dependency")
        if "def " in line:
            dependencies.append("Function definition")
        if "class " in line:
            dependencies.append("Class definition")
        
        return dependencies
    
    def _check_test_coverage(self, file_path: str, line_num: int) -> bool:
        """Check if this line has test coverage (simplified)"""
        # This is a simplified check - in reality, you'd use coverage tools
        test_file = file_path.replace('.py', '_test.py')
        return Path(test_file).exists()
    
    def _generate_description(self, line: str, input_type: str) -> str:
        """Generate description for the business rule"""
        descriptions = {
            "manual_approval": "Requires human approval before proceeding",
            "user_confirmation": "Needs user confirmation for action",
            "parameter_input": "Requires user to provide parameters",
            "decision_making": "Involves complex decision logic",
            "error_handling": "Handles errors requiring human intervention",
            "configuration": "Requires configuration or setup"
        }
        
        base_desc = descriptions.get(input_type, "Business rule requiring human input")
        return f"{base_desc}: {line.strip()[:100]}..."
    
    def _identify_decision_patterns(self):
        """Identify common decision patterns"""
        print("🔍 Identifying decision patterns...")
        
        # Group rules by type and analyze patterns
        rule_groups = {}
        for rule in self.business_rules:
            rule_type = rule.rule_type.value
            if rule_type not in rule_groups:
                rule_groups[rule_type] = []
            rule_groups[rule_type].append(rule)
        
        # Create decision patterns
        for rule_type, rules in rule_groups.items():
            if rules:
                pattern = DecisionPattern(
                    pattern_name=f"{rule_type}_pattern",
                    frequency=len(rules),
                    complexity=self._calculate_average_complexity(rules),
                    automation_feasibility=self._calculate_average_automation_potential(rules),
                    examples=[rule.current_implementation for rule in rules[:3]],
                    common_triggers=[rule_type]
                )
                self.decision_patterns[rule_type] = pattern
    
    def _calculate_average_complexity(self, rules: List[BusinessRule]) -> ComplexityLevel:
        """Calculate average complexity level"""
        complexity_values = {
            ComplexityLevel.LOW: 1,
            ComplexityLevel.MEDIUM: 2,
            ComplexityLevel.HIGH: 3,
            ComplexityLevel.CRITICAL: 4
        }
        
        if not rules:
            return ComplexityLevel.LOW
        
        avg_value = sum(complexity_values[rule.complexity] for rule in rules) / len(rules)
        
        for level, value in complexity_values.items():
            if avg_value <= value:
                return level
        
        return ComplexityLevel.CRITICAL
    
    def _calculate_average_automation_potential(self, rules: List[BusinessRule]) -> float:
        """Calculate average automation potential"""
        if not rules:
            return 0.0
        
        return sum(rule.automation_potential for rule in rules) / len(rules)
    
    def _generate_automation_recommendations(self) -> List[Dict[str, Any]]:
        """Generate automation recommendations"""
        recommendations = []
        
        # High automation potential rules
        high_potential_rules = [rule for rule in self.business_rules 
                              if rule.automation_potential > 0.7]
        
        if high_potential_rules:
            recommendations.append({
                "category": "High Automation Potential",
                "rules": [rule.name for rule in high_potential_rules],
                "recommendation": "These rules can be automated with minimal risk",
                "priority": "HIGH",
                "effort": "LOW"
            })
        
        # Medium automation potential rules
        medium_potential_rules = [rule for rule in self.business_rules 
                                if 0.4 <= rule.automation_potential <= 0.7]
        
        if medium_potential_rules:
            recommendations.append({
                "category": "Medium Automation Potential",
                "rules": [rule.name for rule in medium_potential_rules],
                "recommendation": "These rules can be partially automated with careful design",
                "priority": "MEDIUM",
                "effort": "MEDIUM"
            })
        
        # Low automation potential rules
        low_potential_rules = [rule for rule in self.business_rules 
                             if rule.automation_potential < 0.4]
        
        if low_potential_rules:
            recommendations.append({
                "category": "Low Automation Potential",
                "rules": [rule.name for rule in low_potential_rules],
                "recommendation": "These rules should remain manual or require human-in-the-loop",
                "priority": "LOW",
                "effort": "HIGH"
            })
        
        return recommendations
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate analysis summary"""
        total_rules = len(self.business_rules)
        if total_rules == 0:
            return {
                "total_rules": 0,
                "automation_potential": "No business rules found",
                "complexity_distribution": {},
                "recommendations": "No automation recommendations"
            }
        
        # Calculate statistics
        complexity_dist = {}
        for rule in self.business_rules:
            complexity = rule.complexity.value
            complexity_dist[complexity] = complexity_dist.get(complexity, 0) + 1
        
        avg_automation_potential = sum(rule.automation_potential for rule in self.business_rules) / total_rules
        
        return {
            "total_rules": total_rules,
            "automation_potential": f"{avg_automation_potential:.2f}",
            "complexity_distribution": complexity_dist,
            "high_priority_rules": len([r for r in self.business_rules if r.complexity == ComplexityLevel.CRITICAL]),
            "automation_ready_rules": len([r for r in self.business_rules if r.automation_potential > 0.7])
        }

def main():
    """Main analysis function"""
    print("🤖 AgentDev Advanced - Business Logic Analysis")
    print("=" * 50)
    
    analyzer = BusinessLogicAnalyzer()
    
    try:
        analysis_result = analyzer.analyze_business_logic()
        
        # Save analysis result
        result_path = Path("backup/business_logic_analysis_20250909_234615/business_logic_analysis.json")
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Analysis complete! Result saved to: {result_path}")
        print(f"📊 Found {analysis_result['total_business_rules']} business rules")
        print(f"🔍 Identified {len(analysis_result['decision_patterns'])} decision patterns")
        print(f"📈 Average automation potential: {analysis_result['summary']['automation_potential']}")
        
        return analysis_result
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return None

if __name__ == "__main__":
    main()
