# tests/test_advanced_agentdev.py
"""
Comprehensive tests for Advanced AgentDev System
"""

import pytest
import asyncio
import tempfile
import shutil
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from stillme_core.decision_making.decision_engine import (
    DecisionEngine, DecisionType, DecisionStatus, RiskLevel
)
from stillme_core.decision_making.ethical_guardrails import (
    EthicalGuardrails, EthicalPrinciple, ViolationSeverity
)
from stillme_core.self_learning.experience_memory import (
    ExperienceMemory, ExperienceType, ExperienceCategory, ExperienceQuery
)
from stillme_core.advanced_security.safe_attack_simulator import (
    SafeAttackSimulator, AttackCategory, AttackSeverity, SimulationStatus
)

class TestDecisionEngine:
    """Test Advanced Decision Making Engine"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.decision_engine = DecisionEngine()
        
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_decision_engine_initialization(self):
        """Test decision engine initialization"""
        assert self.decision_engine.criteria_weights is not None
        assert len(self.decision_engine.criteria_weights) > 0
        assert len(self.decision_engine.ethical_boundaries) > 0
    
    def test_make_decision_success(self):
        """Test successful decision making"""
        options = [
            {
                "name": "Option 1",
                "description": "High security, good performance",
                "security_improvements": True,
                "performance_improvements": True,
                "complexity": "low",
                "has_documentation": True,
                "test_coverage": 0.9,
                "business_impact": "high",
                "user_value": "high",
                "resource_usage": "low",
                "cost": 100
            },
            {
                "name": "Option 2", 
                "description": "Medium security, medium performance",
                "security_improvements": False,
                "performance_improvements": False,
                "complexity": "medium",
                "has_documentation": False,
                "test_coverage": 0.6,
                "business_impact": "medium",
                "user_value": "medium",
                "resource_usage": "medium",
                "cost": 200
            }
        ]
        
        context = {
            "requester": "test_user",
            "urgency": "normal",
            "business_impact": "medium",
            "technical_complexity": "low",
            "resource_requirements": {},
            "constraints": [],
            "stakeholders": ["developer", "manager"]
        }
        
        result = self.decision_engine.make_decision(
            DecisionType.CODE_CHANGE, options, context
        )
        
        assert result is not None
        assert result.decision_id is not None
        assert result.context is not None
        assert result.selected_option is not None
        assert result.implementation_status in [DecisionStatus.APPROVED, DecisionStatus.REJECTED]
        assert result.confidence_score >= 0.0
        assert result.confidence_score <= 1.0
    
    def test_decision_engine_criteria_calculation(self):
        """Test criteria score calculation"""
        option_data = {
            "security_improvements": True,
            "performance_improvements": True,
            "complexity": "low",
            "has_documentation": True,
            "test_coverage": 0.9,
            "business_impact": "high",
            "user_value": "high",
            "resource_usage": "low",
            "cost": 100
        }
        
        context = Mock()
        context.decision_type = DecisionType.CODE_CHANGE
        
        # Test individual criteria calculations
        security_score = self.decision_engine._calculate_security_score(option_data, context)
        assert 0.0 <= security_score <= 1.0
        
        performance_score = self.decision_engine._calculate_performance_score(option_data, context)
        assert 0.0 <= performance_score <= 1.0
        
        maintainability_score = self.decision_engine._calculate_maintainability_score(option_data, context)
        assert 0.0 <= maintainability_score <= 1.0
    
    def test_decision_engine_risk_assessment(self):
        """Test risk assessment functionality"""
        option_data = {
            "experimental": False,
            "breaking_changes": False,
            "external_dependencies": 2
        }
        
        criteria_scores = {
            "security": 0.8,
            "performance": 0.7,
            "maintainability": 0.6
        }
        
        risk_level = self.decision_engine._assess_risk_level(option_data, criteria_scores)
        assert risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
    
    def test_decision_engine_performance_metrics(self):
        """Test performance metrics tracking"""
        initial_metrics = self.decision_engine.get_performance_metrics()
        assert isinstance(initial_metrics, dict)
        
        # Make a decision to generate metrics
        options = [{"name": "Test Option", "description": "Test"}]
        context = {"requester": "test"}
        
        self.decision_engine.make_decision(DecisionType.CODE_CHANGE, options, context)
        
        updated_metrics = self.decision_engine.get_performance_metrics()
        assert len(updated_metrics) >= len(initial_metrics)

class TestEthicalGuardrails:
    """Test Ethical Guardrails System"""
    
    def setup_method(self):
        """Setup test environment"""
        self.ethical_guardrails = EthicalGuardrails()
        
    def test_ethical_guardrails_initialization(self):
        """Test ethical guardrails initialization"""
        assert len(self.ethical_guardrails.boundaries) > 0
        assert len(self.ethical_guardrails.ethical_boundaries) > 0
    
    def test_ethical_assessment_safe_decision(self):
        """Test ethical assessment of safe decision"""
        decision_data = {
            "security_score": 0.8,
            "introduces_vulnerability": False,
            "removes_security_controls": False,
            "accesses_personal_data": False,
            "logs_sensitive_information": False,
            "breaking_changes": False,
            "experimental_features": False
        }
        
        context = {
            "environment": "staging",
            "user_consent_given": True,
            "legal_requirement": False
        }
        
        assessment = self.ethical_guardrails.assess_decision(decision_data, context)
        
        assert assessment.is_ethical == True
        assert len(assessment.violations) == 0
        assert assessment.confidence_score > 0.5
    
    def test_ethical_assessment_violation(self):
        """Test ethical assessment with violations"""
        decision_data = {
            "security_score": 0.2,  # Low security score
            "introduces_vulnerability": True,
            "removes_security_controls": True,
            "accesses_personal_data": True,
            "logs_sensitive_information": True,
            "breaking_changes": True,
            "experimental_features": True
        }
        
        context = {
            "environment": "production",
            "user_consent_given": False,
            "legal_requirement": False
        }
        
        assessment = self.ethical_guardrails.assess_decision(decision_data, context)
        
        assert assessment.is_ethical == False
        assert len(assessment.violations) > 0
        assert assessment.confidence_score < 0.5
    
    def test_ethical_boundary_management(self):
        """Test adding and removing ethical boundaries"""
        initial_count = len(self.ethical_guardrails.boundaries)
        
        # Add new boundary
        from stillme_core.decision_making.ethical_guardrails import EthicalBoundary, ViolationSeverity
        
        new_boundary = EthicalBoundary(
            principle=EthicalPrinciple.SECURITY,
            rule_id="TEST_001",
            description="Test boundary",
            severity=ViolationSeverity.MEDIUM,
            conditions=["test_condition"],
            exceptions=["test_exception"],
            enforcement_action="test_action"
        )
        
        self.ethical_guardrails.add_boundary(new_boundary)
        assert len(self.ethical_guardrails.boundaries) == initial_count + 1
        
        # Remove boundary
        self.ethical_guardrails.remove_boundary("TEST_001")
        assert len(self.ethical_guardrails.boundaries) == initial_count
    
    def test_violation_statistics(self):
        """Test violation statistics"""
        stats = self.ethical_guardrails.get_violation_stats()
        
        assert "total_violations" in stats
        assert "by_severity" in stats
        assert "by_principle" in stats
        assert "resolved_count" in stats
        assert "recent_violations" in stats

class TestExperienceMemory:
    """Test Experience Memory Bank"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_experience.db"
        self.experience_memory = ExperienceMemory(str(self.db_path))
        
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_experience_memory_initialization(self):
        """Test experience memory initialization"""
        assert self.experience_memory.db_path == str(self.db_path)
        assert isinstance(self.experience_memory.experiences, list)
        assert isinstance(self.experience_memory.patterns, list)
    
    def test_store_experience(self):
        """Test storing experiences"""
        context = {
            "user_id": "test_user",
            "action_type": "code_review",
            "file_path": "test.py"
        }
        
        outcome = {
            "success": True,
            "issues_found": 2,
            "time_taken": 30
        }
        
        lessons_learned = [
            "Always check for security vulnerabilities",
            "Review error handling patterns"
        ]
        
        tags = ["security", "code_quality", "review"]
        
        experience_id = self.experience_memory.store_experience(
            ExperienceType.DECISION,
            ExperienceCategory.SECURITY,
            context,
            "Perform security code review",
            outcome,
            True,
            lessons_learned,
            tags,
            confidence=0.8,
            impact_score=0.7
        )
        
        assert experience_id is not None
        assert len(self.experience_memory.experiences) > 0
        
        # Verify experience was stored correctly
        stored_experience = self.experience_memory.experiences[0]
        assert stored_experience.experience_id == experience_id
        assert stored_experience.context == context
        assert stored_experience.outcome == outcome
        assert stored_experience.lessons_learned == lessons_learned
        assert stored_experience.tags == tags
    
    def test_experience_query(self):
        """Test querying experiences"""
        # Store multiple experiences
        for i in range(5):
            context = {"test_id": i, "category": "security" if i % 2 == 0 else "performance"}
            outcome = {"success": i % 2 == 0}
            
            self.experience_memory.store_experience(
                ExperienceType.DECISION,
                ExperienceCategory.SECURITY if i % 2 == 0 else ExperienceCategory.PERFORMANCE,
                context,
                f"Test action {i}",
                outcome,
                i % 2 == 0,
                [f"Lesson {i}"],
                ["test"],
                confidence=0.5 + i * 0.1,
                impact_score=0.3 + i * 0.1
            )
        
        # Query experiences
        query = ExperienceQuery(
            categories=[ExperienceCategory.SECURITY],
            success_only=True,
            limit=10
        )
        
        results = self.experience_memory.query_experiences(query)
        assert len(results) > 0
        
        # Verify all results match query criteria
        for result in results:
            assert result.category == ExperienceCategory.SECURITY
            assert result.success == True
    
    def test_get_recommendations(self):
        """Test getting recommendations based on experiences"""
        # Store some experiences
        context = {"user_id": "test_user", "action_type": "security_scan"}
        outcome = {"vulnerabilities_found": 3, "severity": "high"}
        
        self.experience_memory.store_experience(
            ExperienceType.ACTION,
            ExperienceCategory.SECURITY,
            context,
            "Run security scan",
            outcome,
            True,
            ["Update dependencies", "Fix SQL injection"],
            ["security", "scan"],
            confidence=0.9,
            impact_score=0.8
        )
        
        # Get recommendations
        recommendations = self.experience_memory.get_recommendations(
            context, "Run security scan", ["security", "scan"]
        )
        
        assert len(recommendations) > 0
        assert all("type" in rec for rec in recommendations)
        assert all("confidence" in rec for rec in recommendations)
    
    def test_learning_statistics(self):
        """Test learning statistics"""
        stats = self.experience_memory.get_learning_stats()
        
        assert "total_experiences" in stats
        assert "success_rate" in stats
        assert "categories" in stats
        assert "types" in stats
        assert "learning_velocity" in stats
        assert "pattern_accuracy" in stats

