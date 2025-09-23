#!/usr/bin/env python3
"""
🎯 NicheRadar Feedback - Learning Weights & Performance Tracking
==============================================================

Nhập số liệu thực chiến (thủ công hoặc tự động từ dashboard): 
impressions, clicks, signups, revenue (nếu có).

Cập nhật file data/feedback.csv.
Gợi ý điều chỉnh trọng số w* → ghi vào niche_weights.yaml.suggested.

Author: StillMe Framework Team
Version: 1.5.0
"""

import csv
import yaml
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import numpy as np

from .scoring import NicheScore

logger = logging.getLogger(__name__)

@dataclass
class FeedbackRecord:
    """Individual feedback record"""
    timestamp: datetime
    niche_topic: str
    niche_score: float
    confidence: float
    feasibility_fit: float
    competition_proxy: float
    
    # Performance metrics
    impressions: int = 0
    clicks: int = 0
    signups: int = 0
    trials: int = 0
    paid_conversions: int = 0
    revenue: float = 0.0
    
    # Engagement metrics
    time_to_first_value: float = 0.0  # hours
    user_engagement_score: float = 0.0  # 0-1
    support_tickets: int = 0
    
    # Source attribution
    traffic_source: str = "direct"
    campaign_id: str = ""
    
    # Additional context
    notes: str = ""

@dataclass
class LearningWeights:
    """Learning weights suggestion"""
    original_weights: Dict[str, float]
    suggested_weights: Dict[str, float]
    changes: Dict[str, float]
    confidence: float
    sample_size: int
    rationale: str
    timestamp: datetime

