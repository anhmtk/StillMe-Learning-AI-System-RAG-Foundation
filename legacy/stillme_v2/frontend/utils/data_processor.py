"""
Data processing utilities for the frontend
"""

import pandas as pd
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DataProcessor:
    """Processes and transforms data for visualization"""
    
    @staticmethod
    def process_evolution_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Process evolution metrics for display"""
        
        if not metrics or 'error' in metrics:
            return {"error": "Invalid metrics data"}
        
        processed = metrics.copy()
        
        # Calculate additional derived metrics
        if processed.get('total_sessions', 0) > 0:
            processed['efficiency_score'] = (
                processed.get('success_rate', 0) * 
                processed.get('average_proposals_per_session', 0) / 100
            )
        else:
            processed['efficiency_score'] = 0
        
        # Format percentages
        if 'success_rate' in processed:
            processed['success_rate_formatted'] = f"{processed['success_rate']:.1f}%"
        
        return processed
    
    @staticmethod
    def process_learning_history(history: List[Dict[str, Any]]) -> pd.DataFrame:
        """Process learning history into DataFrame"""
        
        if not history:
            return pd.DataFrame()
        
        df_data = []
        for session in history:
            df_data.append({
                'session_id': session.get('session_id', ''),
                'date': session.get('date', ''),
                'proposals_learned': session.get('proposals_learned', 0),
                'evolution_stage': session.get('evolution_stage', 'unknown'),
                'duration_minutes': session.get('duration_minutes', 0),
                'success': session.get('success', False),
                'accuracy_delta': session.get('accuracy_delta', 0),
                'created_at': session.get('created_at', '')
            })
        
        df = pd.DataFrame(df_data)
        
        # Convert date columns
        if not df.empty and 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date', ascending=False)
        
        return df
    
    @staticmethod
    def calculate_learning_trend(history: List[Dict[str, Any]], window: int = 5) -> str:
        """Calculate learning trend from history"""
        
        if len(history) < 2:
            return "insufficient_data"
        
        recent_sessions = history[:window]
        proposals_trend = [s.get('proposals_learned', 0) for s in recent_sessions]
        
        if len(proposals_trend) < 2:
            return "stable"
        
        # Simple trend calculation
        first_half = proposals_trend[:len(proposals_trend)//2]
        second_half = proposals_trend[len(proposals_trend)//2:]
        
        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)
        
        if avg_second > avg_first * 1.1:  # 10% improvement
            return "improving"
        elif avg_second < avg_first * 0.9:  # 10% decline
            return "declining"
        else:
            return "stable"
    
    @staticmethod
    def prepare_chart_data(metrics: Dict[str, Any], history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare data for charts and visualizations"""
        
        chart_data = {
            'stage_distribution': metrics.get('stage_distribution', {}),
            'timeline_data': [],
            'performance_metrics': {}
        }
        
        # Prepare timeline data
        for session in history[:20]:  # Last 20 sessions
            chart_data['timeline_data'].append({
                'date': session.get('date', ''),
                'proposals_learned': session.get('proposals_learned', 0),
                'stage': session.get('evolution_stage', 'unknown'),
                'success': session.get('success', False)
            })
        
        # Calculate performance metrics
        if history:
            success_rate = sum(1 for s in history if s.get('success', False)) / len(history) * 100
            avg_proposals = sum(s.get('proposals_learned', 0) for s in history) / len(history)
            avg_duration = sum(s.get('duration_minutes', 0) for s in history) / len(history)
            
            chart_data['performance_metrics'] = {
                'success_rate': success_rate,
                'avg_proposals': avg_proposals,
                'avg_duration': avg_duration,
                'total_sessions': len(history)
            }
        
        return chart_data