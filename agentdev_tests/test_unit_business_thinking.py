#!/usr/bin/env python3
"""
Unit tests for Business Thinking Module
Tests ROI analysis and business priority assessment
"""

import pytest
from hypothesis import given
from hypothesis import strategies as st

# Import AgentDev modules
from agent_dev.core.business_thinking import (
    BusinessPriority,
    BusinessThinking,
    ROIAnalysis,
)


class TestBusinessThinking:
    """Test cases for Business Thinking Module"""

    def setup_method(self):
        """Set up test fixtures"""
        self.business_thinking = BusinessThinking()

    @pytest.mark.unit
    def test_business_thinking_initialization(self):
        """Test BusinessThinking initialization"""
        assert self.business_thinking is not None
        assert hasattr(self.business_thinking, "analyze_business_impact")
        assert hasattr(self.business_thinking, "calculate_roi")
        assert hasattr(self.business_thinking, "assess_priority")

    @pytest.mark.unit
    def test_roi_calculation_basic(self):
        """Test basic ROI calculation"""
        # Test data
        project_data = {
            "development_cost": 100000,
            "maintenance_cost": 20000,
            "expected_revenue": 200000,
            "time_to_market": 6,  # months
            "market_size": 1000000,
            "competitive_advantage": 0.8,
        }

        roi_result = self.business_thinking.calculate_roi(project_data)

        assert isinstance(roi_result, ROIAnalysis)
        assert 0.0 <= roi_result.roi_score <= 1.0
        assert roi_result.net_present_value > 0
        assert roi_result.payback_period > 0
        assert roi_result.risk_level in ["low", "medium", "high", "critical"]

    @pytest.mark.unit
    @given(
        cost=st.integers(min_value=1000, max_value=1000000),
        revenue=st.integers(min_value=1000, max_value=2000000),
        time_to_market=st.integers(min_value=1, max_value=24),
    )
    def test_roi_calculation_idempotence(
        self, cost, revenue, time_to_market, market_size=1000000
    ):
        """Property test: ROI calculation should be idempotent"""
        project_data = {
            "development_cost": cost,
            "maintenance_cost": cost * 0.2,
            "expected_revenue": revenue,
            "time_to_market": time_to_market,
            "market_size": market_size,
            "competitive_advantage": 0.7,
        }

        # Calculate ROI twice with same input
        roi1 = self.business_thinking.calculate_roi(project_data)
        roi2 = self.business_thinking.calculate_roi(project_data)

        # Results should be identical
        assert abs(roi1.roi_score - roi2.roi_score) < 0.001
        assert abs(roi1.net_present_value - roi2.net_present_value) < 0.001
        assert roi1.risk_level == roi2.risk_level

    @pytest.mark.unit
    def test_roi_calculation_high_value_project(self):
        """Test ROI calculation for high-value project"""
        high_value_project = {
            "development_cost": 50000,
            "maintenance_cost": 5000,
            "expected_revenue": 500000,
            "time_to_market": 3,
            "market_size": 2000000,
            "competitive_advantage": 0.9,
        }

        roi_result = self.business_thinking.calculate_roi(high_value_project)

        # Should have high ROI
        assert roi_result.roi_score > 0.7
        assert roi_result.net_present_value > 400000
        assert roi_result.payback_period < 6  # months

    @pytest.mark.unit
    def test_roi_calculation_low_value_project(self):
        """Test ROI calculation for low-value project"""
        low_value_project = {
            "development_cost": 200000,
            "maintenance_cost": 50000,
            "expected_revenue": 100000,
            "time_to_market": 12,
            "market_size": 100000,
            "competitive_advantage": 0.3,
        }

        roi_result = self.business_thinking.calculate_roi(low_value_project)

        # Should have low ROI
        assert roi_result.roi_score < 0.3
        assert roi_result.net_present_value < 0
        assert roi_result.payback_period > 24  # months

    @pytest.mark.unit
    def test_priority_assessment(self):
        """Test business priority assessment"""
        # High priority project
        high_priority_data = {
            "strategic_alignment": 0.9,
            "customer_demand": 0.8,
            "competitive_pressure": 0.7,
            "regulatory_requirement": True,
            "revenue_impact": 0.9,
        }

        priority_result = self.business_thinking.assess_priority(high_priority_data)

        assert isinstance(priority_result, BusinessPriority)
        assert priority_result.priority_level in ["low", "medium", "high", "critical"]
        assert priority_result.priority_score >= 0.0
        assert priority_result.priority_score <= 1.0
        assert len(priority_result.recommendations) > 0

    @pytest.mark.unit
    def test_priority_assessment_critical_project(self):
        """Test priority assessment for critical project"""
        critical_project = {
            "strategic_alignment": 1.0,
            "customer_demand": 1.0,
            "competitive_pressure": 1.0,
            "regulatory_requirement": True,
            "revenue_impact": 1.0,
            "security_critical": True,
        }

        priority_result = self.business_thinking.assess_priority(critical_project)

        # Should be critical priority
        assert priority_result.priority_level == "critical"
        assert priority_result.priority_score > 0.9

    @pytest.mark.unit
    def test_business_impact_analysis(self):
        """Test comprehensive business impact analysis"""
        business_data = {
            "project_name": "AI Enhancement",
            "development_cost": 150000,
            "maintenance_cost": 30000,
            "expected_revenue": 300000,
            "time_to_market": 6,
            "market_size": 1500000,
            "competitive_advantage": 0.8,
            "strategic_alignment": 0.9,
            "customer_demand": 0.8,
            "regulatory_requirement": False,
        }

        analysis_result = self.business_thinking.analyze_business_impact(business_data)

        # Should return comprehensive analysis
        assert "roi_analysis" in analysis_result
        assert "priority_assessment" in analysis_result
        assert "recommendations" in analysis_result
        assert "risk_assessment" in analysis_result

        # ROI analysis should be present
        roi = analysis_result["roi_analysis"]
        assert isinstance(roi, ROIAnalysis)
        assert roi.roi_score > 0

        # Priority assessment should be present
        priority = analysis_result["priority_assessment"]
        assert isinstance(priority, BusinessPriority)
        assert priority.priority_score > 0

    @pytest.mark.unit
    def test_market_analysis(self):
        """Test market analysis capabilities"""
        market_data = {
            "market_size": 2000000,
            "growth_rate": 0.15,
            "competition_level": 0.7,
            "barriers_to_entry": 0.6,
            "customer_segments": ["enterprise", "smb", "consumer"],
        }

        market_result = self.business_thinking.analyze_market_opportunity(market_data)

        assert "market_attractiveness" in market_result
        assert "competitive_position" in market_result
        assert "growth_potential" in market_result
        assert "recommendations" in market_result

        # Market attractiveness should be calculated
        assert 0.0 <= market_result["market_attractiveness"] <= 1.0
        assert 0.0 <= market_result["competitive_position"] <= 1.0
        assert 0.0 <= market_result["growth_potential"] <= 1.0

    @pytest.mark.unit
    def test_risk_reward_analysis(self):
        """Test risk-reward analysis"""
        project_data = {
            "expected_return": 500000,
            "risk_level": 0.7,
            "probability_of_success": 0.6,
            "worst_case_scenario": -100000,
            "best_case_scenario": 1000000,
        }

        risk_reward_result = self.business_thinking.analyze_risk_reward(project_data)

        assert "risk_score" in risk_reward_result
        assert "reward_score" in risk_reward_result
        assert "risk_reward_ratio" in risk_reward_result
        assert "recommendation" in risk_reward_result

        # Risk and reward scores should be valid
        assert 0.0 <= risk_reward_result["risk_score"] <= 1.0
        assert 0.0 <= risk_reward_result["reward_score"] <= 1.0
        assert risk_reward_result["risk_reward_ratio"] > 0

    @pytest.mark.unit
    def test_empty_input_handling(self):
        """Test handling of empty or invalid inputs"""
        # Test with empty data
        empty_data = {}

        with pytest.raises((ValueError, KeyError)):
            self.business_thinking.calculate_roi(empty_data)

        # Test with None
        with pytest.raises((ValueError, TypeError)):
            self.business_thinking.calculate_roi(None)

    @pytest.mark.unit
    def test_business_thinking_deterministic(self):
        """Test that business thinking is deterministic"""
        project_data = {
            "development_cost": 100000,
            "maintenance_cost": 20000,
            "expected_revenue": 200000,
            "time_to_market": 6,
            "market_size": 1000000,
            "competitive_advantage": 0.8,
        }

        # Run analysis multiple times
        result1 = self.business_thinking.calculate_roi(project_data)
        result2 = self.business_thinking.calculate_roi(project_data)

        # Results should be identical
        assert abs(result1.roi_score - result2.roi_score) < 0.001
        assert abs(result1.net_present_value - result2.net_present_value) < 0.001
        assert result1.risk_level == result2.risk_level

    @pytest.mark.unit
    def test_business_thinking_performance(self):
        """Test business thinking performance"""
        import time

        project_data = {
            "development_cost": 100000,
            "maintenance_cost": 20000,
            "expected_revenue": 200000,
            "time_to_market": 6,
            "market_size": 1000000,
            "competitive_advantage": 0.8,
        }

        start_time = time.time()
        result = self.business_thinking.calculate_roi(project_data)
        end_time = time.time()

        # Should complete within reasonable time
        assert (end_time - start_time) < 0.5  # Less than 0.5 seconds


# ko dùng # type: ignore và ko dùng comment out để che giấu lỗi