class FeedbackTracker:
    """Track and analyze feedback for learning weights"""
    
    def __init__(self, feedback_file: str = "data/feedback.csv"):
        self.feedback_file = Path(feedback_file)
        self.feedback_file.parent.mkdir(exist_ok=True)
        self.logger = logging.getLogger("niche_radar.feedback")
        
        # Initialize CSV file if it doesn't exist
        self._initialize_csv()
    
    def _initialize_csv(self):
        """Initialize CSV file with headers if it doesn't exist"""
        if not self.feedback_file.exists():
            headers = [
                "timestamp", "niche_topic", "niche_score", "confidence", 
                "feasibility_fit", "competition_proxy",
                "impressions", "clicks", "signups", "trials", "paid_conversions", "revenue",
                "time_to_first_value", "user_engagement_score", "support_tickets",
                "traffic_source", "campaign_id", "notes"
            ]
            
            with open(self.feedback_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
            
            self.logger.info(f"✅ Initialized feedback CSV: {self.feedback_file}")
    
    def add_feedback(self, feedback: FeedbackRecord):
        """Add feedback record to CSV"""
        try:
            with open(self.feedback_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    feedback.timestamp.isoformat(),
                    feedback.niche_topic,
                    feedback.niche_score,
                    feedback.confidence,
                    feedback.feasibility_fit,
                    feedback.competition_proxy,
                    feedback.impressions,
                    feedback.clicks,
                    feedback.signups,
                    feedback.trials,
                    feedback.paid_conversions,
                    feedback.revenue,
                    feedback.time_to_first_value,
                    feedback.user_engagement_score,
                    feedback.support_tickets,
                    feedback.traffic_source,
                    feedback.campaign_id,
                    feedback.notes
                ])
            
            self.logger.info(f"✅ Added feedback for niche: {feedback.niche_topic}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to add feedback: {e}")
    
    def get_feedback_data(self, days: int = 30) -> pd.DataFrame:
        """Get feedback data as DataFrame"""
        try:
            if not self.feedback_file.exists():
                return pd.DataFrame()
            
            df = pd.read_csv(self.feedback_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Filter by date range
            cutoff_date = datetime.now() - timedelta(days=days)
            df = df[df['timestamp'] >= cutoff_date]
            
            return df
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load feedback data: {e}")
            return pd.DataFrame()
    
    def calculate_performance_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate performance metrics from feedback data"""
        if df.empty:
            return {}
        
        metrics = {}
        
        # Conversion metrics
        total_impressions = df['impressions'].sum()
        total_clicks = df['clicks'].sum()
        total_signups = df['signups'].sum()
        total_trials = df['trials'].sum()
        total_paid = df['paid_conversions'].sum()
        total_revenue = df['revenue'].sum()
        
        metrics['conversion_rates'] = {
            'impression_to_click': total_clicks / total_impressions if total_impressions > 0 else 0,
            'click_to_signup': total_signups / total_clicks if total_clicks > 0 else 0,
            'signup_to_trial': total_trials / total_signups if total_signups > 0 else 0,
            'trial_to_paid': total_paid / total_trials if total_trials > 0 else 0,
            'overall_conversion': total_paid / total_impressions if total_impressions > 0 else 0
        }
        
        # Revenue metrics
        metrics['revenue'] = {
            'total_revenue': total_revenue,
            'revenue_per_impression': total_revenue / total_impressions if total_impressions > 0 else 0,
            'revenue_per_signup': total_revenue / total_signups if total_signups > 0 else 0,
            'revenue_per_paid': total_revenue / total_paid if total_paid > 0 else 0
        }
        
        # Engagement metrics
        metrics['engagement'] = {
            'avg_time_to_value': df['time_to_first_value'].mean(),
            'avg_engagement_score': df['user_engagement_score'].mean(),
            'avg_support_tickets': df['support_tickets'].mean()
        }
        
        # Niche performance correlation
        metrics['niche_correlations'] = {
            'score_vs_conversion': df['niche_score'].corr(df['paid_conversions']),
            'confidence_vs_engagement': df['confidence'].corr(df['user_engagement_score']),
            'feasibility_vs_revenue': df['feasibility_fit'].corr(df['revenue']),
            'competition_vs_conversion': df['competition_proxy'].corr(df['paid_conversions'])
        }
        
        return metrics
    
    def analyze_weight_effectiveness(self, df: pd.DataFrame) -> Dict[str, float]:
        """Analyze effectiveness of current weights"""
        if df.empty:
            return {}
        
        # Calculate correlation between each weight component and performance
        performance_metrics = ['paid_conversions', 'revenue', 'user_engagement_score']
        weight_components = ['niche_score', 'confidence', 'feasibility_fit', 'competition_proxy']
        
        effectiveness = {}
        
        for component in weight_components:
            correlations = []
            for metric in performance_metrics:
                if metric in df.columns and component in df.columns:
                    corr = df[component].corr(df[metric])
                    if not np.isnan(corr):
                        correlations.append(corr)
            
            # Average correlation across performance metrics
            effectiveness[component] = np.mean(correlations) if correlations else 0.0
        
        return effectiveness
    
    def suggest_weight_adjustments(self, current_weights: Dict[str, float], 
                                 days: int = 30) -> LearningWeights:
        """Suggest weight adjustments based on feedback"""
        try:
            df = self.get_feedback_data(days)
            
            if df.empty or len(df) < 5:  # Need minimum samples
                return LearningWeights(
                    original_weights=current_weights,
                    suggested_weights=current_weights.copy(),
                    changes={},
                    confidence=0.0,
                    sample_size=len(df),
                    rationale="Insufficient data for weight adjustments",
                    timestamp=datetime.now()
                )
            
            # Analyze effectiveness
            effectiveness = self.analyze_weight_effectiveness(df)
            performance_metrics = self.calculate_performance_metrics(df)
            
            # Calculate suggested adjustments
            suggested_weights = current_weights.copy()
            changes = {}
            
            # Map effectiveness to weight components
            weight_mapping = {
                'trend_momentum': 'niche_score',
                'github_velocity': 'niche_score', 
                'hackernews_heat': 'niche_score',
                'news_delta': 'niche_score',
                'reddit_engagement': 'niche_score',
                'feasibility_fit': 'feasibility_fit',
                'competition_proxy': 'competition_proxy'
            }
            
            # Adjust weights based on effectiveness
            for weight_name, component in weight_mapping.items():
                if weight_name in current_weights and component in effectiveness:
                    effectiveness_score = effectiveness[component]
                    
                    # Adjust weight based on effectiveness
                    # Positive correlation = increase weight, negative = decrease
                    adjustment_factor = 1.0 + (effectiveness_score * 0.1)  # Max 10% change
                    adjustment_factor = max(0.5, min(1.5, adjustment_factor))  # Limit to 50%-150%
                    
                    old_weight = current_weights[weight_name]
                    new_weight = old_weight * adjustment_factor
                    change = new_weight - old_weight
                    
                    suggested_weights[weight_name] = new_weight
                    changes[weight_name] = change
            
            # Normalize weights to sum to 1.0
            total_weight = sum(suggested_weights.values())
            if total_weight > 0:
                for key in suggested_weights:
                    suggested_weights[key] /= total_weight
            
            # Calculate confidence in suggestions
            sample_size = len(df)
            confidence = min(1.0, sample_size / 50.0)  # Max confidence at 50 samples
            
            # Generate rationale
            rationale_parts = []
            if sample_size >= 10:
                rationale_parts.append(f"Based on {sample_size} feedback samples")
            
            if performance_metrics.get('conversion_rates', {}).get('overall_conversion', 0) > 0.05:
                rationale_parts.append("Strong conversion performance observed")
            
            if any(abs(change) > 0.02 for change in changes.values()):
                rationale_parts.append("Significant weight adjustments recommended")
            
            rationale = ". ".join(rationale_parts) if rationale_parts else "Minimal adjustments based on limited data"
            
            return LearningWeights(
                original_weights=current_weights,
                suggested_weights=suggested_weights,
                changes=changes,
                confidence=confidence,
                sample_size=sample_size,
                rationale=rationale,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"❌ Weight adjustment suggestion failed: {e}")
            return LearningWeights(
                original_weights=current_weights,
                suggested_weights=current_weights.copy(),
                changes={},
                confidence=0.0,
                sample_size=0,
                rationale=f"Error in analysis: {str(e)}",
                timestamp=datetime.now()
            )
    
    def export_suggested_weights(self, learning_weights: LearningWeights, 
                               output_file: str = "policies/niche_weights.yaml.suggested"):
        """Export suggested weights to YAML file"""
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(exist_ok=True)
            
            # Load current weights structure
            current_weights_file = "policies/niche_weights.yaml"
            if Path(current_weights_file).exists():
                with open(current_weights_file, 'r', encoding='utf-8') as f:
                    weights_structure = yaml.safe_load(f)
            else:
                weights_structure = {"scoring_weights": {}}
            
            # Update with suggested weights
            weights_structure["scoring_weights"] = learning_weights.suggested_weights
            
            # Add metadata
            weights_structure["_metadata"] = {
                "suggested_at": learning_weights.timestamp.isoformat(),
                "confidence": learning_weights.confidence,
                "sample_size": learning_weights.sample_size,
                "rationale": learning_weights.rationale,
                "changes": learning_weights.changes
            }
            
            # Write suggested weights
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(weights_structure, f, default_flow_style=False, allow_unicode=True)
            
            self.logger.info(f"✅ Exported suggested weights to: {output_path}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to export suggested weights: {e}")
    
    def get_performance_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get performance summary for dashboard"""
        df = self.get_feedback_data(days)
        
        if df.empty:
            return {
                "status": "no_data",
                "message": "No feedback data available",
                "metrics": {}
            }
        
        metrics = self.calculate_performance_metrics(df)
        
        # Calculate trends
        recent_df = df[df['timestamp'] >= datetime.now() - timedelta(days=7)]
        older_df = df[df['timestamp'] < datetime.now() - timedelta(days=7)]
        
        trends = {}
        if not recent_df.empty and not older_df.empty:
            for metric in ['impressions', 'clicks', 'signups', 'revenue']:
                if metric in df.columns:
                    recent_avg = recent_df[metric].mean()
                    older_avg = older_df[metric].mean()
                    if older_avg > 0:
                        trends[metric] = (recent_avg - older_avg) / older_avg
        
        return {
            "status": "success",
            "period_days": days,
            "total_records": len(df),
            "metrics": metrics,
            "trends": trends,
            "top_performing_niches": df.groupby('niche_topic')['revenue'].sum().nlargest(5).to_dict()
        }

def update_weights_suggestion(feedback_file: str = "data/feedback.csv", 
                            weights_file: str = "policies/niche_weights.yaml",
                            output_file: str = "policies/niche_weights.yaml.suggested") -> LearningWeights:
    """Convenience function to update weight suggestions"""
    tracker = FeedbackTracker(feedback_file)
    
    # Load current weights
    try:
        with open(weights_file, 'r', encoding='utf-8') as f:
            weights_data = yaml.safe_load(f)
        current_weights = weights_data.get("scoring_weights", {})
    except:
        current_weights = {}
    
    # Generate suggestions
    learning_weights = tracker.suggest_weight_adjustments(current_weights)
    
    # Export suggestions
    tracker.export_suggested_weights(learning_weights, output_file)
    
    return learning_weights

if __name__ == "__main__":
    # Test feedback tracking
    tracker = FeedbackTracker()
    
    # Add sample feedback
    sample_feedback = FeedbackRecord(
        timestamp=datetime.now(),
        niche_topic="ai_translation",
        niche_score=0.75,
        confidence=0.8,
        feasibility_fit=0.9,
        competition_proxy=0.4,
        impressions=1000,
        clicks=50,
        signups=10,
        trials=8,
        paid_conversions=2,
        revenue=98.0,
        time_to_first_value=2.5,
        user_engagement_score=0.7,
        support_tickets=1,
        traffic_source="google_ads",
        campaign_id="translation_001",
        notes="Good initial performance"
    )
    
    tracker.add_feedback(sample_feedback)
    
    # Test weight suggestions
    current_weights = {
        "trend_momentum": 0.20,
        "github_velocity": 0.15,
        "hackernews_heat": 0.10,
        "news_delta": 0.10,
        "reddit_engagement": 0.05,
        "competition_proxy": 0.15,
        "feasibility_fit": 0.25
    }
    
    learning_weights = tracker.suggest_weight_adjustments(current_weights)
    print(f"🎯 Weight suggestions:")
    print(f"  Confidence: {learning_weights.confidence:.2f}")
    print(f"  Sample size: {learning_weights.sample_size}")
    print(f"  Rationale: {learning_weights.rationale}")
    print(f"  Changes: {learning_weights.changes}")
    
    # Export suggestions
    tracker.export_suggested_weights(learning_weights)