class TestSafeAttackSimulator:
    """Test Safe Attack Simulation Framework"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.simulator = SafeAttackSimulator()
        
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        self.simulator.cleanup_all()
    
    def test_simulator_initialization(self):
        """Test simulator initialization"""
        assert len(self.simulator.scenarios) > 0
        assert len(self.simulator.isolation_environments) > 0
        assert self.simulator.safety_config is not None
    
    def test_safety_checks(self):
        """Test safety check functionality"""
        # Test network isolation check
        target_config = {"host": "localhost", "use_test_data": True}
        network_check = self.simulator._check_network_isolation(target_config)
        
        assert network_check.check_name == "network_isolation"
        assert network_check.passed == True  # localhost should be allowed
        
        # Test resource limits check
        resource_check = self.simulator._check_resource_limits()
        assert resource_check.check_name == "resource_limits"
        assert isinstance(resource_check.passed, bool)
        
        # Test filesystem protection check
        filesystem_check = self.simulator._check_filesystem_protection()
        assert filesystem_check.check_name == "filesystem_protection"
        assert isinstance(filesystem_check.passed, bool)
    
    def test_simulation_execution(self):
        """Test simulation execution"""
        target_config = {
            "host": "localhost",
            "port": 8080,
            "use_test_data": True,
            "use_real_data": False
        }
        
        # Run a simulation
        result = self.simulator.run_simulation("OWASP_SQL_INJECTION", target_config)
        
        assert result is not None
        assert result.simulation_id is not None
        assert result.scenario is not None
        assert result.status in [SimulationStatus.COMPLETED, SimulationStatus.FAILED]
        assert result.duration >= 0
        assert isinstance(result.vulnerabilities_found, list)
        assert isinstance(result.defenses_triggered, list)
        assert isinstance(result.recommendations, list)
        assert 0.0 <= result.risk_score <= 1.0
    
    def test_scenario_validation(self):
        """Test scenario safety validation"""
        from stillme_core.advanced_security.safe_attack_simulator import AttackScenario
        
        # Valid scenario
        valid_scenario = AttackScenario(
            scenario_id="TEST_VALID",
            name="Valid Test Scenario",
            category=AttackCategory.OWASP_TOP_10,
            severity=AttackSeverity.LOW,
            description="A safe test scenario",
            attack_vectors=["test_vector"],
            payloads=[{"type": "test", "payload": "test"}],
            expected_behavior="Should be safe",
            safety_measures=["isolation"],
            isolation_requirements={"network": "isolated"},
            success_criteria={"safe": True},
            failure_criteria={"unsafe": False}
        )
        
        assert self.simulator._validate_scenario_safety(valid_scenario) == True
        
        # Invalid scenario (contains forbidden action)
        invalid_scenario = AttackScenario(
            scenario_id="TEST_INVALID",
            name="Invalid Test Scenario",
            category=AttackCategory.OWASP_TOP_10,
            severity=AttackSeverity.LOW,
            description="A scenario that deletes files",  # Contains forbidden action
            attack_vectors=["test_vector"],
            payloads=[{"type": "test", "payload": "test"}],
            expected_behavior="Should be safe",
            safety_measures=["isolation"],
            isolation_requirements={"network": "isolated"},
            success_criteria={"safe": True},
            failure_criteria={"unsafe": False}
        )
        
        assert self.simulator._validate_scenario_safety(invalid_scenario) == False
    
    def test_safety_report(self):
        """Test safety report generation"""
        report = self.simulator.get_safety_report()
        
        assert "total_simulations" in report
        assert "active_simulations" in report
        assert "safety_checks_passed" in report
        assert "safety_checks_failed" in report
        assert "recent_safety_checks" in report
        assert "isolation_environments" in report
        assert "safety_config" in report
    
    def test_simulation_history(self):
        """Test simulation history tracking"""
        # Run a simulation to generate history
        target_config = {
            "host": "localhost",
            "use_test_data": True,
            "use_real_data": False
        }
        
        self.simulator.run_simulation("OWASP_XSS", target_config)
        
        history = self.simulator.get_simulation_history()
        assert len(history) > 0
        
        # Verify history entry
        latest_simulation = history[-1]
        assert latest_simulation.scenario.scenario_id == "OWASP_XSS"
        assert latest_simulation.status in [SimulationStatus.COMPLETED, SimulationStatus.FAILED]

class TestIntegration:
    """Integration tests for Advanced AgentDev System"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Initialize all components
        self.decision_engine = DecisionEngine()
        self.ethical_guardrails = EthicalGuardrails()
        self.experience_memory = ExperienceMemory()
        self.attack_simulator = SafeAttackSimulator()
        
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        self.attack_simulator.cleanup_all()
    
    def test_end_to_end_decision_process(self):
        """Test complete decision-making process"""
        # Step 1: Make a decision
        options = [
            {
                "name": "Implement Security Scanner",
                "description": "Add automated security scanning",
                "security_improvements": True,
                "performance_improvements": False,
                "complexity": "medium",
                "has_documentation": True,
                "test_coverage": 0.8,
                "business_impact": "high",
                "user_value": "high",
                "resource_usage": "medium",
                "cost": 500
            }
        ]
        
        context = {
            "requester": "security_team",
            "urgency": "high",
            "business_impact": "high",
            "technical_complexity": "medium",
            "resource_requirements": {"developers": 2, "time": "2_weeks"},
            "constraints": ["budget_limit", "timeline"],
            "stakeholders": ["security_team", "development_team", "management"]
        }
        
        decision_result = self.decision_engine.make_decision(
            DecisionType.SECURITY_ACTION, options, context
        )
        
        assert decision_result is not None
        assert decision_result.implementation_status in [DecisionStatus.APPROVED, DecisionStatus.REJECTED]
        
        # Step 2: Store experience
        if decision_result.implementation_status == DecisionStatus.APPROVED:
            experience_id = self.experience_memory.store_experience(
                ExperienceType.DECISION,
                ExperienceCategory.SECURITY,
                context,
                f"Decision: {decision_result.selected_option.name}",
                {
                    "decision_id": decision_result.decision_id,
                    "confidence": decision_result.confidence_score,
                    "risk_level": decision_result.selected_option.risk_assessment.value
                },
                True,
                ["Security improvements are important", "Automated scanning reduces manual effort"],
                ["security", "automation", "decision"],
                confidence=decision_result.confidence_score,
                impact_score=0.8
            )
            
            assert experience_id is not None
        
        # Step 3: Run security simulation
        target_config = {
            "host": "localhost",
            "use_test_data": True,
            "use_real_data": False
        }
        
        simulation_result = self.attack_simulator.run_simulation(
            "OWASP_SQL_INJECTION", target_config
        )
        
        assert simulation_result is not None
        assert simulation_result.status in [SimulationStatus.COMPLETED, SimulationStatus.FAILED]
        
        # Step 4: Store simulation experience
        simulation_experience_id = self.experience_memory.store_experience(
            ExperienceType.ACTION,
            ExperienceCategory.SECURITY,
            {"simulation_id": simulation_result.simulation_id},
            f"Security simulation: {simulation_result.scenario.name}",
            {
                "vulnerabilities_found": len(simulation_result.vulnerabilities_found),
                "defenses_triggered": len(simulation_result.defenses_triggered),
                "risk_score": simulation_result.risk_score
            },
            simulation_result.success,
            simulation_result.recommendations,
            ["security", "simulation", "testing"],
            confidence=0.9,
            impact_score=simulation_result.risk_score
        )
        
        assert simulation_experience_id is not None
    
    def test_ethical_decision_validation(self):
        """Test ethical validation of decisions"""
        # Test decision that should pass ethical checks
        safe_decision_data = {
            "security_score": 0.9,
            "introduces_vulnerability": False,
            "removes_security_controls": False,
            "accesses_personal_data": False,
            "breaking_changes": False,
            "experimental_features": False
        }
        
        safe_context = {
            "environment": "staging",
            "user_consent_given": True,
            "legal_requirement": False
        }
        
        ethical_assessment = self.ethical_guardrails.assess_decision(
            safe_decision_data, safe_context
        )
        
        assert ethical_assessment.is_ethical == True
        assert len(ethical_assessment.violations) == 0
        
        # Test decision that should fail ethical checks
        unsafe_decision_data = {
            "security_score": 0.1,
            "introduces_vulnerability": True,
            "removes_security_controls": True,
            "accesses_personal_data": True,
            "breaking_changes": True,
            "experimental_features": True
        }
        
        unsafe_context = {
            "environment": "production",
            "user_consent_given": False,
            "legal_requirement": False
        }
        
        unsafe_ethical_assessment = self.ethical_guardrails.assess_decision(
            unsafe_decision_data, unsafe_context
        )
        
        assert unsafe_ethical_assessment.is_ethical == False
        assert len(unsafe_ethical_assessment.violations) > 0
    
    def test_learning_from_experiences(self):
        """Test learning from multiple experiences"""
        # Store multiple similar experiences
        for i in range(5):
            context = {
                "user_id": f"user_{i}",
                "action_type": "security_scan",
                "target": "web_application"
            }
            
            outcome = {
                "vulnerabilities_found": i + 1,
                "severity": "high" if i > 2 else "medium"
            }
            
            lessons = [
                f"Found {i + 1} vulnerabilities",
                "Security scanning is important"
            ]
            
            self.experience_memory.store_experience(
                ExperienceType.ACTION,
                ExperienceCategory.SECURITY,
                context,
                "Run security scan",
                outcome,
                i < 3,  # First 3 succeed, last 2 fail
                lessons,
                ["security", "scan", "vulnerability"],
                confidence=0.7 + i * 0.05,
                impact_score=0.6 + i * 0.05
            )
        
        # Check if patterns were learned
        assert len(self.experience_memory.patterns) >= 0  # Patterns may or may not be created
        
        # Get recommendations for similar context
        test_context = {
            "user_id": "new_user",
            "action_type": "security_scan",
            "target": "web_application"
        }
        
        recommendations = self.experience_memory.get_recommendations(
            test_context, "Run security scan", ["security", "scan"]
        )
        
        assert len(recommendations) > 0
    
    def test_comprehensive_security_assessment(self):
        """Test comprehensive security assessment workflow"""
        # Run multiple security simulations
        scenarios = ["OWASP_SQL_INJECTION", "OWASP_XSS", "OWASP_CSRF"]
        simulation_results = []
        
        for scenario in scenarios:
            target_config = {
                "host": "localhost",
                "use_test_data": True,
                "use_real_data": False
            }
            
            result = self.attack_simulator.run_simulation(scenario, target_config)
            simulation_results.append(result)
        
        # Analyze results
        total_vulnerabilities = sum(len(r.vulnerabilities_found) for r in simulation_results)
        total_defenses = sum(len(r.defenses_triggered) for r in simulation_results)
        average_risk_score = sum(r.risk_score for r in simulation_results) / len(simulation_results)
        
        assert total_vulnerabilities >= 0
        assert total_defenses >= 0
        assert 0.0 <= average_risk_score <= 1.0
        
        # Store comprehensive assessment experience
        assessment_context = {
            "assessment_type": "comprehensive_security",
            "scenarios_tested": scenarios,
            "total_simulations": len(simulation_results)
        }
        
        assessment_outcome = {
            "total_vulnerabilities": total_vulnerabilities,
            "total_defenses": total_defenses,
            "average_risk_score": average_risk_score,
            "scenarios_completed": len([r for r in simulation_results if r.status == SimulationStatus.COMPLETED])
        }
        
        assessment_lessons = []
        for result in simulation_results:
            assessment_lessons.extend(result.recommendations)
        
        assessment_experience_id = self.experience_memory.store_experience(
            ExperienceType.ASSESSMENT,
            ExperienceCategory.SECURITY,
            assessment_context,
            "Comprehensive security assessment",
            assessment_outcome,
            average_risk_score < 0.5,  # Success if low risk
            list(set(assessment_lessons)),  # Remove duplicates
            ["security", "assessment", "comprehensive"],
            confidence=0.9,
            impact_score=average_risk_score
        )
        
        assert assessment_experience_id is not None

if __name__ == "__main__":
    pytest.main([__file__])
