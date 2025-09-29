#!/usr/bin/env python3
"""
Business Analyzer - Senior Developer Business Thinking Module
Tư duy kinh doanh như dev chuyên nghiệp thật

Tính năng:
1. ROI Analysis - Phân tích lợi nhuận đầu tư
2. User Impact Assessment - Đánh giá tác động người dùng
3. Market Value Evaluation - Đánh giá giá trị thị trường
4. Priority Ranking - Xếp hạng ưu tiên
5. Cost-Benefit Analysis - Phân tích chi phí-lợi ích
6. Strategic Alignment - Căn chỉnh chiến lược
7. Risk-Reward Assessment - Đánh giá rủi ro-phần thưởng
"""

import re
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

class BusinessPriority(Enum):
    """Mức độ ưu tiên kinh doanh"""
    CRITICAL = "critical"      # Sống còn
    HIGH = "high"             # Quan trọng
    MEDIUM = "medium"         # Trung bình
    LOW = "low"               # Thấp
    NICE_TO_HAVE = "nice_to_have"  # Có thì tốt

class MarketImpact(Enum):
    """Tác động thị trường"""
    GAME_CHANGER = "game_changer"    # Thay đổi cuộc chơi
    COMPETITIVE_ADVANTAGE = "competitive_advantage"  # Lợi thế cạnh tranh
    MARKET_MAINTENANCE = "market_maintenance"        # Duy trì thị trường
    MINIMAL_IMPACT = "minimal_impact"                # Tác động tối thiểu

class UserSegment(Enum):
    """Phân khúc người dùng"""
    ENTERPRISE = "enterprise"        # Doanh nghiệp lớn
    SMB = "smb"                     # Doanh nghiệp vừa và nhỏ
    CONSUMER = "consumer"           # Người dùng cá nhân
    DEVELOPER = "developer"         # Nhà phát triển
    ADMIN = "admin"                 # Quản trị viên

@dataclass
class ROIAnalysis:
    """Phân tích ROI"""
    estimated_roi: float            # ROI ước tính (0-1)
    payback_period_months: int      # Thời gian hoàn vốn (tháng)
    net_present_value: float        # Giá trị hiện tại ròng
    internal_rate_of_return: float  # Tỷ suất hoàn vốn nội bộ
    break_even_point: int           # Điểm hòa vốn (tháng)
    confidence_level: float         # Mức độ tin cậy (0-1)

@dataclass
class UserImpactAssessment:
    """Đánh giá tác động người dùng"""
    affected_user_segments: List[UserSegment]
    user_satisfaction_impact: str   # "high", "medium", "low"
    user_retention_impact: str      # "increase", "maintain", "decrease"
    user_acquisition_impact: str    # "increase", "maintain", "decrease"
    support_ticket_reduction: float # Giảm ticket hỗ trợ (%)
    user_training_required: bool    # Cần training người dùng
    migration_complexity: str       # "simple", "moderate", "complex"

@dataclass
class MarketValueEvaluation:
    """Đánh giá giá trị thị trường"""
    market_impact: MarketImpact
    competitive_advantage_score: float  # 0-1
    market_share_potential: float       # 0-1
    customer_acquisition_cost: float    # Chi phí thu hút khách hàng
    customer_lifetime_value: float      # Giá trị khách hàng trọn đời
    time_to_market_advantage: int       # Lợi thế thời gian ra thị trường (tháng)
    market_timing_score: float          # 0-1

@dataclass
class CostBenefitAnalysis:
    """Phân tích chi phí-lợi ích"""
    development_cost: float         # Chi phí phát triển
    maintenance_cost: float         # Chi phí bảo trì (năm)
    operational_cost: float         # Chi phí vận hành (năm)
    infrastructure_cost: float      # Chi phí hạ tầng
    training_cost: float            # Chi phí đào tạo
    total_cost: float               # Tổng chi phí
    
    revenue_increase: float         # Tăng doanh thu
    cost_savings: float             # Tiết kiệm chi phí
    efficiency_gains: float         # Tăng hiệu quả
    risk_reduction_value: float     # Giá trị giảm rủi ro
    total_benefit: float            # Tổng lợi ích
    
    cost_benefit_ratio: float       # Tỷ lệ chi phí-lợi ích
    net_benefit: float              # Lợi ích ròng

