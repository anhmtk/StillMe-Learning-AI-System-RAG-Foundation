#!/usr/bin/env python3
"""
Unit tests for Impact Analysis Module
Tests property-based behavior and edge cases
"""

import tempfile
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

# Import AgentDev modules
from agent_dev.core.impact_analyzer_improved import (
    ImpactAnalysisResult,
    ImpactAnalyzer,
    RiskLevel,
)


class TestImpactAnalyzer:
    """Test cases for Impact Analysis Module"""

    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.analyzer = ImpactAnalyzer(project_root=self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.unit
    def test_impact_analyzer_initialization(self):
        """Test ImpactAnalyzer initialization"""
        assert self.analyzer is not None
        assert hasattr(self.analyzer, "analyze_impact")
        assert hasattr(self.analyzer, "project_root")
        assert self.analyzer.project_root == Path(self.temp_dir)

    @pytest.mark.unit
    def test_analyze_impact_basic(self):
        """Test basic impact analysis"""
        # Test data
        change_data = {
            "files_affected": ["main.py", "utils.py"],
            "lines_changed": 50,
            "functions_modified": 3,
            "dependencies": ["requests", "numpy"],
        }

        result = self.analyzer.analyze_impact(change_data)

        assert isinstance(result, ImpactAnalysisResult)
        assert result.risk_level in [
            RiskLevel.LOW,
            RiskLevel.MEDIUM,
            RiskLevel.HIGH,
            RiskLevel.CRITICAL,
        ]
        assert result.impact_score >= 0.0
        assert result.impact_score <= 1.0
        assert result.analysis_time > 0

    @pytest.mark.unit
    @given(
        files_count=st.integers(min_value=1, max_value=100),
        lines_count=st.integers(min_value=1, max_value=1000),
        functions_count=st.integers(min_value=1, max_value=50),
    )
    def test_impact_analyzer_monotonicity(
        self, files_count, lines_count, functions_count
    ):
        """Property test: Impact score should be monotonic with respect to changes"""
        # Base change
        base_change = {
            "files_affected": ["file1.py"],
            "lines_changed": 10,
            "functions_modified": 1,
            "dependencies": ["requests"],
        }

        # Larger change
        larger_change = {
            "files_affected": ["file1.py"] * files_count,
            "lines_changed": lines_count,
            "functions_modified": functions_count,
            "dependencies": ["requests", "numpy", "pandas"],
        }

        base_result = self.analyzer.analyze_impact(base_change)
        larger_result = self.analyzer.analyze_impact(larger_change)

        # Impact score should not decrease with more changes
        assert larger_result.impact_score >= base_result.impact_score

    @pytest.mark.unit
    def test_dependency_cycle_detection(self):
        """Test dependency cycle detection raises risk level"""
        # Create circular dependency scenario
        change_with_cycle = {
            "files_affected": ["module_a.py", "module_b.py", "module_c.py"],
            "lines_changed": 100,
            "functions_modified": 5,
            "dependencies": ["module_a", "module_b", "module_c"],  # Circular
            "dependency_cycles": True,
        }

        result = self.analyzer.analyze_impact(change_with_cycle)

        # Should detect cycle and raise risk level
        assert result.risk_level in [
            RiskLevel.MEDIUM,
            RiskLevel.HIGH,
            RiskLevel.CRITICAL,
        ]
        assert (
            "cycle" in result.recommendations.lower()
            or "circular" in result.recommendations.lower()
        )

    @pytest.mark.unit
    def test_security_impact_assessment(self):
        """Test security impact assessment"""
        # High security impact change
        security_change = {
            "files_affected": ["auth.py", "security.py"],
            "lines_changed": 200,
            "functions_modified": 10,
            "dependencies": ["cryptography", "bcrypt"],
            "security_impact": True,
            "vulnerabilities": ["CVE-2024-0001", "CVE-2024-0002"],
        }

        result = self.analyzer.analyze_impact(security_change)

        # Should have high security impact
        assert result.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        assert "security" in result.recommendations.lower()

    @pytest.mark.unit
    def test_performance_impact_assessment(self):
        """Test performance impact assessment"""
        # Performance-critical change
        performance_change = {
            "files_affected": ["algorithm.py", "optimizer.py"],
            "lines_changed": 500,
            "functions_modified": 20,
            "dependencies": ["numpy", "scipy"],
            "performance_impact": True,
            "complexity_increase": True,
        }

        result = self.analyzer.analyze_impact(performance_change)

        # Should consider performance impact
        assert result.impact_score > 0.5  # High impact
        assert (
            "performance" in result.recommendations.lower()
            or "optimization" in result.recommendations.lower()
        )

    @pytest.mark.unit
    def test_empty_change_handling(self):
        """Test handling of empty or minimal changes"""
        empty_change = {
            "files_affected": [],
            "lines_changed": 0,
            "functions_modified": 0,
            "dependencies": [],
        }

        result = self.analyzer.analyze_impact(empty_change)

        # Should handle empty changes gracefully
        assert result.risk_level == RiskLevel.LOW
        assert result.impact_score == 0.0

    @pytest.mark.unit
    def test_invalid_input_handling(self):
        """Test handling of invalid inputs"""
        # Test with None values
        with pytest.raises((ValueError, TypeError, AttributeError)):
            self.analyzer.analyze_impact(None)

        # Test with invalid data types
        with pytest.raises((ValueError, TypeError, AttributeError)):
            self.analyzer.analyze_impact("invalid_string")

    @pytest.mark.unit
    def test_impact_analyzer_deterministic(self):
        """Test that impact analysis is deterministic"""
        change_data = {
            "files_affected": ["main.py", "utils.py"],
            "lines_changed": 50,
            "functions_modified": 3,
            "dependencies": ["requests", "numpy"],
        }

        # Run analysis multiple times
        result1 = self.analyzer.analyze_impact(change_data)
        result2 = self.analyzer.analyze_impact(change_data)

        # Results should be identical
        assert result1.risk_level == result2.risk_level
        assert abs(result1.impact_score - result2.impact_score) < 0.001
        assert result1.recommendations == result2.recommendations

    @pytest.mark.unit
    def test_impact_analyzer_edge_cases(self):
        """Test edge cases for impact analysis"""
        # Very large change
        large_change = {
            "files_affected": ["file" + str(i) + ".py" for i in range(1000)],
            "lines_changed": 100000,
            "functions_modified": 5000,
            "dependencies": ["dep" + str(i) for i in range(100)],
        }

        result = self.analyzer.analyze_impact(large_change)

        # Should handle large changes
        assert result.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        assert result.impact_score > 0.8

    @pytest.mark.unit
    def test_impact_analyzer_recommendations(self):
        """Test that recommendations are meaningful"""
        change_data = {
            "files_affected": ["critical_module.py"],
            "lines_changed": 100,
            "functions_modified": 5,
            "dependencies": ["external_lib"],
            "security_impact": True,
        }

        result = self.analyzer.analyze_impact(change_data)

        # Recommendations should be non-empty and meaningful
        assert len(result.recommendations) > 0
        assert isinstance(result.recommendations, str)
        assert len(result.recommendations.split()) > 3  # At least a few words

    @pytest.mark.unit
    def test_impact_analyzer_performance(self):
        """Test impact analysis performance"""
        import time

        change_data = {
            "files_affected": ["main.py", "utils.py", "helpers.py"],
            "lines_changed": 100,
            "functions_modified": 10,
            "dependencies": ["requests", "numpy", "pandas"],
        }

        start_time = time.time()
        result = self.analyzer.analyze_impact(change_data)
        end_time = time.time()

        # Should complete within reasonable time
        assert (end_time - start_time) < 1.0  # Less than 1 second
        assert result.analysis_time < 1.0


# ko dùng # type: ignore và ko dùng comment out để che giấu lỗi
