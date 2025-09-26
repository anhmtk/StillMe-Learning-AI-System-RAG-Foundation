import os

# tests/test_enhanced_agentdev.py
"""
Comprehensive tests for enhanced AgentDev system
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from stillme_core.enhanced_executor import EnhancedExecutor, TestFramework, TestResult
from stillme_core.error_recovery import (
    CircuitBreakerConfig,
    ErrorRecoveryManager,
    RetryConfig,
)
from stillme_core.quality.quality_governor import QualityGovernor, QualityMetric
from stillme_core.risk.risk_assessor import RiskAssessor, RiskCategory, RiskLevel
from stillme_core.security.attack_simulator import AttackSimulator, AttackType
from stillme_core.security.security_scanner import SecurityScanner, VulnerabilityLevel


class TestEnhancedExecutor:
    """Test enhanced executor functionality"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.executor = EnhancedExecutor(self.temp_dir)

        # Create test files
        self._create_test_files()

    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir)

    def _create_test_files(self):
        """Create test files for testing"""
        # Create a simple Python file
        test_file = Path(self.temp_dir) / "test_sample.py"
        test_file.write_text(
            """
def test_simple():
    assert 1 + 1 == 2

def test_another():
    assert True
"""
        )

        # Create a unittest file
        unittest_file = Path(self.temp_dir) / "test_unittest.py"
        unittest_file.write_text(
            """
import unittest

class TestSample(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(1 + 1, 2)
    
    def test_another(self):
        self.assertTrue(True)
"""
        )

    def test_detect_test_framework(self):
        """Test test framework detection"""
        # Test pytest detection
        pytest_file = Path(self.temp_dir) / "test_pytest.py"
        pytest_file.write_text("import pytest\ndef test_something(): pass")

        framework = self.executor._detect_test_framework(str(pytest_file))
        assert framework == TestFramework.PYTEST

        # Test unittest detection
        framework = self.executor._detect_test_framework(
            str(Path(self.temp_dir) / "test_unittest.py")
        )
        assert framework == TestFramework.UNITTEST

    def test_analyze_test_impact(self):
        """Test test impact analysis"""
        changed_files = ["test_sample.py"]
        impact = self.executor.analyze_test_impact(changed_files)

        assert isinstance(impact.affected_tests, list)
        assert isinstance(impact.total_tests, int)
        assert isinstance(impact.impact_percent, float)
        assert isinstance(impact.recommended_tests, list)

    def test_generate_coverage_report(self):
        """Test coverage report generation"""
        # Mock test results
        test_results = [
            TestResult(
                framework=TestFramework.PYTEST,
                passed=5,
                failed=1,
                skipped=0,
                errors=0,
                duration=2.5,
                output="test output",
                error_output="",
                coverage_percent=85.0,
                test_files=["test_sample.py"],
            )
        ]

        report = self.executor.generate_coverage_report(test_results)

        assert "summary" in report
        assert "frameworks" in report
        assert "recommendations" in report
        assert report["summary"]["total_passed"] == 5
        assert report["summary"]["total_failed"] == 1
        assert report["summary"]["overall_coverage"] == 85.0


class TestSecurityScanner:
    """Test security scanner functionality"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.scanner = SecurityScanner(self.temp_dir)

        # Create test files with security issues
        self._create_test_files()

    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir)

    def _create_test_files(self):
        """Create test files with security issues"""
        # File with hardcoded password
        insecure_file = Path(self.temp_dir) / "insecure.py"
        insecure_file.write_text(
            """
password = os.getenv("PASSWORD", "default_password")
api_key = os.getenv("API_KEY", "")
"""
        )

        # File with SQL injection vulnerability
        sql_file = Path(self.temp_dir) / "sql_vuln.py"
        sql_file.write_text(
            """