@dataclass
class StrategicAlignment:
    """Căn chỉnh chiến lược"""
    business_objectives_alignment: float  # 0-1
    technical_strategy_alignment: float   # 0-1
    product_roadmap_alignment: float      # 0-1
    company_values_alignment: float       # 0-1
    overall_strategic_score: float        # 0-1
    strategic_risks: List[str]            # Rủi ro chiến lược

@dataclass
class RiskRewardAssessment:
    """Đánh giá rủi ro-phần thưởng"""
    technical_risk: float           # Rủi ro kỹ thuật (0-1)
    business_risk: float            # Rủi ro kinh doanh (0-1)
    market_risk: float              # Rủi ro thị trường (0-1)
    competitive_risk: float         # Rủi ro cạnh tranh (0-1)
    overall_risk_score: float       # Tổng rủi ro (0-1)
    
    potential_reward: float         # Phần thưởng tiềm năng (0-1)
    reward_probability: float       # Xác suất đạt phần thưởng (0-1)
    expected_reward: float          # Phần thưởng kỳ vọng (0-1)
    
    risk_reward_ratio: float        # Tỷ lệ rủi ro-phần thưởng
    recommendation: str             # "proceed", "proceed_with_caution", "reconsider", "reject"

@dataclass
class BusinessAnalysisResult:
    """Kết quả phân tích kinh doanh"""
    priority: BusinessPriority
    roi_analysis: ROIAnalysis
    user_impact: UserImpactAssessment
    market_value: MarketValueEvaluation
    cost_benefit: CostBenefitAnalysis
    strategic_alignment: StrategicAlignment
    risk_reward: RiskRewardAssessment
    
    business_score: float           # Điểm tổng thể (0-1)
    recommendation: str             # Khuyến nghị cuối cùng
    key_insights: List[str]         # Những hiểu biết chính
    success_factors: List[str]      # Yếu tố thành công
    failure_risks: List[str]        # Rủi ro thất bại
    analysis_time: float            # Thời gian phân tích

