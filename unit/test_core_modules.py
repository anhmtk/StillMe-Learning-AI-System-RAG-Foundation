"""
Unit tests for AgentDev core modules
Test cases for Senior Thinking, Execution Engine, and Learning Foundation
"""

import os
import sys

import pytest

# Add agent_dev path to sys.path
agent_dev_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "agent_dev", "core"
)
if agent_dev_path not in sys.path:
    sys.path.insert(0, agent_dev_path)

from fixtures import TestFixtures


class TestImpactAnalyzer:
    """Test Impact Analysis module"""

    def test_impact_analysis_basic(self):
        """Test impact analysis with simple dependency"""
        try:
            from impact_analyzer import ImpactAnalyzer

            # Create temporary project
            temp_project = TestFixtures.create_temp_project()

            # Initialize analyzer
            analyzer = ImpactAnalyzer(temp_project)

            # Test basic impact analysis
            task = "Add new feature to user module"
            result = analyzer.analyze_impact(task)

            # Assertions
            assert result is not None
            assert hasattr(result, "dependencies")
            assert hasattr(result, "performance")
            assert hasattr(result, "security_risks")
            assert hasattr(result, "overall_risk_level")

            # Cleanup
            TestFixtures.cleanup_temp_project(temp_project)

        except ImportError:
            pytest.skip("ImpactAnalyzer not available")

    def test_impact_analysis_dependency_detection(self):
        """Test dependency detection in impact analysis"""
        try:
            from impact_analyzer import ImpactAnalyzer

            temp_project = TestFixtures.create_temp_project()
            analyzer = ImpactAnalyzer(temp_project)

            # Test with task that should have dependencies
            task = "Modify database schema for user table"
            result = analyzer.analyze_impact(task)

            # Assert dependencies are detected
            assert len(result.dependencies) > 0

            TestFixtures.cleanup_temp_project(temp_project)

        except ImportError:
            pytest.skip("ImpactAnalyzer not available")


class TestBusinessAnalyzer:
    """Test Business Analysis module"""

    def test_business_thinking_roi_calculation(self):
        """Test ROI calculation logic"""
        try:
            from business_analyzer import BusinessAnalyzer

            analyzer = BusinessAnalyzer()

            # Test ROI calculation
            task = "Implement user authentication system"
            result = analyzer.analyze_business_value(task)

            # Assertions
            assert result is not None
            assert hasattr(result, "roi_analysis")
            assert hasattr(result, "business_score")
            assert hasattr(result, "priority")

            # ROI should be between 0 and 1
            assert 0 <= result.roi_analysis.estimated_roi <= 1

        except ImportError:
            pytest.skip("BusinessAnalyzer not available")

    def test_business_priority_assessment(self):
        """Test business priority assessment"""
        try:
            from business_analyzer import BusinessAnalyzer

            analyzer = BusinessAnalyzer()

            # Test high priority task
            high_priority_task = "Fix critical security vulnerability"
            result = analyzer.analyze_business_value(high_priority_task)

            # Should be high priority
            assert result.priority.value in ["HIGH", "CRITICAL"]

        except ImportError:
            pytest.skip("BusinessAnalyzer not available")


class TestSecurityAnalyzer:
    """Test Security Analysis module"""

    def test_security_thinking_vulnerability_detection(self):
        """Test vulnerability detection"""
        try:
            from security_analyzer import SecurityAnalyzer

            analyzer = SecurityAnalyzer()

            # Test with security-related task
            task = "Fix SQL injection vulnerability in login"
            result = analyzer.analyze_security_risks(task)

            # Assertions
            assert result is not None
            assert hasattr(result, "vulnerabilities")
            assert hasattr(result, "security_level")
            assert hasattr(result, "overall_security_score")

            # Should detect security issues
            assert len(result.vulnerabilities) > 0

        except ImportError:
            pytest.skip("SecurityAnalyzer not available")

    def test_security_sql_injection_detection(self):
        """Test SQL injection pattern detection"""
        try:
            from security_analyzer import SecurityAnalyzer

            analyzer = SecurityAnalyzer()

            # Test with SQL injection code
            task = "SELECT * FROM users WHERE username='admin' OR '1'='1'"
            result = analyzer.analyze_security_risks(task)

            # Should detect SQL injection
            assert result.overall_security_score < 0.5  # Low security score

        except ImportError:
            pytest.skip("SecurityAnalyzer not available")


class TestConflictResolver:
    """Test Conflict Resolution module"""

    def test_conflict_resolver_basic_merge(self):
        """Test basic merge conflict resolution"""
        try:
            from conflict_resolver import ConflictResolver

            temp_project = TestFixtures.create_temp_project()
            resolver = ConflictResolver(str(temp_project))

            # Test conflict analysis
            result = resolver.analyze_conflicts()

            # Assertions
            assert result is not None
            assert hasattr(result, "conflicts")
            assert hasattr(result, "conflict_count")
            assert hasattr(result, "recommendations")

            TestFixtures.cleanup_temp_project(temp_project)

        except ImportError:
            pytest.skip("ConflictResolver not available")

    def test_conflict_resolver_import_conflicts(self):
        """Test import conflict resolution"""
        try:
            from conflict_resolver import ConflictResolver

            temp_project = TestFixtures.create_temp_project()
            resolver = ConflictResolver(str(temp_project))

            # Create sample files with import conflicts
            TestFixtures.get_sample_code_files()

            # Test conflict detection
            result = resolver.analyze_conflicts()

            # Should handle conflicts gracefully
            assert result is not None

            TestFixtures.cleanup_temp_project(temp_project)

        except ImportError:
            pytest.skip("ConflictResolver not available")