query = "SELECT * FROM users WHERE id = " + user_id
"""
        )

    def test_secret_detection(self):
        """Test secret detection functionality"""
        issues = self.scanner._run_secret_detection()

        assert len(issues) > 0
        assert any(issue.tool == "secret_detection" for issue in issues)
        assert any("password" in issue.description.lower() for issue in issues)

    def test_custom_patterns(self):
        """Test custom vulnerability patterns"""
        issues = self.scanner._run_custom_patterns()

        assert len(issues) > 0
        assert any(issue.tool == "custom_patterns" for issue in issues)

    def test_generate_security_report(self):
        """Test security report generation"""
        # Mock security issues
        from stillme_core.security.security_scanner import SecurityIssue

        issues = [
            SecurityIssue(
                tool="custom_patterns",
                level=VulnerabilityLevel.HIGH,
                rule_id="sql_injection",
                description="Potential SQL injection",
                file_path="test.py",
                line_number=1,
                code_snippet="query = 'SELECT * FROM users WHERE id = ' + user_id",
                confidence="high",
            )
        ]

        report = self.scanner._generate_security_report(issues, 1.0)

        assert report.total_issues == 1
        assert report.issues_by_level[VulnerabilityLevel.HIGH] == 1
        assert len(report.recommendations) > 0
        assert report.risk_score > 0


class TestAttackSimulator:
    """Test attack simulator functionality"""

    def setup_method(self):
        """Setup test environment"""
        self.simulator = AttackSimulator("http://localhost:8000")

    def test_load_attack_payloads(self):
        """Test attack payload loading"""
        payloads = self.simulator._load_attack_payloads()

        assert AttackType.SQL_INJECTION in payloads
        assert AttackType.XSS in payloads
        assert AttackType.CSRF in payloads
        assert len(payloads[AttackType.SQL_INJECTION]) > 0

    def test_analyze_response(self):
        """Test response analysis"""
        # Mock response with SQL error
        mock_response = Mock()
        mock_response.text = "SQL syntax error near '1'"

        vulnerability = self.simulator._analyze_response(
            mock_response,
            AttackType.SQL_INJECTION,
            self.simulator.payloads[AttackType.SQL_INJECTION][0],
        )

        assert vulnerability == True

    def test_generate_attack_report(self):
        """Test attack report generation"""
        from stillme_core.security.attack_simulator import AttackResult

        # Mock attack results
        results = [
            AttackResult(
                attack_type=AttackType.SQL_INJECTION,
                payload="' OR '1'='1",
                success=True,
                response_code=200,
                response_time=0.5,
                response_body="success",
                vulnerability_detected=True,
                severity="high",
                recommendations=["Use parameterized queries"],
            )
        ]

        report = self.simulator._generate_attack_report(results, 1.0)

        assert report.total_attacks == 1
        assert report.successful_attacks == 1
        assert report.vulnerabilities_found == 1
        assert report.security_score < 100  # Should be penalized for vulnerability
        assert len(report.recommendations) > 0


class TestRiskAssessor:
    """Test risk assessor functionality"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.assessor = RiskAssessor(self.temp_dir)

        # Create test files with risks
        self._create_test_files()

    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir)

    def _create_test_files(self):
        """Create test files with risks"""
        # File with hardcoded credentials
        risky_file = Path(self.temp_dir) / "risky.py"
        risky_file.write_text(
            """
password = os.getenv("PASSWORD", "")
try:
    pass
except:
    pass
"""
        )

        # File with complex function
        complex_file = Path(self.temp_dir) / "complex.py"
        complex_file.write_text(
            """
def complex_function():
    if True:
        if True:
            if True:
                if True:
                    if True:
                        return "too complex"
"""
        )

    def test_analyze_file_risks(self):
        """Test file risk analysis"""
        risky_file = Path(self.temp_dir) / "risky.py"
        risks = self.assessor._analyze_file_risks(risky_file)

        assert len(risks) > 0
        assert any(risk.category == RiskCategory.SECURITY for risk in risks)
        assert any(risk.level == RiskLevel.HIGH for risk in risks)

    def test_calculate_risk_score(self):
        """Test risk score calculation"""
        from stillme_core.risk.risk_assessor import RiskFactor

        # Mock risk factors
        risks = [
            RiskFactor(
                category=RiskCategory.SECURITY,
                level=RiskLevel.HIGH,
                description="Hardcoded password",
                file_path="test.py",
                line_number=1,
                code_snippet="password = os.getenv("PASSWORD", "")",
                impact="Security breach",
                probability=0.8,
                mitigation="Use environment variables",
            )
        ]

        score = self.assessor._calculate_overall_risk_score(risks)
        assert 0 <= score <= 100
        assert score > 0  # Should have some risk score

    def test_generate_risk_recommendations(self):
        """Test risk recommendation generation"""
        from stillme_core.risk.risk_assessor import RiskFactor

        risks = [
            RiskFactor(
                category=RiskCategory.SECURITY,
                level=RiskLevel.CRITICAL,
                description="Critical security issue",
                file_path="test.py",
                line_number=1,
                code_snippet="",
                impact="Critical impact",
                probability=1.0,
                mitigation="Fix immediately",
            )
        ]

        recommendations = self.assessor._generate_risk_recommendations(
            risks, {RiskLevel.CRITICAL: 1}
        )

        assert len(recommendations) > 0
        assert any("CRITICAL" in rec for rec in recommendations)


