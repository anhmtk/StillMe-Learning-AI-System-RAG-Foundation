"""
End-to-end scenarios for basic AgentDev tasks
Real-world scenarios that test complete functionality
"""

import pytest
import sys
import os
from pathlib import Path
import time

# Add agent-dev path to sys.path
agent_dev_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'agent-dev', 'core')
if agent_dev_path not in sys.path:
    sys.path.insert(0, agent_dev_path)

from fixtures import TestFixtures

# E2E Scenarios
SCENARIOS = [
    {
        "name": "Fix Simple Bug",
        "input": "Fix NullPointerException in user authentication",
        "expected": "code fixed, test pass",
        "category": "bug_fix"
    },
    {
        "name": "Basic Refactor", 
        "input": "Refactor function with bad naming conventions",
        "expected": "improved naming, functionality preserved",
        "category": "refactor"
    },
    {
        "name": "Add Simple Feature",
        "input": "Add input validation to contact form",
        "expected": "feature implemented, tests pass",
        "category": "feature"
    },
    {
        "name": "Security Fix",
        "input": "Fix SQL injection vulnerability in login",
        "expected": "vulnerability patched, security improved",
        "category": "security"
    },
    {
        "name": "Performance Optimization",
        "input": "Optimize database query performance",
        "expected": "performance improved, functionality preserved",
        "category": "performance"
    },
    {
        "name": "Test Creation",
        "input": "Create unit tests for payment module",
        "expected": "comprehensive tests created",
        "category": "testing"
    },
    {
        "name": "Documentation",
        "input": "Add API documentation for user endpoints",
        "expected": "documentation created and updated",
        "category": "documentation"
    },
    {
        "name": "Conflict Resolution",
        "input": "Resolve merge conflicts in main branch",
        "expected": "conflicts resolved, code merged",
        "category": "conflict"
    },
    {
        "name": "Code Review",
        "input": "Review code quality and suggest improvements",
        "expected": "review completed, suggestions provided",
        "category": "review"
    },
    {
        "name": "System Monitoring",
        "input": "Monitor system health and performance",
        "expected": "monitoring active, issues detected",
        "category": "monitoring"
    }
]