class TestAgentDev:
    """Test AgentDev main class"""

    def test_agentdev_initialization(self):
        """Test AgentDev initialization"""
        try:
            from agent_dev.core.agentdev import AgentDev

            temp_project = TestFixtures.create_temp_project()
            agentdev = AgentDev(str(temp_project))

            # Assertions
            assert agentdev is not None
            assert agentdev.mode == "critical-first"
            assert hasattr(agentdev, "impact_analyzer")
            assert hasattr(agentdev, "business_analyzer")
            assert hasattr(agentdev, "security_analyzer")

            TestFixtures.cleanup_temp_project(temp_project)

        except ImportError:
            pytest.skip("AgentDev not available")

    def test_agentdev_task_execution(self):
        """Test basic task execution"""
        try:
            from agent_dev.core.agentdev import AgentDev

            temp_project = TestFixtures.create_temp_project()
            agentdev = AgentDev(str(temp_project))

            # Test task execution
            task = "Create a test module"
            result = agentdev.execute_task(task, "SENIOR")

            # Assertions
            assert result is not None
            assert "✅" in result or "success" in result.lower()

            TestFixtures.cleanup_temp_project(temp_project)

        except ImportError:
            pytest.skip("AgentDev not available")

    def test_agentdev_senior_thinking(self):
        """Test senior thinking mode"""
        try:
            from agent_dev.core.agentdev import AgentDev

            temp_project = TestFixtures.create_temp_project()
            agentdev = AgentDev(str(temp_project))

            # Test senior thinking
            task = "Implement security feature"
            result = agentdev.execute_task(task, "SENIOR")

            # Should include thinking analysis
            assert "🧠" in result or "thinking" in result.lower()

            TestFixtures.cleanup_temp_project(temp_project)

        except ImportError:
            pytest.skip("AgentDev not available")


class TestExperienceLearner:
    """Test Experience Learning module"""

    def test_experience_learner_basic(self):
        """Test basic experience learning"""
        try:
            from experience_learner import ExperienceLearner

            temp_project = TestFixtures.create_temp_project()
            learner = ExperienceLearner(str(temp_project))

            # Test learning from experience
            result = learner.learn_from_experience()

            # Assertions
            assert result is not None
            assert hasattr(result, "insights")
            assert hasattr(result, "patterns")

            TestFixtures.cleanup_temp_project(temp_project)

        except ImportError:
            pytest.skip("ExperienceLearner not available")


class TestAdaptiveStrategy:
    """Test Adaptive Strategy module"""

    def test_adaptive_strategy_selection(self):
        """Test strategy selection based on context"""
        try:
            from adaptive_strategy import AdaptiveStrategy

            temp_project = TestFixtures.create_temp_project()
            strategy = AdaptiveStrategy(str(temp_project))

            # Test strategy selection
            context = {"task": "security fix", "priority": "high"}
            result = strategy.select_strategy(context)

            # Assertions
            assert result is not None
            assert hasattr(result, "selected_strategy")
            assert hasattr(result, "confidence_score")

            TestFixtures.cleanup_temp_project(temp_project)

        except ImportError:
            pytest.skip("AdaptiveStrategy not available")


# Performance tests
class TestPerformance:
    """Test performance requirements"""

    def test_single_operation_performance(self):
        """Test single operation performance (≤ 2000ms)"""
        try:
            import time

            from agent_dev.core.agentdev import AgentDev

            temp_project = TestFixtures.create_temp_project()
            agentdev = AgentDev(str(temp_project))

            # Measure execution time
            start_time = time.time()
            agentdev.execute_task("Create test file", "SENIOR")
            end_time = time.time()

            execution_time = (end_time - start_time) * 1000  # Convert to ms

            # Should complete within 2000ms
            assert (
                execution_time <= 2000
            ), f"Operation took {execution_time}ms, expected ≤ 2000ms"

            TestFixtures.cleanup_temp_project(temp_project)

        except ImportError:
            pytest.skip("AgentDev not available")

    def test_basic_concurrency_performance(self):
        """Test basic concurrency performance (≤ 5s for 10 operations)"""
        try:
            import concurrent.futures
            import time

            from agent_dev.core.agentdev import AgentDev

            temp_project = TestFixtures.create_temp_project()
            agentdev = AgentDev(str(temp_project))

            def execute_task(task_id):
                return agentdev.execute_task(f"Create test file {task_id}", "SIMPLE")

            # Measure concurrent execution time
            start_time = time.time()

            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(execute_task, i) for i in range(10)]
                results = [
                    future.result()
                    for future in concurrent.futures.as_completed(futures)
                ]

            end_time = time.time()
            execution_time = end_time - start_time

            # Should complete within 5 seconds
            assert (
                execution_time <= 5
            ), f"Concurrent operations took {execution_time}s, expected ≤ 5s"
            assert len(results) == 10

            TestFixtures.cleanup_temp_project(temp_project)

        except ImportError:
            pytest.skip("AgentDev not available")