class TestQualityGovernor:
    """Test quality governor functionality"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.governor = QualityGovernor(self.temp_dir)

        # Create test files
        self._create_test_files()

    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir)

    def _create_test_files(self):
        """Create test files for quality analysis"""
        # Simple file
        simple_file = Path(self.temp_dir) / "simple.py"
        simple_file.write_text(
            """
def simple_function():
    \"\"\"Simple function with docstring\"\"\"
    return 42
"""
        )

        # Complex file
        complex_file = Path(self.temp_dir) / "complex.py"
        complex_file.write_text(
            """
def complex_function():
    if True:
        if True:
            if True:
                if True:
                    if True:
                        if True:
                            if True:
                                if True:
                                    if True:
                                        if True:
                                            return "very complex"
"""
        )

    def test_calculate_file_metrics(self):
        """Test file metrics calculation"""
        simple_file = Path(self.temp_dir) / "simple.py"
        metrics = self.governor._calculate_file_metrics(simple_file)

        assert QualityMetric.CYCLOMATIC_COMPLEXITY in metrics
        assert QualityMetric.DOCUMENTATION_COVERAGE in metrics
        assert QualityMetric.MAINTAINABILITY_INDEX in metrics
        assert metrics[QualityMetric.CYCLOMATIC_COMPLEXITY] >= 1

    def test_calculate_cyclomatic_complexity(self):
        """Test cyclomatic complexity calculation"""
        # Simple AST for testing
        import ast

        # Simple function
        simple_code = "def test(): return 1"
        simple_tree = ast.parse(simple_code)
        complexity = self.governor._calculate_cyclomatic_complexity(simple_tree)
        assert complexity == 1

        # Complex function
        complex_code = """
def test():
    if True:
        if True:
            for i in range(10):
                if i > 5:
                    return i
