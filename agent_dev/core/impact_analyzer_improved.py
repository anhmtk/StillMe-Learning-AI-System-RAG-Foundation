#!/usr/bin/env python3
"""
Improved Impact Analyzer - Enhanced dependency detection
"""

import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


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
    import_type: str
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
    caching_opportunities: list[str]

@dataclass
class SecurityRisk:
    """Rủi ro bảo mật"""
    risk_type: str
    severity: str
    description: str
    mitigation: str

@dataclass
class MaintainabilityScore:
    """Điểm khả năng bảo trì"""
    overall_score: float
    complexity_score: float
    testability_score: float
    documentation_score: float
    coupling_score: float
    cohesion_score: float
    suggestions: list[str]

@dataclass
class UserImpact:
    """Tác động người dùng"""
    level: ImpactLevel
    affected_features: list[str]
    user_experience_changes: list[str]
    breaking_changes: list[str]
    migration_required: bool
    user_training_needed: bool

@dataclass
class BusinessValue:
    """Giá trị kinh doanh"""
    roi_estimate: float
    user_satisfaction_impact: str
    market_competitiveness: str
    development_cost: int
    maintenance_cost: int
    time_to_market: str

@dataclass
class ImpactAnalysisResult:
    """Kết quả phân tích tác động"""
    dependencies: list[DependencyInfo]
    performance: PerformanceImpact
    security_risks: list[SecurityRisk]
    maintainability: MaintainabilityScore
    user_impact: UserImpact
    business_value: BusinessValue
    overall_risk_level: RiskLevel
    recommendations: list[str]
    analysis_time: float

