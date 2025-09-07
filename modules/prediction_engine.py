#!/usr/bin/env python3
"""
Prediction Engine Module - StillMe AI Framework
===============================================

Module dự đoán xu hướng thị trường dựa trên dữ liệu từ Market Intelligence.
Chuyển đổi dữ liệu thô thành dự báo và khuyến nghị kinh doanh.

Author: StillMe Framework Team
Version: 1.0.0
"""

import logging
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TrendDirection(Enum):
    """Xu hướng phát triển"""
    RISING = "rising"
    STABLE = "stable"
    DECLINING = "declining"
    UNKNOWN = "unknown"

class PredictionConfidence(Enum):
    """Độ tin cậy dự báo"""
    HIGH = "high"      # > 80%
    MEDIUM = "medium"  # 60-80%
    LOW = "low"        # < 60%

@dataclass
class PredictionSignal:
    """Tín hiệu dự báo từ một nguồn dữ liệu"""
    source: str
    signal_type: str
    strength: float  # 0-100
    direction: TrendDirection
    confidence: float  # 0-1
    metadata: Dict[str, Any]

@dataclass
class TrendPrediction:
    """Dự báo xu hướng cho một technology/tool"""
    name: str
    category: str
    potential_score: float  # 0-100
    confidence_score: float  # 0-1
    direction: TrendDirection
    time_horizon: str  # "short" (1-3 months), "medium" (3-6 months), "long" (6+ months)
    signals: List[PredictionSignal]
    reasoning: str
    metadata: Dict[str, Any]

@dataclass
class BusinessRecommendation:
    """Khuyến nghị kinh doanh dựa trên dự báo"""
    recommendation_type: str  # "adoption", "investment", "development", "monitoring"
    priority: str  # "high", "medium", "low"
    description: str
    expected_impact: str
    timeline: str
    confidence: float
    supporting_data: List[str]