"""
        complex_tree = ast.parse(complex_code)
        complexity = self.governor._calculate_cyclomatic_complexity(complex_tree)
        assert complexity > 1

    def test_calculate_overall_quality_score(self):
        """Test overall quality score calculation"""
        # Mock metrics summary
        metrics_summary = {
            QualityMetric.CYCLOMATIC_COMPLEXITY: {"average": 5.0},
            QualityMetric.DOCUMENTATION_COVERAGE: {"average": 0.8},
            QualityMetric.MAINTAINABILITY_INDEX: {"average": 80.0},
        }

        score = self.governor._calculate_overall_quality_score(metrics_summary, [])
        assert 0 <= score <= 100


class TestErrorRecovery:
    """Test error recovery functionality"""

    def setup_method(self):
        """Setup test environment"""
        self.recovery_manager = ErrorRecoveryManager()

    def test_retry_manager(self):
        """Test retry manager functionality"""
        from stillme_core.error_recovery import RetryManager

        config = RetryConfig(max_attempts=3, base_delay=0.1)
        retry_manager = RetryManager(config)

        # Test successful operation
        def success_func():
            return "success"

        result = retry_manager.execute(success_func)
        assert result.success == True
        assert result.result == "success"
        assert result.attempts == 1

        # Test failing operation
        def fail_func():
            raise ValueError("test error")

        result = retry_manager.execute(fail_func)
        assert result.success == False
        assert result.attempts == 3
        assert isinstance(result.error, ValueError)

    def test_circuit_breaker(self):
        """Test circuit breaker functionality"""
        from stillme_core.error_recovery import (
            CircuitBreaker,
            CircuitState,
        )

        config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=1.0)
        circuit_breaker = CircuitBreaker("test", config)

        # Test normal operation
        def success_func():
            return "success"

        result = circuit_breaker.call(success_func)
        assert result == "success"
        assert circuit_breaker.state == CircuitState.CLOSED

        # Test failure threshold
        def fail_func():
            raise ValueError("test error")

        # First failure
        try:
            circuit_breaker.call(fail_func)
        except ValueError:
            pass

        # Second failure - should open circuit
        try:
            circuit_breaker.call(fail_func)
        except ValueError:
            pass

        assert circuit_breaker.state == CircuitState.OPEN

        # Test circuit open
        try:
            circuit_breaker.call(success_func)
            assert False, "Should have raised exception"
        except Exception as e:
            assert "OPEN" in str(e)

    def test_execute_with_recovery(self):
        """Test full error recovery execution"""

        # Test successful operation
        def success_func():
            return "success"

        result = self.recovery_manager.execute_with_recovery(success_func)
        assert result.success == True
        assert result.result == "success"

        # Test failing operation
        def fail_func():
            raise ValueError("test error")

        result = self.recovery_manager.execute_with_recovery(fail_func)
        assert result.success == False
        assert isinstance(result.error, ValueError)

    def test_get_operation_stats(self):
        """Test operation statistics"""
        stats = self.recovery_manager.get_operation_stats()

        assert "total_operations" in stats
        assert "success_rate" in stats
        assert "circuit_breakers" in stats
        assert isinstance(stats["total_operations"], int)


# Integration tests
class TestIntegration:
    """Integration tests for enhanced AgentDev system"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()

        # Create a complete test project
        self._create_test_project()

    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir)

    def _create_test_project(self):
        """Create a complete test project"""
        # Create main module
        main_file = Path(self.temp_dir) / "main.py"
        main_file.write_text(
            """
def calculate_sum(a, b):
    \"\"\"Calculate sum of two numbers\"\"\"
    return a + b

def calculate_product(a, b):
    \"\"\"Calculate product of two numbers\"\"\"
    return a * b
"""
        )

        # Create test file
        test_file = Path(self.temp_dir) / "test_main.py"
        test_file.write_text(
            """
import pytest
from main import calculate_sum, calculate_product

def test_calculate_sum():
    assert calculate_sum(2, 3) == 5

def test_calculate_product():
    assert calculate_product(2, 3) == 6
"""
        )

        # Create requirements.txt
        requirements_file = Path(self.temp_dir) / "requirements.txt"
        requirements_file.write_text("pytest==7.0.0\nrequests==2.28.0\n")

    def test_full_quality_assessment(self):
        """Test full quality assessment workflow"""
        governor = QualityGovernor(self.temp_dir)
        report = governor.assess_code_quality()

        assert report.overall_score >= 0
        assert report.overall_score <= 100
        assert len(report.metrics_summary) > 0
        assert len(report.recommendations) > 0

    def test_full_risk_assessment(self):
        """Test full risk assessment workflow"""
        assessor = RiskAssessor(self.temp_dir)
        report = assessor.assess_repository_risks()

        assert report.overall_risk_score >= 0
        assert report.overall_risk_score <= 100
        assert len(report.risk_factors) >= 0
        assert len(report.recommendations) > 0

    def test_full_security_scan(self):
        """Test full security scan workflow"""
        scanner = SecurityScanner(self.temp_dir)
        report = scanner.scan_repository()

        assert report.total_issues >= 0
        assert len(report.issues_by_level) > 0
        assert len(report.recommendations) > 0
        assert report.risk_score >= 0
        assert report.risk_score <= 100


if __name__ == "__main__":
    pytest.main([__file__])