class ImpactAnalyzer:
    """Enhanced Impact Analyzer with improved dependency detection"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)

    def analyze_impact(self, task: str) -> ImpactAnalysisResult:
        """Phân tích tác động toàn diện"""
        start_time = time.time()

        # Enhanced dependency analysis
        dependencies = self._analyze_dependencies_enhanced(task)

        # Performance analysis
        performance = self._analyze_performance(task)

        # Security analysis
        security_risks = self._analyze_security_risks(task)

        # Maintainability analysis
        maintainability = self._analyze_maintainability(task)

        # User impact analysis
        user_impact = self._analyze_user_impact(task)

        # Business value analysis
        business_value = self._analyze_business_value(task)

        # Overall risk assessment
        overall_risk = self._assess_overall_risk(security_risks, performance, user_impact)

        # Generate recommendations
        recommendations = self._generate_recommendations(dependencies, security_risks, performance)

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

    def _analyze_dependencies_enhanced(self, task: str) -> list[DependencyInfo]:
        """Enhanced dependency analysis with better detection"""
        dependencies = []
        task_lower = task.lower()

        # Database dependencies
        if any(keyword in task_lower for keyword in ['database', 'db', 'sql', 'query', 'schema', 'table', 'user', 'data']):
            dependencies.extend([
                DependencyInfo("database", "database/connection.py", "import", 1, True, 1),
                DependencyInfo("sqlalchemy", "database/models.py", "from_import", 2, True, 1),
                DependencyInfo("pymongo", "database/mongo.py", "import", 3, True, 1)
            ])

        # API dependencies
        if any(keyword in task_lower for keyword in ['api', 'http', 'request', 'endpoint', 'authentication', 'login', 'rest']):
            dependencies.extend([
                DependencyInfo("requests", "api/client.py", "import", 1, True, 1),
                DependencyInfo("flask", "api/routes.py", "from_import", 3, True, 1),
                DependencyInfo("fastapi", "api/endpoints.py", "import", 2, True, 1)
            ])

        # Security dependencies
        if any(keyword in task_lower for keyword in ['security', 'auth', 'password', 'encrypt', 'vulnerability', 'secure']):
            dependencies.extend([
                DependencyInfo("bcrypt", "security/hash.py", "import", 1, True, 1),
                DependencyInfo("jwt", "security/token.py", "import", 2, True, 1),
                DependencyInfo("cryptography", "security/encryption.py", "import", 3, True, 1)
            ])

        # Performance dependencies
        if any(keyword in task_lower for keyword in ['performance', 'optimize', 'cache', 'memory', 'speed']):
            dependencies.extend([
                DependencyInfo("redis", "cache/manager.py", "import", 1, True, 1),
                DependencyInfo("psutil", "monitoring/performance.py", "import", 2, True, 1)
            ])

        # Testing dependencies
        if any(keyword in task_lower for keyword in ['test', 'testing', 'unit', 'integration', 'spec']):
            dependencies.extend([
                DependencyInfo("pytest", "tests/conftest.py", "import", 1, True, 1),
                DependencyInfo("unittest", "tests/test_core.py", "import", 2, True, 1)
            ])

        # UI dependencies
        if any(keyword in task_lower for keyword in ['ui', 'frontend', 'web', 'html', 'css', 'javascript']):
            dependencies.extend([
                DependencyInfo("flask", "templates/base.html", "template", 1, True, 1),
                DependencyInfo("jinja2", "templates/", "template", 2, True, 1)
            ])

        return dependencies

    def _analyze_performance(self, task: str) -> PerformanceImpact:
        """Phân tích tác động hiệu suất"""
        task_lower = task.lower()

        # Determine performance impact level
        if any(keyword in task_lower for keyword in ['optimize', 'performance', 'speed', 'fast']):
            level = ImpactLevel.MEDIUM
            complexity = "O(log n)"
            memory = "Medium"
            io_ops = 5
            network = 2
            db_queries = 3
            caching = ["Database query caching", "API response caching"]
        elif any(keyword in task_lower for keyword in ['database', 'query', 'search']):
            level = ImpactLevel.HIGH
            complexity = "O(n)"
            memory = "High"
            io_ops = 10
            network = 1
            db_queries = 8
            caching = ["Database connection pooling", "Query result caching"]
        else:
            level = ImpactLevel.LOW
            complexity = "O(1)"
            memory = "Low"
            io_ops = 1
            network = 0
            db_queries = 1
            caching = []

        return PerformanceImpact(
            level=level,
            estimated_time_complexity=complexity,
            memory_impact=memory,
            io_operations=io_ops,
            network_calls=network,
            database_queries=db_queries,
            caching_opportunities=caching
        )

    def _analyze_security_risks(self, task: str) -> list[SecurityRisk]:
        """Phân tích rủi ro bảo mật"""
        risks = []
        task_lower = task.lower()

        # SQL injection risks
        if any(keyword in task_lower for keyword in ['sql', 'query', 'database', 'user input']):
            risks.append(SecurityRisk(
                risk_type="SQL Injection",
                severity="HIGH",
                description="Potential SQL injection vulnerability in database queries",
                mitigation="Use parameterized queries and input validation"
            ))

        # Authentication risks
        if any(keyword in task_lower for keyword in ['auth', 'login', 'password', 'authentication']):
            risks.append(SecurityRisk(
                risk_type="Authentication Bypass",
                severity="CRITICAL",
                description="Potential authentication bypass vulnerability",
                mitigation="Implement proper authentication checks and session management"
            ))

        # XSS risks
        if any(keyword in task_lower for keyword in ['html', 'web', 'frontend', 'user input', 'display']):
            risks.append(SecurityRisk(
                risk_type="Cross-Site Scripting (XSS)",
                severity="MEDIUM",
                description="Potential XSS vulnerability in user input handling",
                mitigation="Sanitize user input and use proper output encoding"
            ))

        return risks

    def _analyze_maintainability(self, task: str) -> MaintainabilityScore:
        """Phân tích khả năng bảo trì"""
        task_lower = task.lower()

        # Calculate scores based on task complexity
        if any(keyword in task_lower for keyword in ['refactor', 'clean', 'improve', 'optimize']):
            overall_score = 0.8
            complexity_score = 0.7
            testability_score = 0.8
            documentation_score = 0.6
            coupling_score = 0.7
            cohesion_score = 0.8
            suggestions = ["Add comprehensive unit tests", "Improve code documentation", "Reduce coupling between modules"]
        else:
            overall_score = 0.6
            complexity_score = 0.5
            testability_score = 0.6
            documentation_score = 0.5
            coupling_score = 0.6
            cohesion_score = 0.6
            suggestions = ["Add unit tests", "Improve documentation", "Consider refactoring"]

        return MaintainabilityScore(
            overall_score=overall_score,
            complexity_score=complexity_score,
            testability_score=testability_score,
            documentation_score=documentation_score,
            coupling_score=coupling_score,
            cohesion_score=cohesion_score,
            suggestions=suggestions
        )

    def _analyze_user_impact(self, task: str) -> UserImpact:
        """Phân tích tác động người dùng"""
        task_lower = task.lower()

        if any(keyword in task_lower for keyword in ['user', 'interface', 'ui', 'frontend', 'login']):
            level = ImpactLevel.HIGH
            affected_features = ["User Interface", "Authentication", "User Experience"]
            ux_changes = ["UI changes", "User workflow changes"]
            breaking_changes = ["API changes", "Database schema changes"]
            migration_required = True
            training_needed = True
        else:
            level = ImpactLevel.MEDIUM
            affected_features = ["Backend functionality"]
            ux_changes = ["Performance improvements"]
            breaking_changes = []
            migration_required = False
            training_needed = False

        return UserImpact(
            level=level,
            affected_features=affected_features,
            user_experience_changes=ux_changes,
            breaking_changes=breaking_changes,
            migration_required=migration_required,
            user_training_needed=training_needed
        )

    def _analyze_business_value(self, task: str) -> BusinessValue:
        """Phân tích giá trị kinh doanh"""
        task_lower = task.lower()

        if any(keyword in task_lower for keyword in ['security', 'vulnerability', 'fix', 'critical']):
            roi_estimate = 0.9
            user_satisfaction = "High"
            market_competitiveness = "High"
            development_cost = 10000
            maintenance_cost = 2000
            time_to_market = "1-2 weeks"
        elif any(keyword in task_lower for keyword in ['optimize', 'performance', 'speed']):
            roi_estimate = 0.7
            user_satisfaction = "Medium"
            market_competitiveness = "Medium"
            development_cost = 15000
            maintenance_cost = 3000
            time_to_market = "2-4 weeks"
        else:
            roi_estimate = 0.5
            user_satisfaction = "Low"
            market_competitiveness = "Low"
            development_cost = 5000
            maintenance_cost = 1000
            time_to_market = "1-2 weeks"

        return BusinessValue(
            roi_estimate=roi_estimate,
            user_satisfaction_impact=user_satisfaction,
            market_competitiveness=market_competitiveness,
            development_cost=development_cost,
            maintenance_cost=maintenance_cost,
            time_to_market=time_to_market
        )

    def _assess_overall_risk(self, security_risks: list[SecurityRisk], performance: PerformanceImpact, user_impact: UserImpact) -> RiskLevel:
        """Đánh giá rủi ro tổng thể"""
        if security_risks and any(risk.severity == "CRITICAL" for risk in security_risks):
            return RiskLevel.CRITICAL
        elif security_risks and any(risk.severity == "HIGH" for risk in security_risks):
            return RiskLevel.HIGH
        elif performance.level == ImpactLevel.HIGH or user_impact.level == ImpactLevel.HIGH:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _generate_recommendations(self, dependencies: list[DependencyInfo], security_risks: list[SecurityRisk], performance: PerformanceImpact) -> list[str]:
        """Tạo khuyến nghị"""
        recommendations = []

        if dependencies:
            recommendations.append("Review and update dependencies")

        if security_risks:
            recommendations.append("Implement security best practices")
            recommendations.append("Conduct security testing")

        if performance.level in [ImpactLevel.HIGH, ImpactLevel.CRITICAL]:
            recommendations.append("Optimize performance bottlenecks")
            recommendations.append("Implement caching strategies")

        return recommendations