class PredictionEngine:
    """
    Prediction Engine - Dự đoán xu hướng thị trường
    
    Sử dụng dữ liệu từ Market Intelligence để:
    1. Phân tích velocity và momentum
    2. Tính toán potential score
    3. Đưa ra dự báo với confidence level
    4. Tạo khuyến nghị kinh doanh
    """
    
    def __init__(self):
        """Initialize Prediction Engine"""
        self.logger = logging.getLogger(__name__)
        
        # Weights cho các nguồn dữ liệu
        self.source_weights = {
            'GitHub': 0.25,      # Code adoption
            'Google Trends': 0.20,  # Search interest
            'Reddit': 0.20,      # Community sentiment
            'Stack Overflow': 0.20,  # Developer adoption
            'Tech News': 0.15    # Media attention
        }
        
        # Thresholds cho scoring
        self.thresholds = {
            'high_potential': 70,
            'medium_potential': 50,
            'high_confidence': 0.8,
            'medium_confidence': 0.6
        }
        
        self.logger.info("✅ PredictionEngine initialized")
    
    def analyze_trends(self, market_data: List[Dict[str, Any]]) -> List[TrendPrediction]:
        """
        Phân tích dữ liệu thị trường và tạo dự báo
        
        Args:
            market_data: Dữ liệu từ market_intel.consolidate_trends()
            
        Returns:
            List[TrendPrediction]: Danh sách dự báo xu hướng
        """
        self.logger.info("🔍 Starting trend analysis and prediction")
        
        # Group trends by technology/tool
        grouped_trends = self._group_trends_by_technology(market_data)
        
        predictions = []
        for tech_name, trends in grouped_trends.items():
            try:
                prediction = self._analyze_technology_trends(tech_name, trends)
                if prediction:
                    predictions.append(prediction)
            except Exception as e:
                self.logger.warning(f"⚠️ Error analyzing {tech_name}: {e}")
                continue
        
        # Sort by potential score
        predictions.sort(key=lambda x: x.potential_score, reverse=True)
        
        self.logger.info(f"✅ Generated {len(predictions)} trend predictions")
        return predictions
    
    def _group_trends_by_technology(self, market_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group trends by technology/tool name"""
        grouped = {}
        
        for trend in market_data:
            # Extract technology name from title
            tech_name = self._extract_technology_name(trend.get('title', ''))
            if tech_name:
                if tech_name not in grouped:
                    grouped[tech_name] = []
                grouped[tech_name].append(trend)
        
        return grouped
    
    def _extract_technology_name(self, title: str) -> Optional[str]:
        """Extract technology name from trend title"""
        # Simple keyword extraction
        tech_keywords = [
            'Python', 'JavaScript', 'React', 'Vue', 'Angular', 'Node.js',
            'Django', 'Flask', 'FastAPI', 'Express', 'Spring',
            'TensorFlow', 'PyTorch', 'Keras', 'Scikit-learn',
            'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP',
            'MongoDB', 'PostgreSQL', 'MySQL', 'Redis',
            'TypeScript', 'Rust', 'Go', 'Java', 'C++', 'C#',
            'AI', 'Machine Learning', 'Deep Learning', 'NLP',
            'Blockchain', 'Web3', 'NFT', 'DeFi'
        ]
        
        title_lower = title.lower()
        for keyword in tech_keywords:
            if keyword.lower() in title_lower:
                return keyword
        
        # If no specific tech found, try to extract from common patterns
        if 'github' in title_lower or 'repository' in title_lower:
            # Extract from GitHub repo names
            words = title.split()
            for word in words:
                if len(word) > 3 and word.isalpha():
                    return word.title()
        
        # Default fallback
        return "General Technology"
    
    def _analyze_technology_trends(self, tech_name: str, trends: List[Dict[str, Any]]) -> Optional[TrendPrediction]:
        """Analyze trends for a specific technology"""
        if not trends:
            return None
        
        signals = []
        total_potential = 0
        total_confidence = 0
        signal_count = 0
        
        for trend in trends:
            signal = self._create_prediction_signal(trend)
            if signal:
                signals.append(signal)
                total_potential += signal.strength
                total_confidence += signal.confidence
                signal_count += 1
        
        if signal_count == 0:
            return None
        
        # Calculate average scores
        avg_potential = total_potential / signal_count
        avg_confidence = total_confidence / signal_count
        
        # Determine direction based on signals
        direction = self._determine_trend_direction(signals)
        
        # Determine time horizon
        time_horizon = self._determine_time_horizon(signals)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(tech_name, signals, avg_potential, direction)
        
        return TrendPrediction(
            name=tech_name,
            category=self._categorize_technology(tech_name),
            potential_score=avg_potential,
            confidence_score=avg_confidence,
            direction=direction,
            time_horizon=time_horizon,
            signals=signals,
            reasoning=reasoning,
            metadata={
                'signal_count': signal_count,
                'sources': list(set(signal.source for signal in signals)),
                'analysis_timestamp': datetime.now().isoformat()
            }
        )
    
    def _create_prediction_signal(self, trend: Dict[str, Any]) -> Optional[PredictionSignal]:
        """Create prediction signal from trend data"""
        source = trend.get('source', '')
        title = trend.get('title', '')
        score = trend.get('score', 0)
        metadata = trend.get('metadata', {})
        
        # Calculate signal strength based on source and data
        strength = self._calculate_signal_strength(source, score, metadata)
        confidence = self._calculate_signal_confidence(source, metadata)
        direction = self._determine_signal_direction(source, score, metadata)
        
        if strength < 10:  # Filter out weak signals
            return None
        
        return PredictionSignal(
            source=source,
            signal_type=self._get_signal_type(source, metadata),
            strength=strength,
            direction=direction,
            confidence=confidence,
            metadata=metadata
        )
    
    def _calculate_signal_strength(self, source: str, score: float, metadata: Dict[str, Any]) -> float:
        """Calculate signal strength (0-100)"""
        base_score = min(score, 100)  # Cap at 100
        
        # Apply source-specific multipliers
        multipliers = {
            'GitHub': 1.2,  # GitHub stars are strong indicators
            'Google Trends': 1.0,
            'Reddit': 0.9,  # Community sentiment
            'Stack Overflow': 1.1,  # Developer adoption
            'Tech News': 0.8  # Media attention
        }
        
        multiplier = multipliers.get(source, 1.0)
        
        # Apply metadata bonuses
        if source == 'GitHub':
            stars = metadata.get('stars', 0)
            forks = metadata.get('forks', 0)
            # Bonus for high engagement
            if stars > 1000:
                multiplier += 0.2
            if forks > 100:
                multiplier += 0.1
        
        elif source == 'Reddit':
            upvotes = metadata.get('upvotes', 0)
            comments = metadata.get('comments', 0)
            # Bonus for high engagement
            if upvotes > 100:
                multiplier += 0.2
            if comments > 50:
                multiplier += 0.1
        
        elif source == 'Stack Overflow':
            views = metadata.get('views', 0)
            answers = metadata.get('answers', 0)
            # Bonus for high engagement
            if views > 1000:
                multiplier += 0.2
            if answers > 5:
                multiplier += 0.1
        
        return min(base_score * multiplier, 100)
    
    def _calculate_signal_confidence(self, source: str, metadata: Dict[str, Any]) -> float:
        """Calculate signal confidence (0-1)"""
        base_confidence = 0.7  # Default confidence
        
        # Source-specific confidence adjustments
        if source == 'GitHub':
            # High confidence for GitHub data
            base_confidence = 0.8
            stars = metadata.get('stars', 0)
            if stars > 100:
                base_confidence += 0.1
        
        elif source == 'Google Trends':
            # Medium confidence for search trends
            base_confidence = 0.6
            avg_interest = metadata.get('avg_interest', 0)
            if avg_interest > 50:
                base_confidence += 0.1
        
        elif source == 'Reddit':
            # Medium confidence for community sentiment
            base_confidence = 0.6
            upvotes = metadata.get('upvotes', 0)
            if upvotes > 50:
                base_confidence += 0.1
        
        elif source == 'Stack Overflow':
            # High confidence for developer adoption
            base_confidence = 0.7
            views = metadata.get('views', 0)
            if views > 500:
                base_confidence += 0.1
        
        elif source == 'Tech News':
            # Lower confidence for media coverage
            base_confidence = 0.5
        
        return min(base_confidence, 1.0)
    
    def _determine_signal_direction(self, source: str, score: float, metadata: Dict[str, Any]) -> TrendDirection:
        """Determine trend direction from signal"""
        # Simple rule-based direction determination
        if score > 70:
            return TrendDirection.RISING
        elif score > 40:
            return TrendDirection.STABLE
        else:
            return TrendDirection.DECLINING
    
    def _determine_trend_direction(self, signals: List[PredictionSignal]) -> TrendDirection:
        """Determine overall trend direction from multiple signals"""
        if not signals:
            return TrendDirection.UNKNOWN
        
        rising_count = sum(1 for s in signals if s.direction == TrendDirection.RISING)
        stable_count = sum(1 for s in signals if s.direction == TrendDirection.STABLE)
        declining_count = sum(1 for s in signals if s.direction == TrendDirection.DECLINING)
        
        total = len(signals)
        
        if rising_count / total > 0.5:
            return TrendDirection.RISING
        elif declining_count / total > 0.5:
            return TrendDirection.DECLINING
        else:
            return TrendDirection.STABLE
    
    def _determine_time_horizon(self, signals: List[PredictionSignal]) -> str:
        """Determine prediction time horizon"""
        # Simple heuristic based on signal types
        github_signals = [s for s in signals if s.source == 'GitHub']
        news_signals = [s for s in signals if s.source == 'Tech News']
        
        if github_signals and news_signals:
            return "medium"  # 3-6 months
        elif github_signals:
            return "long"    # 6+ months
        else:
            return "short"   # 1-3 months
    
    def _get_signal_type(self, source: str, metadata: Dict[str, Any]) -> str:
        """Get signal type based on source and metadata"""
        if source == 'GitHub':
            return "adoption_velocity"
        elif source == 'Google Trends':
            return "search_momentum"
        elif source == 'Reddit':
            return "community_sentiment"
        elif source == 'Stack Overflow':
            return "developer_adoption"
        elif source == 'Tech News':
            return "media_attention"
        else:
            return "general_trend"
    
    def _categorize_technology(self, tech_name: str) -> str:
        """Categorize technology"""
        categories = {
            'Python': 'Programming Language',
            'JavaScript': 'Programming Language',
            'React': 'Frontend Framework',
            'Vue': 'Frontend Framework',
            'Angular': 'Frontend Framework',
            'Node.js': 'Backend Framework',
            'Django': 'Backend Framework',
            'Flask': 'Backend Framework',
            'FastAPI': 'Backend Framework',
            'TensorFlow': 'AI/ML Framework',
            'PyTorch': 'AI/ML Framework',
            'Docker': 'DevOps Tool',
            'Kubernetes': 'DevOps Tool',
            'MongoDB': 'Database',
            'PostgreSQL': 'Database',
            'AI': 'Technology Category',
            'Machine Learning': 'Technology Category',
            'Blockchain': 'Technology Category'
        }
        
        return categories.get(tech_name, 'Other')
    
    def _generate_reasoning(self, tech_name: str, signals: List[PredictionSignal], 
                          potential_score: float, direction: TrendDirection) -> str:
        """Generate human-readable reasoning for prediction"""
        signal_sources = [s.source for s in signals]
        strong_signals = [s for s in signals if s.strength > 60]
        
        reasoning_parts = []
        
        # Overall assessment
        if potential_score > 70:
            reasoning_parts.append(f"{tech_name} shows strong potential with a score of {potential_score:.1f}")
        elif potential_score > 50:
            reasoning_parts.append(f"{tech_name} shows moderate potential with a score of {potential_score:.1f}")
        else:
            reasoning_parts.append(f"{tech_name} shows limited potential with a score of {potential_score:.1f}")
        
        # Direction
        if direction == TrendDirection.RISING:
            reasoning_parts.append("trending upward")
        elif direction == TrendDirection.DECLINING:
            reasoning_parts.append("trending downward")
        else:
            reasoning_parts.append("maintaining stable interest")
        
        # Data sources
        if len(signal_sources) > 1:
            reasoning_parts.append(f"supported by data from {', '.join(set(signal_sources))}")
        
        # Strong signals
        if strong_signals:
            strong_sources = [s.source for s in strong_signals]
            reasoning_parts.append(f"with particularly strong signals from {', '.join(set(strong_sources))}")
        
        return f"{tech_name} is " + ", ".join(reasoning_parts) + "."
    
    def generate_business_recommendations(self, predictions: List[TrendPrediction]) -> List[BusinessRecommendation]:
        """
        Generate business recommendations based on predictions
        
        Args:
            predictions: List of trend predictions
            
        Returns:
            List[BusinessRecommendation]: Business recommendations
        """
        recommendations = []
        
        for prediction in predictions:
            if prediction.confidence_score > 0.6:  # Only recommend for confident predictions
                recs = self._create_recommendations_for_trend(prediction)
                recommendations.extend(recs)
        
        # Sort by priority and confidence
        recommendations.sort(key=lambda x: (x.priority == 'high', x.confidence), reverse=True)
        
        return recommendations[:10]  # Top 10 recommendations
    
    def _create_recommendations_for_trend(self, prediction: TrendPrediction) -> List[BusinessRecommendation]:
        """Create business recommendations for a specific trend"""
        recommendations = []
        
        if prediction.potential_score > 70 and prediction.direction == TrendDirection.RISING:
            # High potential, rising trend
            recommendations.append(BusinessRecommendation(
                recommendation_type="adoption",
                priority="high",
                description=f"Consider adopting {prediction.name} for new projects",
                expected_impact="High - Early adoption advantage",
                timeline="1-3 months",
                confidence=prediction.confidence_score,
                supporting_data=[f"Potential score: {prediction.potential_score:.1f}", 
                               f"Trend direction: {prediction.direction.value}"]
            ))
            
            recommendations.append(BusinessRecommendation(
                recommendation_type="investment",
                priority="medium",
                description=f"Invest in training team on {prediction.name}",
                expected_impact="Medium - Skill development",
                timeline="3-6 months",
                confidence=prediction.confidence_score,
                supporting_data=[f"Category: {prediction.category}",
                               f"Time horizon: {prediction.time_horizon}"]
            ))
        
        elif prediction.potential_score > 50:
            # Medium potential
            recommendations.append(BusinessRecommendation(
                recommendation_type="monitoring",
                priority="medium",
                description=f"Monitor {prediction.name} for future opportunities",
                expected_impact="Low - Risk mitigation",
                timeline="6+ months",
                confidence=prediction.confidence_score,
                supporting_data=[f"Current potential: {prediction.potential_score:.1f}"]
            ))
        
        return recommendations
