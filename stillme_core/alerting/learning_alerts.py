"""
🧠 StillMe Learning Alert Integration
====================================

Specialized alert integration for learning system monitoring.
Provides AGI-specific alert templates and intelligent alerting
for learning automation, evolution milestones, and performance tracking.

Tính năng:
- Learning-specific alert templates
- Evolution milestone notifications
- Performance degradation alerts
- Resource exhaustion warnings
- Learning session failure alerts
- AGI progress tracking
- Intelligent alert escalation

Author: StillMe AI Framework
Version: 2.0.0
Date: 2025-09-28
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from .alert_manager import get_alert_manager, AlertManager

logger = logging.getLogger(__name__)

@dataclass
class LearningMetrics:
    """Learning system metrics for alerting"""
    session_id: str
    timestamp: datetime
    evolution_stage: str
    learning_accuracy: float
    training_time: float
    memory_usage: float
    cpu_usage: float
    token_consumption: int
    error_count: int
    success_rate: float
    knowledge_items_processed: int
    performance_score: float

class LearningAlertManager:
    """
    Specialized alert manager for learning system
    """
    
    def __init__(self, alert_manager: AlertManager = None):
        self.alert_manager = alert_manager or get_alert_manager()
        self.logger = logging.getLogger(__name__)
        
        # Learning-specific thresholds
        self.thresholds = {
            'memory_usage_mb': 2048,  # 2GB
            'cpu_usage_percent': 80,
            'learning_accuracy_min': 0.7,
            'error_rate_max': 0.1,  # 10%
            'training_time_max': 3600,  # 1 hour
            'token_budget_daily': 10000,
            'performance_score_min': 0.6
        }
        
        # Evolution milestone tracking
        self.evolution_milestones = {
            'infant': ['first_learning_session', 'first_knowledge_item', 'first_assessment'],
            'child': ['100_sessions', '1000_knowledge_items', 'accuracy_80_percent'],
            'adolescent': ['10000_sessions', '100000_knowledge_items', 'accuracy_90_percent'],
            'adult': ['100000_sessions', '1000000_knowledge_items', 'accuracy_95_percent']
        }
        
        # Tracked milestones
        self.achieved_milestones = set()
        
        # Performance tracking
        self.performance_history = []
        self.degradation_threshold = 0.1  # 10% degradation
    
    async def check_learning_session_alerts(self, metrics: LearningMetrics) -> List[str]:
        """Check and send alerts for learning session"""
        alerts_sent = []
        
        # Check resource usage
        if metrics.memory_usage > self.thresholds['memory_usage_mb']:
            alert_id = await self.alert_manager.send_alert(
                alert_type='resource_high',
                severity='high',
                title='High Memory Usage in Learning Session',
                message=f'Memory usage is {metrics.memory_usage:.1f}MB (limit: {self.thresholds["memory_usage_mb"]}MB)',
                component='learning_system',
                context={
                    'session_id': metrics.session_id,
                    'memory_usage_mb': metrics.memory_usage,
                    'limit_mb': self.thresholds['memory_usage_mb'],
                    'evolution_stage': metrics.evolution_stage,
                    'metrics': {
                        'Memory Usage': f'{metrics.memory_usage:.1f}MB',
                        'CPU Usage': f'{metrics.cpu_usage:.1f}%',
                        'Training Time': f'{metrics.training_time:.1f}s',
                        'Accuracy': f'{metrics.learning_accuracy:.2%}'
                    }
                },
                channels=['email', 'desktop', 'telegram']
            )
            alerts_sent.append(alert_id)
        
        if metrics.cpu_usage > self.thresholds['cpu_usage_percent']:
            alert_id = await self.alert_manager.send_alert(
                alert_type='resource_high',
                severity='medium',
                title='High CPU Usage in Learning Session',
                message=f'CPU usage is {metrics.cpu_usage:.1f}% (limit: {self.thresholds["cpu_usage_percent"]}%)',
                component='learning_system',
                context={
                    'session_id': metrics.session_id,
                    'cpu_usage_percent': metrics.cpu_usage,
                    'limit_percent': self.thresholds['cpu_usage_percent'],
                    'evolution_stage': metrics.evolution_stage,
                    'metrics': {
                        'CPU Usage': f'{metrics.cpu_usage:.1f}%',
                        'Memory Usage': f'{metrics.memory_usage:.1f}MB',
                        'Training Time': f'{metrics.training_time:.1f}s',
                        'Accuracy': f'{metrics.learning_accuracy:.2%}'
                    }
                },
                channels=['email', 'desktop', 'telegram']
            )
            alerts_sent.append(alert_id)
        
        # Check learning accuracy
        if metrics.learning_accuracy < self.thresholds['learning_accuracy_min']:
            alert_id = await self.alert_manager.send_alert(
                alert_type='learning_failure',
                severity='high',
                title='Low Learning Accuracy',
                message=f'Learning accuracy is {metrics.learning_accuracy:.2%} (minimum: {self.thresholds["learning_accuracy_min"]:.2%})',
                component='learning_system',
                context={
                    'session_id': metrics.session_id,
                    'learning_accuracy': metrics.learning_accuracy,
                    'minimum_accuracy': self.thresholds['learning_accuracy_min'],
                    'evolution_stage': metrics.evolution_stage,
                    'error_count': metrics.error_count,
                    'metrics': {
                        'Accuracy': f'{metrics.learning_accuracy:.2%}',
                        'Error Count': metrics.error_count,
                        'Success Rate': f'{metrics.success_rate:.2%}',
                        'Performance Score': f'{metrics.performance_score:.2f}'
                    }
                },
                channels=['email', 'desktop', 'telegram']
            )
            alerts_sent.append(alert_id)
        
        # Check error rate
        error_rate = metrics.error_count / max(metrics.knowledge_items_processed, 1)
        if error_rate > self.thresholds['error_rate_max']:
            alert_id = await self.alert_manager.send_alert(
                alert_type='learning_failure',
                severity='high',
                title='High Error Rate in Learning',
                message=f'Error rate is {error_rate:.2%} (maximum: {self.thresholds["error_rate_max"]:.2%})',
                component='learning_system',
                context={
                    'session_id': metrics.session_id,
                    'error_rate': error_rate,
                    'maximum_error_rate': self.thresholds['error_rate_max'],
                    'error_count': metrics.error_count,
                    'items_processed': metrics.knowledge_items_processed,
                    'evolution_stage': metrics.evolution_stage,
                    'metrics': {
                        'Error Rate': f'{error_rate:.2%}',
                        'Error Count': metrics.error_count,
                        'Items Processed': metrics.knowledge_items_processed,
                        'Success Rate': f'{metrics.success_rate:.2%}'
                    }
                },
                channels=['email', 'desktop', 'telegram']
            )
            alerts_sent.append(alert_id)
        
        # Check training time
        if metrics.training_time > self.thresholds['training_time_max']:
            alert_id = await self.alert_manager.send_alert(
                alert_type='performance_degradation',
                severity='medium',
                title='Long Training Time',
                message=f'Training time is {metrics.training_time:.1f}s (maximum: {self.thresholds["training_time_max"]}s)',
                component='learning_system',
                context={
                    'session_id': metrics.session_id,
                    'training_time': metrics.training_time,
                    'maximum_time': self.thresholds['training_time_max'],
                    'evolution_stage': metrics.evolution_stage,
                    'metrics': {
                        'Training Time': f'{metrics.training_time:.1f}s',
                        'Memory Usage': f'{metrics.memory_usage:.1f}MB',
                        'CPU Usage': f'{metrics.cpu_usage:.1f}%',
                        'Accuracy': f'{metrics.learning_accuracy:.2%}'
                    }
                },
                channels=['email', 'desktop', 'telegram']
            )
            alerts_sent.append(alert_id)
        
        # Check performance score
        if metrics.performance_score < self.thresholds['performance_score_min']:
            alert_id = await self.alert_manager.send_alert(
                alert_type='performance_degradation',
                severity='medium',
                title='Low Performance Score',
                message=f'Performance score is {metrics.performance_score:.2f} (minimum: {self.thresholds["performance_score_min"]:.2f})',
                component='learning_system',
                context={
                    'session_id': metrics.session_id,
                    'performance_score': metrics.performance_score,
                    'minimum_score': self.thresholds['performance_score_min'],
                    'evolution_stage': metrics.evolution_stage,
                    'metrics': {
                        'Performance Score': f'{metrics.performance_score:.2f}',
                        'Accuracy': f'{metrics.learning_accuracy:.2%}',
                        'Success Rate': f'{metrics.success_rate:.2%}',
                        'Training Time': f'{metrics.training_time:.1f}s'
                    }
                },
                channels=['email', 'desktop', 'telegram']
            )
            alerts_sent.append(alert_id)
        
        return alerts_sent
    
    async def check_evolution_milestones(self, metrics: LearningMetrics) -> List[str]:
        """Check and send alerts for evolution milestones"""
        alerts_sent = []
        
        # Check for new milestones
        current_stage = metrics.evolution_stage.lower()
        stage_milestones = self.evolution_milestones.get(current_stage, [])
        
        for milestone in stage_milestones:
            milestone_key = f"{current_stage}_{milestone}"
            
            if milestone_key not in self.achieved_milestones:
                # Check if milestone is achieved
                if self._check_milestone_achieved(milestone, metrics):
                    self.achieved_milestones.add(milestone_key)
                    
                    alert_id = await self.alert_manager.send_alert(
                        alert_type='evolution_milestone',
                        severity='medium',
                        title=f'AGI Evolution Milestone: {milestone.replace("_", " ").title()}',
                        message=f'StillMe has achieved the {milestone.replace("_", " ")} milestone in {current_stage} stage',
                        component='evolution_system',
                        context={
                            'milestone_name': milestone,
                            'evolution_stage': current_stage,
                            'session_id': metrics.session_id,
                            'achievement_time': metrics.timestamp.isoformat(),
                            'metrics': {
                                'Evolution Stage': current_stage.title(),
                                'Milestone': milestone.replace('_', ' ').title(),
                                'Session ID': metrics.session_id,
                                'Accuracy': f'{metrics.learning_accuracy:.2%}',
                                'Performance Score': f'{metrics.performance_score:.2f}'
                            }
                        },
                        channels=['email', 'telegram']
                    )
                    alerts_sent.append(alert_id)
        
        return alerts_sent
    
    def _check_milestone_achieved(self, milestone: str, metrics: LearningMetrics) -> bool:
        """Check if a specific milestone is achieved"""
        if milestone == 'first_learning_session':
            return True  # This is the first session
        
        elif milestone == 'first_knowledge_item':
            return metrics.knowledge_items_processed >= 1
        
        elif milestone == 'first_assessment':
            return metrics.learning_accuracy > 0
        
        elif milestone == '100_sessions':
            # This would need to be tracked across sessions
            return False  # Placeholder
        
        elif milestone == '1000_knowledge_items':
            return metrics.knowledge_items_processed >= 1000
        
        elif milestone == 'accuracy_80_percent':
            return metrics.learning_accuracy >= 0.8
        
        elif milestone == '10000_sessions':
            return False  # Placeholder
        
        elif milestone == '100000_knowledge_items':
            return metrics.knowledge_items_processed >= 100000
        
        elif milestone == 'accuracy_90_percent':
            return metrics.learning_accuracy >= 0.9
        
        elif milestone == '100000_sessions':
            return False  # Placeholder
        
        elif milestone == '1000000_knowledge_items':
            return metrics.knowledge_items_processed >= 1000000
        
        elif milestone == 'accuracy_95_percent':
            return metrics.learning_accuracy >= 0.95
        
        return False
    
    async def check_performance_degradation(self, metrics: LearningMetrics) -> List[str]:
        """Check for performance degradation"""
        alerts_sent = []
        
        # Add current metrics to history
        self.performance_history.append(metrics)
        
        # Keep only last 10 sessions for comparison
        if len(self.performance_history) > 10:
            self.performance_history.pop(0)
        
        # Need at least 2 sessions to compare
        if len(self.performance_history) < 2:
            return alerts_sent
        
        # Compare with previous session
        previous_metrics = self.performance_history[-2]
        
        # Check accuracy degradation
        accuracy_change = metrics.learning_accuracy - previous_metrics.learning_accuracy
        if accuracy_change < -self.degradation_threshold:
            alert_id = await self.alert_manager.send_alert(
                alert_type='performance_degradation',
                severity='medium',
                title='Learning Accuracy Degradation',
                message=f'Learning accuracy decreased by {abs(accuracy_change):.2%} from {previous_metrics.learning_accuracy:.2%} to {metrics.learning_accuracy:.2%}',
                component='learning_system',
                context={
                    'session_id': metrics.session_id,
                    'previous_accuracy': previous_metrics.learning_accuracy,
                    'current_accuracy': metrics.learning_accuracy,
                    'degradation_percent': abs(accuracy_change),
                    'evolution_stage': metrics.evolution_stage,
                    'metrics': {
                        'Previous Accuracy': f'{previous_metrics.learning_accuracy:.2%}',
                        'Current Accuracy': f'{metrics.learning_accuracy:.2%}',
                        'Degradation': f'{abs(accuracy_change):.2%}',
                        'Performance Score': f'{metrics.performance_score:.2f}'
                    }
                },
                channels=['email', 'desktop', 'telegram']
            )
            alerts_sent.append(alert_id)
        
        # Check performance score degradation
        performance_change = metrics.performance_score - previous_metrics.performance_score
        if performance_change < -self.degradation_threshold:
            alert_id = await self.alert_manager.send_alert(
                alert_type='performance_degradation',
                severity='medium',
                title='Performance Score Degradation',
                message=f'Performance score decreased by {abs(performance_change):.2f} from {previous_metrics.performance_score:.2f} to {metrics.performance_score:.2f}',
                component='learning_system',
                context={
                    'session_id': metrics.session_id,
                    'previous_score': previous_metrics.performance_score,
                    'current_score': metrics.performance_score,
                    'degradation_percent': abs(performance_change),
                    'evolution_stage': metrics.evolution_stage,
                    'metrics': {
                        'Previous Score': f'{previous_metrics.performance_score:.2f}',
                        'Current Score': f'{metrics.performance_score:.2f}',
                        'Degradation': f'{abs(performance_change):.2f}',
                        'Accuracy': f'{metrics.learning_accuracy:.2%}'
                    }
                },
                channels=['email', 'desktop', 'telegram']
            )
            alerts_sent.append(alert_id)
        
        return alerts_sent
    
    async def send_learning_session_failure(self, session_id: str, error_message: str, 
                                          component: str = 'learning_system') -> str:
        """Send alert for learning session failure"""
        return await self.alert_manager.send_alert(
            alert_type='learning_failure',
            severity='high',
            title='Learning Session Failed',
            message=f'Learning session {session_id} failed: {error_message}',
            component=component,
            context={
                'session_id': session_id,
                'error_message': error_message,
                'failure_time': datetime.now().isoformat(),
                'metrics': {
                    'Session ID': session_id,
                    'Error': error_message,
                    'Component': component,
                    'Time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            },
            channels=['email', 'desktop', 'telegram', 'sms']
        )
    
    async def send_system_critical_error(self, error_message: str, component: str = 'system') -> str:
        """Send alert for critical system error"""
        return await self.alert_manager.send_alert(
            alert_type='system_critical',
            severity='critical',
            title='Critical System Error',
            message=f'Critical error in {component}: {error_message}',
            component=component,
            context={
                'error_message': error_message,
                'component': component,
                'error_time': datetime.now().isoformat(),
                'metrics': {
                    'Error': error_message,
                    'Component': component,
                    'Time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'Severity': 'CRITICAL'
                }
            },
            channels=['email', 'desktop', 'telegram', 'sms']
        )
    
    async def send_resource_exhaustion_warning(self, resource_type: str, current_usage: float, 
                                             limit: float, component: str = 'resource_monitor') -> str:
        """Send alert for resource exhaustion warning"""
        severity = 'critical' if current_usage >= limit * 0.95 else 'high'
        
        return await self.alert_manager.send_alert(
            alert_type='resource_high',
            severity=severity,
            title=f'{resource_type.title()} Resource Exhaustion Warning',
            message=f'{resource_type} usage is {current_usage:.1f} (limit: {limit:.1f}) - {current_usage/limit:.1%} of limit',
            component=component,
            context={
                'resource_type': resource_type,
                'current_usage': current_usage,
                'limit': limit,
                'usage_percent': current_usage / limit,
                'warning_time': datetime.now().isoformat(),
                'metrics': {
                    'Resource Type': resource_type.title(),
                    'Current Usage': f'{current_usage:.1f}',
                    'Limit': f'{limit:.1f}',
                    'Usage %': f'{current_usage/limit:.1%}',
                    'Time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            },
            channels=['email', 'desktop', 'telegram', 'sms'] if severity == 'critical' else ['email', 'desktop', 'telegram']
        )
    
    def get_learning_alert_statistics(self) -> Dict[str, Any]:
        """Get learning-specific alert statistics"""
        return {
            'achieved_milestones': list(self.achieved_milestones),
            'performance_history_count': len(self.performance_history),
            'thresholds': self.thresholds,
            'degradation_threshold': self.degradation_threshold,
            'evolution_milestones': self.evolution_milestones,
            'alert_manager_stats': self.alert_manager.get_alert_statistics()
        }

# Global learning alert manager instance
_learning_alert_manager_instance: Optional[LearningAlertManager] = None

def get_learning_alert_manager() -> LearningAlertManager:
    """Get global learning alert manager instance"""
    global _learning_alert_manager_instance
    if _learning_alert_manager_instance is None:
        _learning_alert_manager_instance = LearningAlertManager()
    return _learning_alert_manager_instance

async def check_learning_alerts(metrics: LearningMetrics) -> List[str]:
    """Convenience function to check all learning alerts"""
    manager = get_learning_alert_manager()
    
    alerts_sent = []
    
    # Check session alerts
    session_alerts = await manager.check_learning_session_alerts(metrics)
    alerts_sent.extend(session_alerts)
    
    # Check evolution milestones
    milestone_alerts = await manager.check_evolution_milestones(metrics)
    alerts_sent.extend(milestone_alerts)
    
    # Check performance degradation
    degradation_alerts = await manager.check_performance_degradation(metrics)
    alerts_sent.extend(degradation_alerts)
    
    return alerts_sent