class BusinessAnalyzer:
    """Senior Developer Business Analyzer"""
    
    def __init__(self):
        self.business_keywords = self._load_business_keywords()
        self.user_segment_patterns = self._load_user_segment_patterns()
        self.market_patterns = self._load_market_patterns()
        self.cost_patterns = self._load_cost_patterns()
        
    def _load_business_keywords(self) -> Dict[str, Dict]:
        """Load business analysis keywords"""
        return {
            'high_value': {
                'keywords': ['revenue', 'profit', 'sales', 'monetization', 'subscription', 'premium', 'enterprise'],
                'weight': 3.0
            },
            'user_experience': {
                'keywords': ['user experience', 'ux', 'ui', 'interface', 'usability', 'satisfaction', 'retention'],
                'weight': 2.5
            },
            'performance': {
                'keywords': ['performance', 'speed', 'optimization', 'efficiency', 'scalability', 'reliability'],
                'weight': 2.0
            },
            'security': {
                'keywords': ['security', 'privacy', 'compliance', 'gdpr', 'sox', 'hipaa', 'authentication', 'encryption'],
                'weight': 3.5  # Bảo mật là vấn đề sống còn
            },
            'competitive': {
                'keywords': ['competitive', 'advantage', 'differentiation', 'market share', 'leadership'],
                'weight': 2.8
            },
            'operational': {
                'keywords': ['operational', 'maintenance', 'support', 'cost reduction', 'automation'],
                'weight': 2.2
            },
            'strategic': {
                'keywords': ['strategic', 'roadmap', 'vision', 'mission', 'goals', 'objectives'],
                'weight': 2.5
            }
        }
    
    def _load_user_segment_patterns(self) -> Dict[UserSegment, List[str]]:
        """Load user segment patterns"""
        return {
            UserSegment.ENTERPRISE: ['enterprise', 'corporate', 'business', 'company', 'organization'],
            UserSegment.SMB: ['smb', 'small business', 'medium business', 'startup'],
            UserSegment.CONSUMER: ['consumer', 'user', 'customer', 'individual', 'personal'],
            UserSegment.DEVELOPER: ['developer', 'dev', 'programmer', 'engineer', 'api', 'sdk'],
            UserSegment.ADMIN: ['admin', 'administrator', 'management', 'ops', 'operations']
        }
    
    def _load_market_patterns(self) -> Dict[str, Dict]:
        """Load market analysis patterns"""
        return {
            'game_changer': {
                'keywords': ['revolutionary', 'breakthrough', 'disruptive', 'innovative', 'game changer'],
                'impact': MarketImpact.GAME_CHANGER
            },
            'competitive_advantage': {
                'keywords': ['advantage', 'competitive', 'differentiation', 'unique', 'superior'],
                'impact': MarketImpact.COMPETITIVE_ADVANTAGE
            },
            'market_maintenance': {
                'keywords': ['maintenance', 'improvement', 'enhancement', 'update', 'upgrade'],
                'impact': MarketImpact.MARKET_MAINTENANCE
            },
            'minimal_impact': {
                'keywords': ['minor', 'small', 'incremental', 'cosmetic', 'nice to have'],
                'impact': MarketImpact.MINIMAL_IMPACT
            }
        }
    
    def _load_cost_patterns(self) -> Dict[str, float]:
        """Load cost estimation patterns"""
        return {
            'simple': 1000,      # Task đơn giản
            'moderate': 5000,    # Task trung bình
            'complex': 15000,    # Task phức tạp
            'enterprise': 50000, # Task enterprise
            'security': 25000,   # Task bảo mật (cao hơn vì quan trọng)
            'performance': 10000, # Task performance
            'new_feature': 20000, # Feature mới
            'integration': 30000  # Tích hợp hệ thống
        }
    
    def analyze_roi(self, task: str) -> ROIAnalysis:
        """Phân tích ROI"""
        task_lower = task.lower()
        
        # Tính điểm dựa trên keywords
        total_score = 0
        for category, info in self.business_keywords.items():
            for keyword in info['keywords']:
                if keyword in task_lower:
                    total_score += info['weight']
        
        # Normalize score to 0-1
        max_possible_score = sum(info['weight'] for info in self.business_keywords.values())
        roi_score = min(1.0, total_score / max_possible_score)
        
        # Estimate costs and benefits
        base_cost = self._estimate_base_cost(task)
        security_multiplier = 1.5 if 'security' in task_lower else 1.0
        complexity_multiplier = 1.2 if 'complex' in task_lower else 1.0
        
        development_cost = base_cost * security_multiplier * complexity_multiplier
        maintenance_cost = development_cost * 0.2  # 20% of dev cost per year
        
        # Estimate benefits
        if roi_score > 0.7:
            revenue_increase = development_cost * 3  # 3x return for high-value features
            payback_period = 6  # 6 months
        elif roi_score > 0.4:
            revenue_increase = development_cost * 2  # 2x return for medium-value features
            payback_period = 12  # 12 months
        else:
            revenue_increase = development_cost * 1.2  # 1.2x return for low-value features
            payback_period = 24  # 24 months
        
        # Calculate financial metrics
        net_present_value = revenue_increase - development_cost
        internal_rate_of_return = (revenue_increase / development_cost) ** (12 / payback_period) - 1
        break_even_point = int(development_cost / (revenue_increase / 12))
        
        # Confidence level based on task clarity
        confidence_level = 0.8 if len(task.split()) > 5 else 0.6
        
        return ROIAnalysis(
            estimated_roi=roi_score,
            payback_period_months=payback_period,
            net_present_value=net_present_value,
            internal_rate_of_return=internal_rate_of_return,
            break_even_point=break_even_point,
            confidence_level=confidence_level
        )
    
    def _estimate_base_cost(self, task: str) -> float:
        """Ước tính chi phí cơ bản"""
        task_lower = task.lower()
        
        # Find matching cost pattern
        for pattern, cost in self.cost_patterns.items():
            if pattern in task_lower:
                return cost
        
        # Default cost based on task length and complexity
        word_count = len(task.split())
        if word_count < 5:
            return self.cost_patterns['simple']
        elif word_count < 10:
            return self.cost_patterns['moderate']
        else:
            return self.cost_patterns['complex']
    
    def assess_user_impact(self, task: str) -> UserImpactAssessment:
        """Đánh giá tác động người dùng"""
        task_lower = task.lower()
        
        # Identify affected user segments
        affected_segments = []
        for segment, patterns in self.user_segment_patterns.items():
            for pattern in patterns:
                if pattern in task_lower:
                    affected_segments.append(segment)
        
        # Default to consumer if no specific segment identified
        if not affected_segments:
            affected_segments = [UserSegment.CONSUMER]
        
        # Assess impact levels
        if any(keyword in task_lower for keyword in ['new', 'feature', 'improve', 'enhance']):
            satisfaction_impact = "high"
            retention_impact = "increase"
            acquisition_impact = "increase"
        elif any(keyword in task_lower for keyword in ['fix', 'bug', 'error', 'issue']):
            satisfaction_impact = "medium"
            retention_impact = "maintain"
            acquisition_impact = "maintain"
        else:
            satisfaction_impact = "low"
            retention_impact = "maintain"
            acquisition_impact = "maintain"
        
        # Estimate support ticket reduction
        if 'automation' in task_lower or 'self-service' in task_lower:
            support_reduction = 0.3  # 30% reduction
        elif 'improve' in task_lower or 'optimize' in task_lower:
            support_reduction = 0.15  # 15% reduction
        else:
            support_reduction = 0.05  # 5% reduction
        
        # Assess migration complexity
        if any(keyword in task_lower for keyword in ['breaking', 'deprecate', 'remove', 'change']):
            migration_complexity = "complex"
            training_required = True
        elif any(keyword in task_lower for keyword in ['new', 'add', 'feature']):
            migration_complexity = "moderate"
            training_required = True
        else:
            migration_complexity = "simple"
            training_required = False
        
        return UserImpactAssessment(
            affected_user_segments=affected_segments,
            user_satisfaction_impact=satisfaction_impact,
            user_retention_impact=retention_impact,
            user_acquisition_impact=acquisition_impact,
            support_ticket_reduction=support_reduction,
            user_training_required=training_required,
            migration_complexity=migration_complexity
        )
    
    def evaluate_market_value(self, task: str) -> MarketValueEvaluation:
        """Đánh giá giá trị thị trường"""
        task_lower = task.lower()
        
        # Determine market impact
        market_impact = MarketImpact.MINIMAL_IMPACT
        for category, info in self.market_patterns.items():
            for keyword in info['keywords']:
                if keyword in task_lower:
                    market_impact = info['impact']
                    break
        
        # Calculate competitive advantage score
        competitive_keywords = ['competitive', 'advantage', 'unique', 'superior', 'better', 'faster']
        competitive_score = sum(1 for keyword in competitive_keywords if keyword in task_lower) / len(competitive_keywords)
        
        # Estimate market share potential
        if market_impact == MarketImpact.GAME_CHANGER:
            market_share_potential = 0.8
        elif market_impact == MarketImpact.COMPETITIVE_ADVANTAGE:
            market_share_potential = 0.6
        elif market_impact == MarketImpact.MARKET_MAINTENANCE:
            market_share_potential = 0.3
        else:
            market_share_potential = 0.1
        
        # Estimate costs and values
        base_cost = self._estimate_base_cost(task)
        customer_acquisition_cost = base_cost * 0.1  # 10% of dev cost
        customer_lifetime_value = base_cost * 2.0    # 2x dev cost
        
        # Time to market advantage
        if 'security' in task_lower:
            time_advantage = 12  # Security features have high time advantage
        elif 'performance' in task_lower:
            time_advantage = 6   # Performance features have medium time advantage
        else:
            time_advantage = 3   # Other features have low time advantage
        
        # Market timing score
        market_timing_score = min(1.0, time_advantage / 12)
        
        return MarketValueEvaluation(
            market_impact=market_impact,
            competitive_advantage_score=competitive_score,
            market_share_potential=market_share_potential,
            customer_acquisition_cost=customer_acquisition_cost,
            customer_lifetime_value=customer_lifetime_value,
            time_to_market_advantage=time_advantage,
            market_timing_score=market_timing_score
        )
    
    def analyze_cost_benefit(self, task: str) -> CostBenefitAnalysis:
        """Phân tích chi phí-lợi ích"""
        base_cost = self._estimate_base_cost(task)
        task_lower = task.lower()
        
        # Calculate costs
        development_cost = base_cost
        maintenance_cost = base_cost * 0.2  # 20% per year
        operational_cost = base_cost * 0.1  # 10% per year
        infrastructure_cost = base_cost * 0.05  # 5% per year
        training_cost = base_cost * 0.1 if 'training' in task_lower else base_cost * 0.05
        
        total_cost = development_cost + maintenance_cost + operational_cost + infrastructure_cost + training_cost
        
        # Calculate benefits
        if 'security' in task_lower:
            # Security features have high value
            revenue_increase = base_cost * 4
            cost_savings = base_cost * 2
            efficiency_gains = base_cost * 1.5
            risk_reduction_value = base_cost * 3
        elif 'performance' in task_lower:
            # Performance features have medium-high value
            revenue_increase = base_cost * 2.5
            cost_savings = base_cost * 1.5
            efficiency_gains = base_cost * 2
            risk_reduction_value = base_cost * 1
        elif 'new' in task_lower and 'feature' in task_lower:
            # New features have medium value
            revenue_increase = base_cost * 2
            cost_savings = base_cost * 1
            efficiency_gains = base_cost * 1.5
            risk_reduction_value = base_cost * 0.5
        else:
            # Other tasks have lower value
            revenue_increase = base_cost * 1.2
            cost_savings = base_cost * 0.5
            efficiency_gains = base_cost * 1
            risk_reduction_value = base_cost * 0.2
        
        total_benefit = revenue_increase + cost_savings + efficiency_gains + risk_reduction_value
        
        # Calculate ratios
        cost_benefit_ratio = total_benefit / total_cost if total_cost > 0 else 0
        net_benefit = total_benefit - total_cost
        
        return CostBenefitAnalysis(
            development_cost=development_cost,
            maintenance_cost=maintenance_cost,
            operational_cost=operational_cost,
            infrastructure_cost=infrastructure_cost,
            training_cost=training_cost,
            total_cost=total_cost,
            revenue_increase=revenue_increase,
            cost_savings=cost_savings,
            efficiency_gains=efficiency_gains,
            risk_reduction_value=risk_reduction_value,
            total_benefit=total_benefit,
            cost_benefit_ratio=cost_benefit_ratio,
            net_benefit=net_benefit
        )
    
    def assess_strategic_alignment(self, task: str) -> StrategicAlignment:
        """Đánh giá căn chỉnh chiến lược"""
        task_lower = task.lower()
        
        # Business objectives alignment
        business_keywords = ['revenue', 'profit', 'growth', 'customer', 'market', 'competitive']
        business_score = sum(1 for keyword in business_keywords if keyword in task_lower) / len(business_keywords)
        
        # Technical strategy alignment
        tech_keywords = ['performance', 'scalability', 'reliability', 'security', 'maintainability']
        tech_score = sum(1 for keyword in tech_keywords if keyword in task_lower) / len(tech_keywords)
        
        # Product roadmap alignment
        product_keywords = ['feature', 'enhancement', 'improvement', 'user experience', 'functionality']
        product_score = sum(1 for keyword in product_keywords if keyword in task_lower) / len(product_keywords)
        
        # Company values alignment (assuming security, quality, innovation are core values)
        values_keywords = ['security', 'quality', 'innovation', 'excellence', 'integrity']
        values_score = sum(1 for keyword in values_keywords if keyword in task_lower) / len(values_keywords)
        
        overall_strategic_score = (business_score + tech_score + product_score + values_score) / 4
        
        # Identify strategic risks
        strategic_risks = []
        if business_score < 0.3:
            strategic_risks.append("Low business objective alignment")
        if tech_score < 0.3:
            strategic_risks.append("Low technical strategy alignment")
        if product_score < 0.3:
            strategic_risks.append("Low product roadmap alignment")
        if values_score < 0.3:
            strategic_risks.append("Low company values alignment")
        
        return StrategicAlignment(
            business_objectives_alignment=business_score,
            technical_strategy_alignment=tech_score,
            product_roadmap_alignment=product_score,
            company_values_alignment=values_score,
            overall_strategic_score=overall_strategic_score,
            strategic_risks=strategic_risks
        )
    
    def assess_risk_reward(self, task: str) -> RiskRewardAssessment:
        """Đánh giá rủi ro-phần thưởng"""
        task_lower = task.lower()
        
        # Assess risks
        technical_risk = 0.3  # Base technical risk
        if 'complex' in task_lower or 'integration' in task_lower:
            technical_risk += 0.3
        if 'new' in task_lower and 'technology' in task_lower:
            technical_risk += 0.2
        if 'security' in task_lower:
            technical_risk += 0.1  # Security adds some technical complexity
        
        business_risk = 0.2  # Base business risk
        if 'breaking' in task_lower or 'deprecate' in task_lower:
            business_risk += 0.4
        if 'new' in task_lower and 'feature' in task_lower:
            business_risk += 0.2
        
        market_risk = 0.2  # Base market risk
        if 'competitive' in task_lower:
            market_risk += 0.2
        if 'timing' in task_lower:
            market_risk += 0.1
        
        competitive_risk = 0.1  # Base competitive risk
        if 'advantage' in task_lower:
            competitive_risk += 0.2
        
        overall_risk_score = (technical_risk + business_risk + market_risk + competitive_risk) / 4
        
        # Assess potential reward
        potential_reward = 0.5  # Base reward
        if 'security' in task_lower:
            potential_reward += 0.3  # Security has high reward
        if 'performance' in task_lower:
            potential_reward += 0.2  # Performance has medium-high reward
        if 'new' in task_lower and 'feature' in task_lower:
            potential_reward += 0.2  # New features have medium reward
        if 'revenue' in task_lower or 'profit' in task_lower:
            potential_reward += 0.3  # Revenue features have high reward
        
        # Reward probability based on task clarity and complexity
        reward_probability = 0.8  # Base probability
        if len(task.split()) < 5:
            reward_probability -= 0.2  # Unclear tasks have lower probability
        if 'complex' in task_lower:
            reward_probability -= 0.1  # Complex tasks have lower probability
        if 'security' in task_lower:
            reward_probability += 0.1  # Security tasks have higher probability of success
        
        expected_reward = potential_reward * reward_probability
        
        # Calculate risk-reward ratio
        risk_reward_ratio = overall_risk_score / expected_reward if expected_reward > 0 else float('inf')
        
        # Generate recommendation
        if risk_reward_ratio < 0.5 and expected_reward > 0.7:
            recommendation = "proceed"
        elif risk_reward_ratio < 1.0 and expected_reward > 0.5:
            recommendation = "proceed_with_caution"
        elif risk_reward_ratio < 2.0 and expected_reward > 0.3:
            recommendation = "reconsider"
        else:
            recommendation = "reject"
        
        return RiskRewardAssessment(
            technical_risk=technical_risk,
            business_risk=business_risk,
            market_risk=market_risk,
            competitive_risk=competitive_risk,
            overall_risk_score=overall_risk_score,
            potential_reward=potential_reward,
            reward_probability=reward_probability,
            expected_reward=expected_reward,
            risk_reward_ratio=risk_reward_ratio,
            recommendation=recommendation
        )
    
    def analyze_business_value(self, task: str) -> BusinessAnalysisResult:
        """Phân tích giá trị kinh doanh toàn diện"""
        start_time = time.time()
        
        # Run all analyses
        roi_analysis = self.analyze_roi(task)
        user_impact = self.assess_user_impact(task)
        market_value = self.evaluate_market_value(task)
        cost_benefit = self.analyze_cost_benefit(task)
        strategic_alignment = self.assess_strategic_alignment(task)
        risk_reward = self.assess_risk_reward(task)
        
        # Determine priority
        if risk_reward.recommendation == "proceed" and roi_analysis.estimated_roi > 0.7:
            priority = BusinessPriority.CRITICAL
        elif risk_reward.recommendation in ["proceed", "proceed_with_caution"] and roi_analysis.estimated_roi > 0.5:
            priority = BusinessPriority.HIGH
        elif risk_reward.recommendation in ["proceed_with_caution", "reconsider"] and roi_analysis.estimated_roi > 0.3:
            priority = BusinessPriority.MEDIUM
        elif risk_reward.recommendation == "reconsider" and roi_analysis.estimated_roi > 0.1:
            priority = BusinessPriority.LOW
        else:
            priority = BusinessPriority.NICE_TO_HAVE
        
        # Calculate overall business score
        business_score = (
            roi_analysis.estimated_roi * 0.25 +
            (1 - risk_reward.overall_risk_score) * 0.25 +
            strategic_alignment.overall_strategic_score * 0.25 +
            risk_reward.expected_reward * 0.25
        )
        
        # Generate recommendation
        if priority == BusinessPriority.CRITICAL:
            recommendation = "IMMEDIATE ACTION REQUIRED - Critical business priority"
        elif priority == BusinessPriority.HIGH:
            recommendation = "HIGH PRIORITY - Should be implemented soon"
        elif priority == BusinessPriority.MEDIUM:
            recommendation = "MEDIUM PRIORITY - Plan for next sprint"
        elif priority == BusinessPriority.LOW:
            recommendation = "LOW PRIORITY - Consider for future releases"
        else:
            recommendation = "NICE TO HAVE - Low business value"
        
        # Generate key insights
        key_insights = []
        if roi_analysis.estimated_roi > 0.7:
            key_insights.append("High ROI potential - strong business case")
        if 'security' in task.lower():
            key_insights.append("Security-focused - critical for business continuity")
        if market_value.market_impact == MarketImpact.GAME_CHANGER:
            key_insights.append("Game-changing potential - could transform market position")
        if cost_benefit.cost_benefit_ratio > 2.0:
            key_insights.append("Excellent cost-benefit ratio - high value investment")
        
        # Generate success factors
        success_factors = []
        if strategic_alignment.overall_strategic_score > 0.7:
            success_factors.append("Strong strategic alignment")
        if risk_reward.reward_probability > 0.8:
            success_factors.append("High probability of success")
        if user_impact.user_satisfaction_impact == "high":
            success_factors.append("High user satisfaction potential")
        
        # Generate failure risks
        failure_risks = []
        if risk_reward.overall_risk_score > 0.7:
            failure_risks.append("High overall risk")
        if strategic_alignment.strategic_risks:
            failure_risks.extend(strategic_alignment.strategic_risks)
        if user_impact.migration_complexity == "complex":
            failure_risks.append("Complex user migration required")
        
        analysis_time = time.time() - start_time
        
        return BusinessAnalysisResult(
            priority=priority,
            roi_analysis=roi_analysis,
            user_impact=user_impact,
            market_value=market_value,
            cost_benefit=cost_benefit,
            strategic_alignment=strategic_alignment,
            risk_reward=risk_reward,
            business_score=business_score,
            recommendation=recommendation,
            key_insights=key_insights,
            success_factors=success_factors,
            failure_risks=failure_risks,
            analysis_time=analysis_time
        )

# Test function
if __name__ == "__main__":
    analyzer = BusinessAnalyzer()
    result = analyzer.analyze_business_value("Implement new security authentication system for enterprise customers")
    
    print("=== BUSINESS ANALYSIS RESULT ===")
    print(f"Priority: {result.priority.value}")
    print(f"Business Score: {result.business_score:.2f}")
    print(f"ROI: {result.roi_analysis.estimated_roi:.2f}")
    print(f"Risk Score: {result.risk_reward.overall_risk_score:.2f}")
    print(f"Recommendation: {result.recommendation}")
    print(f"Key Insights: {len(result.key_insights)}")
    print(f"Analysis Time: {result.analysis_time:.3f}s")
