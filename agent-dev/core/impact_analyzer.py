#!/usr/bin/env python3
"""
Impact Analyzer - Senior Developer Thinking Module
Phân tích tác động toàn diện trước khi thực hiện thay đổi

Tính năng:
1. Dependency Analysis - Phân tích dependencies
2. Performance Impact - Đánh giá tác động hiệu suất
3. Security Analysis - Phân tích bảo mật
4. Maintainability Assessment - Đánh giá khả năng bảo trì
5. User Impact Analysis - Phân tích tác động người dùng
6. Business Value Assessment - Đánh giá giá trị kinh doanh
"""

import os
import ast
import re
import json
import subprocess
import time
from typing import Dict, List, Set, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

class ImpactLevel(Enum):
    """Mức độ tác động"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RiskLevel(Enum):
    """Mức độ rủi ro"""
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class DependencyInfo:
    """Thông tin dependency"""
    module: str
    file_path: str
    import_type: str  # 'import', 'from_import', 'relative_import'
    line_number: int
    is_used: bool
    usage_count: int

@dataclass
class PerformanceImpact:
    """Tác động hiệu suất"""
    level: ImpactLevel
    estimated_time_complexity: str
    memory_impact: str
    io_operations: int
    network_calls: int
    database_queries: int
    caching_opportunities: List[str]

@dataclass
class SecurityRisk:
    """Rủi ro bảo mật"""
    risk_type: str
    severity: RiskLevel
    description: str
    affected_files: List[str]
    mitigation_suggestions: List[str]

@dataclass
class MaintainabilityScore:
    """Điểm khả năng bảo trì"""
    overall_score: float  # 0-1
    complexity_score: float
    testability_score: float
    documentation_score: float
    coupling_score: float
    cohesion_score: float
    suggestions: List[str]

@dataclass
class UserImpact:
    """Tác động người dùng"""
    level: ImpactLevel
    affected_features: List[str]
    user_experience_changes: List[str]
    breaking_changes: List[str]
    migration_required: bool
    user_training_needed: bool

@dataclass
class BusinessValue:
    """Giá trị kinh doanh"""
    roi_estimate: float
    user_satisfaction_impact: str
    market_competitiveness: str
    development_cost: float
    maintenance_cost: float
    time_to_market: str

@dataclass
class ImpactAnalysisResult:
    """Kết quả phân tích tác động"""
    dependencies: List[DependencyInfo]
    performance: PerformanceImpact
    security_risks: List[SecurityRisk]
    maintainability: MaintainabilityScore
    user_impact: UserImpact
    business_value: BusinessValue
    overall_risk_level: RiskLevel
    recommendations: List[str]
    analysis_time: float

class ImpactAnalyzer:
    """Senior Developer Impact Analyzer"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.python_files = self._find_python_files()
        self.dependency_graph = {}
        self.performance_patterns = self._load_performance_patterns()
        self.security_patterns = self._load_security_patterns()
        
    def _find_python_files(self) -> List[Path]:
        """Tìm tất cả Python files trong project"""
        python_files = []
        for root, dirs, files in os.walk(self.project_root):
            # Skip certain directories
            dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', 'node_modules', '.venv', 'venv'}]
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)
        return python_files
    
    def _load_performance_patterns(self) -> Dict[str, Dict]:
        """Load performance analysis patterns"""
        return {
            'high_complexity': {
                'patterns': [r'O\(n\^2\)', r'O\(2\^n\)', r'nested.*for.*in.*for'],
                'impact': ImpactLevel.HIGH
            },
            'io_operations': {
                'patterns': [r'open\(', r'requests\.', r'urllib\.', r'socket\.'],
                'impact': ImpactLevel.MEDIUM
            },
            'database_queries': {
                'patterns': [r'SELECT.*FROM', r'INSERT.*INTO', r'UPDATE.*SET', r'DELETE.*FROM'],
                'impact': ImpactLevel.MEDIUM
            },
            'network_calls': {
                'patterns': [r'requests\.get', r'requests\.post', r'urllib\.request', r'http\.client'],
                'impact': ImpactLevel.MEDIUM
            }
        }
    
    def _load_security_patterns(self) -> Dict[str, Dict]:
        """Load security analysis patterns"""
        return {
            'sql_injection': {
                'patterns': [r'execute\(.*\+', r'cursor\.execute\(.*%', r'query.*format\('],
                'severity': RiskLevel.HIGH
            },
            'xss_vulnerability': {
                'patterns': [r'innerHTML\s*=', r'document\.write\(', r'eval\('],
                'severity': RiskLevel.HIGH
            },
            'path_traversal': {
                'patterns': [r'open\(.*\.\.', r'os\.path\.join\(.*\.\.', r'file.*\.\.'],
                'severity': RiskLevel.MEDIUM
            },
            'hardcoded_secrets': {
                'patterns': [r'password\s*=\s*["\'][^"\']+["\']', r'api_key\s*=\s*["\'][^"\']+["\']', r'token\s*=\s*["\'][^"\']+["\']'],
                'severity': RiskLevel.CRITICAL
            },
            'insecure_random': {
                'patterns': [r'random\.random\(\)', r'random\.randint\(', r'random\.choice\('],
                'severity': RiskLevel.MEDIUM
            }
        }
    
    def analyze_dependencies(self, task: str) -> List[DependencyInfo]:
        """Phân tích dependencies thực tế"""
        dependencies = []
        
        # Parse task để tìm files sẽ bị ảnh hưởng
        affected_files = self._extract_affected_files(task)
        
        for file_path in affected_files:
            if file_path.exists() and file_path.suffix == '.py':
                file_deps = self._analyze_file_dependencies(file_path)
                dependencies.extend(file_deps)
        
        return dependencies
    
    def _extract_affected_files(self, task: str) -> List[Path]:
        """Extract files sẽ bị ảnh hưởng từ task description"""
        affected_files = []
        
        # Tìm file names trong task
        file_patterns = [
            r'(\w+\.py)',
            r'file\s+(\w+\.py)',
            r'(\w+/\w+\.py)',
            r'(\w+\\\w+\.py)'
        ]
        
        for pattern in file_patterns:
            matches = re.findall(pattern, task, re.IGNORECASE)
            for match in matches:
                # Tìm file trong project
                for py_file in self.python_files:
                    if py_file.name == match or str(py_file).endswith(match):
                        affected_files.append(py_file)
        
        # Nếu không tìm thấy file cụ thể, return một số file quan trọng
        if not affected_files:
            important_files = [
                self.project_root / "stillme_core" / "framework.py",
                self.project_root / "agent-dev" / "core" / "agentdev_unified.py"
            ]
            affected_files = [f for f in important_files if f.exists()]
        
        return affected_files
    
    def _analyze_file_dependencies(self, file_path: Path) -> List[DependencyInfo]:
        """Phân tích dependencies của một file"""
        dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dep = DependencyInfo(
                            module=alias.name,
                            file_path=str(file_path),
                            import_type='import',
                            line_number=node.lineno,
                            is_used=self._check_module_usage(content, alias.name),
                            usage_count=self._count_module_usage(content, alias.name)
                        )
                        dependencies.append(dep)
                
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        dep = DependencyInfo(
                            module=f"{module}.{alias.name}",
                            file_path=str(file_path),
                            import_type='from_import',
                            line_number=node.lineno,
                            is_used=self._check_module_usage(content, alias.name),
                            usage_count=self._count_module_usage(content, alias.name)
                        )
                        dependencies.append(dep)
        
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
        
        return dependencies
    
    def _check_module_usage(self, content: str, module_name: str) -> bool:
        """Kiểm tra module có được sử dụng không"""
        # Simple check - tìm module name trong content
        return module_name in content
    
    def _count_module_usage(self, content: str, module_name: str) -> int:
        """Đếm số lần module được sử dụng"""
        return content.count(module_name)
    
    def analyze_performance(self, task: str) -> PerformanceImpact:
        """Phân tích tác động hiệu suất"""
        affected_files = self._extract_affected_files(task)
        
        io_operations = 0
        network_calls = 0
        database_queries = 0
        caching_opportunities = []
        complexity_level = ImpactLevel.LOW
        
        for file_path in affected_files:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Analyze performance patterns
                for pattern_type, pattern_info in self.performance_patterns.items():
                    for pattern in pattern_info['patterns']:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        
                        if pattern_type == 'io_operations':
                            io_operations += len(matches)
                        elif pattern_type == 'network_calls':
                            network_calls += len(matches)
                        elif pattern_type == 'database_queries':
                            database_queries += len(matches)
                        elif pattern_type == 'high_complexity':
                            if matches:
                                complexity_level = pattern_info['impact']
                
                # Find caching opportunities
                if 'cache' not in content.lower() and ('expensive' in content.lower() or 'slow' in content.lower()):
                    caching_opportunities.append(f"Consider caching in {file_path.name}")
        
        # Determine overall impact level
        total_operations = io_operations + network_calls + database_queries
        if total_operations > 10 or complexity_level == ImpactLevel.HIGH:
            impact_level = ImpactLevel.HIGH
        elif total_operations > 5 or complexity_level == ImpactLevel.MEDIUM:
            impact_level = ImpactLevel.MEDIUM
        else:
            impact_level = ImpactLevel.LOW
        
        return PerformanceImpact(
            level=impact_level,
            estimated_time_complexity="O(n)" if complexity_level == ImpactLevel.LOW else "O(n²)" if complexity_level == ImpactLevel.MEDIUM else "O(2ⁿ)",
            memory_impact="Low" if impact_level == ImpactLevel.LOW else "Medium" if impact_level == ImpactLevel.MEDIUM else "High",
            io_operations=io_operations,
            network_calls=network_calls,
            database_queries=database_queries,
            caching_opportunities=caching_opportunities
        )
    
    def analyze_security(self, task: str) -> List[SecurityRisk]:
        """Phân tích rủi ro bảo mật"""
        security_risks = []
        affected_files = self._extract_affected_files(task)
        
        for file_path in affected_files:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check security patterns
                for risk_type, risk_info in self.security_patterns.items():
                    for pattern in risk_info['patterns']:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        
                        if matches:
                            risk = SecurityRisk(
                                risk_type=risk_type,
                                severity=risk_info['severity'],
                                description=f"Found {len(matches)} potential {risk_type} vulnerabilities",
                                affected_files=[str(file_path)],
                                mitigation_suggestions=self._get_mitigation_suggestions(risk_type)
                            )
                            security_risks.append(risk)
        
        return security_risks
    
    def _get_mitigation_suggestions(self, risk_type: str) -> List[str]:
        """Get mitigation suggestions for security risks"""
        suggestions = {
            'sql_injection': [
                "Use parameterized queries",
                "Implement input validation",
                "Use ORM with built-in protection"
            ],
            'xss_vulnerability': [
                "Sanitize user input",
                "Use Content Security Policy",
                "Escape output properly"
            ],
            'path_traversal': [
                "Validate file paths",
                "Use whitelist of allowed directories",
                "Implement proper access controls"
            ],
            'hardcoded_secrets': [
                "Use environment variables",
                "Implement secret management system",
                "Never commit secrets to version control"
            ],
            'insecure_random': [
                "Use cryptographically secure random",
                "Use secrets module for Python",
                "Implement proper random number generation"
            ]
        }
        return suggestions.get(risk_type, ["Review and fix security issue"])
    
    def analyze_maintainability(self, task: str) -> MaintainabilityScore:
        """Phân tích khả năng bảo trì"""
        affected_files = self._extract_affected_files(task)
        
        total_complexity = 0
        total_testability = 0
        total_documentation = 0
        total_coupling = 0
        total_cohesion = 0
        suggestions = []
        
        for file_path in affected_files:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Analyze complexity
                complexity = self._calculate_complexity(content)
                total_complexity += complexity
                
                # Analyze testability
                testability = self._calculate_testability(content)
                total_testability += testability
                
                # Analyze documentation
                documentation = self._calculate_documentation(content)
                total_documentation += documentation
                
                # Analyze coupling
                coupling = self._calculate_coupling(content)
                total_coupling += coupling
                
                # Analyze cohesion
                cohesion = self._calculate_cohesion(content)
                total_cohesion += cohesion
        
        # Calculate average scores
        file_count = len(affected_files) if affected_files else 1
        complexity_score = max(0, 1 - (total_complexity / file_count) / 10)  # Normalize to 0-1
        testability_score = total_testability / file_count
        documentation_score = total_documentation / file_count
        coupling_score = max(0, 1 - (total_coupling / file_count) / 5)  # Lower coupling is better
        cohesion_score = total_cohesion / file_count
        
        # Overall score
        overall_score = (complexity_score + testability_score + documentation_score + coupling_score + cohesion_score) / 5
        
        # Generate suggestions
        if complexity_score < 0.7:
            suggestions.append("Consider refactoring complex functions")
        if testability_score < 0.7:
            suggestions.append("Add more unit tests")
        if documentation_score < 0.7:
            suggestions.append("Improve code documentation")
        if coupling_score < 0.7:
            suggestions.append("Reduce coupling between modules")
        if cohesion_score < 0.7:
            suggestions.append("Improve module cohesion")
        
        return MaintainabilityScore(
            overall_score=overall_score,
            complexity_score=complexity_score,
            testability_score=testability_score,
            documentation_score=documentation_score,
            coupling_score=coupling_score,
            cohesion_score=cohesion_score,
            suggestions=suggestions
        )
    
    def _calculate_complexity(self, content: str) -> float:
        """Tính độ phức tạp của code"""
        # Simple complexity calculation based on control structures
        complexity_indicators = [
            r'\bif\b', r'\bfor\b', r'\bwhile\b', r'\btry\b', r'\bexcept\b',
            r'\bwith\b', r'\bdef\b', r'\bclass\b', r'\blambda\b'
        ]
        
        total_complexity = 0
        for pattern in complexity_indicators:
            matches = re.findall(pattern, content)
            total_complexity += len(matches)
        
        return total_complexity
    
    def _calculate_testability(self, content: str) -> float:
        """Tính khả năng test"""
        # Check for test-related patterns
        test_patterns = [r'\btest\b', r'\bassert\b', r'\bmock\b', r'\bunittest\b', r'\bpytest\b']
        test_count = 0
        
        for pattern in test_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            test_count += len(matches)
        
        # Normalize to 0-1
        return min(1.0, test_count / 10)
    
    def _calculate_documentation(self, content: str) -> float:
        """Tính chất lượng documentation"""
        # Check for docstrings and comments
        docstring_pattern = r'""".*?"""'
        comment_pattern = r'#.*'
        
        docstring_count = len(re.findall(docstring_pattern, content, re.DOTALL))
        comment_count = len(re.findall(comment_pattern, content))
        
        # Normalize to 0-1
        total_docs = docstring_count + comment_count
        return min(1.0, total_docs / 20)
    
    def _calculate_coupling(self, content: str) -> float:
        """Tính độ coupling"""
        # Count imports and external dependencies
        import_pattern = r'^(import|from)\s+'
        imports = len(re.findall(import_pattern, content, re.MULTILINE))
        
        # Higher imports = higher coupling
        return imports
    
    def _calculate_cohesion(self, content: str) -> float:
        """Tính độ cohesion"""
        # Check for related functions and classes
        function_pattern = r'def\s+\w+'
        class_pattern = r'class\s+\w+'
        
        functions = len(re.findall(function_pattern, content))
        classes = len(re.findall(class_pattern, content))
        
        # Higher cohesion = more related functions/classes
        return min(1.0, (functions + classes) / 10)
    
    def analyze_user_impact(self, task: str) -> UserImpact:
        """Phân tích tác động người dùng"""
        # Simple analysis based on task keywords
        breaking_keywords = ['remove', 'delete', 'deprecate', 'breaking', 'change api']
        feature_keywords = ['feature', 'new', 'add', 'implement']
        ui_keywords = ['ui', 'interface', 'frontend', 'user', 'display']
        
        task_lower = task.lower()
        
        breaking_changes = []
        affected_features = []
        user_experience_changes = []
        
        # Check for breaking changes
        for keyword in breaking_keywords:
            if keyword in task_lower:
                breaking_changes.append(f"Potential breaking change: {keyword}")
        
        # Check for feature changes
        for keyword in feature_keywords:
            if keyword in task_lower:
                affected_features.append(f"New feature: {keyword}")
        
        # Check for UI changes
        for keyword in ui_keywords:
            if keyword in task_lower:
                user_experience_changes.append(f"UI change: {keyword}")
        
        # Determine impact level
        if breaking_changes:
            impact_level = ImpactLevel.HIGH
        elif affected_features or user_experience_changes:
            impact_level = ImpactLevel.MEDIUM
        else:
            impact_level = ImpactLevel.LOW
        
        return UserImpact(
            level=impact_level,
            affected_features=affected_features,
            user_experience_changes=user_experience_changes,
            breaking_changes=breaking_changes,
            migration_required=len(breaking_changes) > 0,
            user_training_needed=len(affected_features) > 0
        )
    
    def analyze_business_value(self, task: str) -> BusinessValue:
        """Phân tích giá trị kinh doanh"""
        # Simple business value analysis
        high_value_keywords = ['performance', 'security', 'user experience', 'revenue', 'cost']
        medium_value_keywords = ['feature', 'improvement', 'optimization', 'bug fix']
        low_value_keywords = ['refactor', 'cleanup', 'documentation', 'test']
        
        task_lower = task.lower()
        
        # Calculate ROI based on keywords
        roi_score = 0
        for keyword in high_value_keywords:
            if keyword in task_lower:
                roi_score += 3
        
        for keyword in medium_value_keywords:
            if keyword in task_lower:
                roi_score += 2
        
        for keyword in low_value_keywords:
            if keyword in task_lower:
                roi_score += 1
        
        # Normalize ROI to 0-1
        roi_estimate = min(1.0, roi_score / 10)
        
        # Estimate costs (simplified)
        development_cost = 1000 if 'new' in task_lower else 500
        maintenance_cost = 200 if 'complex' in task_lower else 100
        
        return BusinessValue(
            roi_estimate=roi_estimate,
            user_satisfaction_impact="High" if roi_score > 5 else "Medium" if roi_score > 2 else "Low",
            market_competitiveness="High" if 'feature' in task_lower else "Medium",
            development_cost=development_cost,
            maintenance_cost=maintenance_cost,
            time_to_market="1-2 weeks" if 'simple' in task_lower else "2-4 weeks"
        )
    
    def analyze_impact(self, task: str) -> ImpactAnalysisResult:
        """Phân tích tác động toàn diện"""
        start_time = time.time()
        
        # Run all analyses
        dependencies = self.analyze_dependencies(task)
        performance = self.analyze_performance(task)
        security_risks = self.analyze_security(task)
        maintainability = self.analyze_maintainability(task)
        user_impact = self.analyze_user_impact(task)
        business_value = self.analyze_business_value(task)
        
        # Determine overall risk level
        risk_factors = []
        if performance.level in [ImpactLevel.HIGH, ImpactLevel.CRITICAL]:
            risk_factors.append(1)
        if any(risk.severity in [RiskLevel.HIGH, RiskLevel.CRITICAL] for risk in security_risks):
            risk_factors.append(1)
        if user_impact.level in [ImpactLevel.HIGH, ImpactLevel.CRITICAL]:
            risk_factors.append(1)
        if maintainability.overall_score < 0.5:
            risk_factors.append(1)
        
        if len(risk_factors) >= 3:
            overall_risk = RiskLevel.CRITICAL
        elif len(risk_factors) >= 2:
            overall_risk = RiskLevel.HIGH
        elif len(risk_factors) >= 1:
            overall_risk = RiskLevel.MEDIUM
        else:
            overall_risk = RiskLevel.LOW
        
        # Generate recommendations
        recommendations = []
        if performance.level == ImpactLevel.HIGH:
            recommendations.append("Consider performance optimization")
        if security_risks:
            recommendations.append("Address security vulnerabilities")
        if maintainability.overall_score < 0.7:
            recommendations.append("Improve code maintainability")
        if user_impact.migration_required:
            recommendations.append("Plan user migration strategy")
        
        analysis_time = time.time() - start_time
        
        return ImpactAnalysisResult(
            dependencies=dependencies,
            performance=performance,
            security_risks=security_risks,
            maintainability=maintainability,
            user_impact=user_impact,
            business_value=business_value,
            overall_risk_level=overall_risk,
            recommendations=recommendations,
            analysis_time=analysis_time
        )

# Test function
if __name__ == "__main__":
    analyzer = ImpactAnalyzer()
    result = analyzer.analyze_impact("Add new feature to improve user experience")
    
    print("=== IMPACT ANALYSIS RESULT ===")
    print(f"Overall Risk Level: {result.overall_risk_level.value}")
    print(f"Analysis Time: {result.analysis_time:.2f}s")
    print(f"Dependencies: {len(result.dependencies)}")
    print(f"Security Risks: {len(result.security_risks)}")
    print(f"Maintainability Score: {result.maintainability.overall_score:.2f}")
    print(f"Recommendations: {len(result.recommendations)}")