class TestE2EScenarios:
    """Test end-to-end scenarios"""
    
    @pytest.mark.parametrize("scenario", SCENARIOS)
    def test_e2e_scenario(self, scenario):
        """Test individual E2E scenario"""
        try:
            from agentdev_unified_simple import AgentDevUnified, AgentMode
            
            temp_project = TestFixtures.create_temp_project()
            agentdev = AgentDevUnified(str(temp_project))
            
            # Execute scenario
            start_time = time.time()
            result = agentdev.execute_task(scenario["input"], AgentMode.SENIOR)
            end_time = time.time()
            
            execution_time = end_time - start_time
            
            # Assertions
            assert result is not None, f"Scenario {scenario['name']} returned None"
            assert "✅" in result or "success" in result.lower(), f"Scenario {scenario['name']} failed: {result}"
            
            # Performance check (should complete within 5 seconds)
            assert execution_time <= 5, f"Scenario {scenario['name']} took {execution_time}s, expected ≤ 5s"
            
            # Log scenario result
            print(f"\n✅ E2E Scenario: {scenario['name']}")
            print(f"   Input: {scenario['input']}")
            print(f"   Expected: {scenario['expected']}")
            print(f"   Result: {result[:100]}...")
            print(f"   Time: {execution_time:.2f}s")
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("AgentDevUnified not available")
    
    def test_bug_fix_scenarios(self):
        """Test all bug fix scenarios"""
        bug_scenarios = [s for s in SCENARIOS if s["category"] == "bug_fix"]
        
        try:
            from agentdev_unified_simple import AgentDevUnified, AgentMode
            
            temp_project = TestFixtures.create_temp_project()
            agentdev = AgentDevUnified(str(temp_project))
            
            results = []
            for scenario in bug_scenarios:
                result = agentdev.execute_task(scenario["input"], AgentMode.SENIOR)
                results.append(result)
            
            # All bug fix scenarios should succeed
            assert len(results) == len(bug_scenarios)
            for result in results:
                assert "✅" in result or "success" in result.lower()
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("AgentDevUnified not available")
    
    def test_security_scenarios(self):
        """Test all security scenarios"""
        security_scenarios = [s for s in SCENARIOS if s["category"] == "security"]
        
        try:
            from agentdev_unified_simple import AgentDevUnified, AgentMode
            
            temp_project = TestFixtures.create_temp_project()
            agentdev = AgentDevUnified(str(temp_project))
            
            results = []
            for scenario in security_scenarios:
                result = agentdev.execute_task(scenario["input"], AgentMode.SENIOR)
                results.append(result)
            
            # All security scenarios should succeed
            assert len(results) == len(security_scenarios)
            for result in results:
                assert "✅" in result or "success" in result.lower()
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("AgentDevUnified not available")
    
    def test_feature_development_scenarios(self):
        """Test feature development scenarios"""
        feature_scenarios = [s for s in SCENARIOS if s["category"] in ["feature", "refactor"]]
        
        try:
            from agentdev_unified_simple import AgentDevUnified, AgentMode
            
            temp_project = TestFixtures.create_temp_project()
            agentdev = AgentDevUnified(str(temp_project))
            
            results = []
            for scenario in feature_scenarios:
                result = agentdev.execute_task(scenario["input"], AgentMode.SENIOR)
                results.append(result)
            
            # All feature scenarios should succeed
            assert len(results) == len(feature_scenarios)
            for result in results:
                assert "✅" in result or "success" in result.lower()
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("AgentDevUnified not available")
    
    def test_complex_workflow(self):
        """Test complex multi-step workflow"""
        try:
            from agentdev_unified_simple import AgentDevUnified, AgentMode
            
            temp_project = TestFixtures.create_temp_project()
            agentdev = AgentDevUnified(str(temp_project))
            
            # Complex workflow: Plan → Implement → Test → Review
            workflow_steps = [
                "Plan implementation of user authentication system",
                "Implement secure login functionality",
                "Create comprehensive tests for authentication",
                "Review code quality and security"
            ]
            
            results = []
            for step in workflow_steps:
                result = agentdev.execute_task(step, AgentMode.SENIOR)
                results.append(result)
            
            # All workflow steps should succeed
            assert len(results) == 4
            for result in results:
                assert "✅" in result or "success" in result.lower()
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("AgentDevUnified not available")
    
    def test_error_recovery_scenarios(self):
        """Test error recovery scenarios"""
        try:
            from agentdev_unified_simple import AgentDevUnified, AgentMode
            
            temp_project = TestFixtures.create_temp_project()
            agentdev = AgentDevUnified(str(temp_project))
            
            # Test error recovery
            error_scenarios = [
                "Fix broken build after failed merge",
                "Recover from database connection failure",
                "Handle memory leak in production system"
            ]
            
            results = []
            for scenario in error_scenarios:
                result = agentdev.execute_task(scenario, AgentMode.SENIOR)
                results.append(result)
            
            # Should handle errors gracefully
            assert len(results) == 3
            for result in results:
                assert result is not None
                # Should either succeed or provide helpful error message
                assert "✅" in result or "success" in result.lower() or "❌" in result or "error" in result.lower()
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("AgentDevUnified not available")

class TestRealWorldScenarios:
    """Test real-world scenarios"""
    
    def test_production_incident_response(self):
        """Test production incident response scenario"""
        try:
            from agentdev_unified_simple import AgentDevUnified, AgentMode
            
            temp_project = TestFixtures.create_temp_project()
            agentdev = AgentDevUnified(str(temp_project))
            
            # Production incident scenario
            incident_tasks = [
                "Investigate production system outage",
                "Identify root cause of performance degradation",
                "Implement hotfix for critical bug",
                "Monitor system recovery"
            ]
            
            results = []
            for task in incident_tasks:
                result = agentdev.execute_task(task, AgentMode.SENIOR)
                results.append(result)
            
            # All incident response tasks should complete
            assert len(results) == 4
            for result in results:
                assert "✅" in result or "success" in result.lower()
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("AgentDevUnified not available")
    
    def test_technical_debt_management(self):
        """Test technical debt management scenario"""
        try:
            from agentdev_unified_simple import AgentDevUnified, AgentMode
            
            temp_project = TestFixtures.create_temp_project()
            agentdev = AgentDevUnified(str(temp_project))
            
            # Technical debt management
            debt_tasks = [
                "Identify technical debt in codebase",
                "Prioritize debt reduction tasks",
                "Refactor legacy code modules",
                "Update outdated dependencies"
            ]
            
            results = []
            for task in debt_tasks:
                result = agentdev.execute_task(task, AgentMode.SENIOR)
                results.append(result)
            
            # All debt management tasks should complete
            assert len(results) == 4
            for result in results:
                assert "✅" in result or "success" in result.lower()
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("AgentDevUnified not available")
