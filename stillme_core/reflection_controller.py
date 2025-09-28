"""Reflection Controller for StillMe Framework"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class ReflectionType(Enum):
    SELF_ASSESSMENT = "self_assessment"
    PERFORMANCE_REVIEW = "performance_review"
    ERROR_ANALYSIS = "error_analysis"
    LEARNING_REFLECTION = "learning_reflection"
    ETHICS_REFLECTION = "ethics_reflection"

class ReflectionStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class ReflectionMode(Enum):
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"
    EMERGENCY = "emergency"

@dataclass
class ReflectionResult:
    """Reflection result record"""
    result_id: str
    session_id: str
    enhanced_response: str
    confidence_score: float
    processing_time: float
    steps_taken: int
    insights: List[str]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ReflectionSession:
    """Reflection session record"""
    session_id: str
    reflection_type: ReflectionType
    status: ReflectionStatus
    title: str
    description: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    insights: List[str] = None
    improvements: List[str] = None
    action_items: List[str] = None
    confidence_score: Optional[float] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.insights is None:
            self.insights = []
        if self.improvements is None:
            self.improvements = []
        if self.action_items is None:
            self.action_items = []
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ReflectionConfig:
    """Reflection configuration"""
    max_reflection_duration: int = 30  # minutes
    min_reflection_duration: int = 5   # minutes
    reflection_frequency: str = "daily"
    auto_reflection_enabled: bool = True
    max_steps: int = 3
    max_latency_s: float = 5.0
    confidence_threshold: float = 0.7

@dataclass
class ReflectionContext:
    """Reflection context record"""
    context_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    topic: Optional[str] = None
    domain: Optional[str] = None
    urgency: str = "normal"
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class ReflectionController:
    """Reflection controller for StillMe Framework"""
    
    def __init__(self, config: ReflectionConfig = None):
        self.logger = logger
        self.reflection_sessions: List[ReflectionSession] = []
        self.config = config or ReflectionConfig()
        self.reflection_config = self._initialize_reflection_config()
        self.logger.info("✅ ReflectionController initialized")
    
    def _initialize_reflection_config(self) -> Dict[str, Any]:
        """Initialize reflection configuration"""
        return {
            "max_reflection_duration": 30,  # minutes
            "min_reflection_duration": 5,   # minutes
            "reflection_frequency": "daily",
            "auto_reflection_enabled": True,
            "reflection_categories": [
                "performance",
                "learning",
                "ethics",
                "security",
                "user_satisfaction"
            ],
            "confidence_threshold": 0.7
        }
    
    def start_reflection_session(self, 
                                reflection_type: ReflectionType,
                                title: str,
                                description: str,
                                metadata: Dict[str, Any] = None) -> ReflectionSession:
        """Start a new reflection session"""
        try:
            session_id = f"reflection_{len(self.reflection_sessions) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            session = ReflectionSession(
                session_id=session_id,
                reflection_type=reflection_type,
                status=ReflectionStatus.IN_PROGRESS,
                title=title,
                description=description,
                start_time=datetime.now(),
                metadata=metadata or {}
            )
            
            self.reflection_sessions.append(session)
            self.logger.info(f"🤔 Reflection session started: {title} (ID: {session_id})")
            return session
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start reflection session: {e}")
            raise
    
    def complete_reflection_session(self, 
                                   session_id: str,
                                   insights: List[str] = None,
                                   improvements: List[str] = None,
                                   action_items: List[str] = None,
                                   confidence_score: float = None) -> bool:
        """Complete a reflection session"""
        try:
            for session in self.reflection_sessions:
                if session.session_id == session_id:
                    session.status = ReflectionStatus.COMPLETED
                    session.end_time = datetime.now()
                    session.duration = (session.end_time - session.start_time).total_seconds()
                    
                    if insights:
                        session.insights.extend(insights)
                    if improvements:
                        session.improvements.extend(improvements)
                    if action_items:
                        session.action_items.extend(action_items)
                    if confidence_score is not None:
                        session.confidence_score = confidence_score
                    
                    self.logger.info(f"✅ Reflection session completed: {session.title} (ID: {session_id})")
                    return True
            
            self.logger.warning(f"⚠️ Reflection session not found: {session_id}")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Failed to complete reflection session: {e}")
            return False
    
    def fail_reflection_session(self, session_id: str, error_message: str) -> bool:
        """Mark a reflection session as failed"""
        try:
            for session in self.reflection_sessions:
                if session.session_id == session_id:
                    session.status = ReflectionStatus.FAILED
                    session.end_time = datetime.now()
                    session.duration = (session.end_time - session.start_time).total_seconds()
                    session.metadata["error_message"] = error_message
                    
                    self.logger.error(f"❌ Reflection session failed: {session.title} (ID: {session_id}) - {error_message}")
                    return True
            
            self.logger.warning(f"⚠️ Reflection session not found: {session_id}")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Failed to fail reflection session: {e}")
            return False
    
    def get_reflection_sessions_by_type(self, reflection_type: ReflectionType) -> List[ReflectionSession]:
        """Get reflection sessions by type"""
        return [s for s in self.reflection_sessions if s.reflection_type == reflection_type]
    
    def get_reflection_sessions_by_status(self, status: ReflectionStatus) -> List[ReflectionSession]:
        """Get reflection sessions by status"""
        return [s for s in self.reflection_sessions if s.status == status]
    
    def get_active_reflection_sessions(self) -> List[ReflectionSession]:
        """Get active reflection sessions"""
        return [s for s in self.reflection_sessions if s.status == ReflectionStatus.IN_PROGRESS]
    
    def get_completed_reflection_sessions(self) -> List[ReflectionSession]:
        """Get completed reflection sessions"""
        return [s for s in self.reflection_sessions if s.status == ReflectionStatus.COMPLETED]
    
    def get_reflection_insights(self, limit: int = 10) -> List[str]:
        """Get recent reflection insights"""
        try:
            completed_sessions = self.get_completed_reflection_sessions()
            all_insights = []
            
            for session in completed_sessions[-limit:]:
                all_insights.extend(session.insights)
            
            return all_insights[-limit:]
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get reflection insights: {e}")
            return []
    
    def get_improvement_suggestions(self, limit: int = 10) -> List[str]:
        """Get recent improvement suggestions"""
        try:
            completed_sessions = self.get_completed_reflection_sessions()
            all_improvements = []
            
            for session in completed_sessions[-limit:]:
                all_improvements.extend(session.improvements)
            
            return all_improvements[-limit:]
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get improvement suggestions: {e}")
            return []
    
    def get_action_items(self, limit: int = 10) -> List[str]:
        """Get recent action items"""
        try:
            completed_sessions = self.get_completed_reflection_sessions()
            all_action_items = []
            
            for session in completed_sessions[-limit:]:
                all_action_items.extend(session.action_items)
            
            return all_action_items[-limit:]
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get action items: {e}")
            return []
    
    def get_reflection_summary(self) -> Dict[str, Any]:
        """Get reflection summary"""
        try:
            total_sessions = len(self.reflection_sessions)
            completed_sessions = len(self.get_completed_reflection_sessions())
            active_sessions = len(self.get_active_reflection_sessions())
            failed_sessions = len(self.get_reflection_sessions_by_status(ReflectionStatus.FAILED))
            
            sessions_by_type = {}
            sessions_by_status = {}
            
            for session in self.reflection_sessions:
                # By type
                type_key = session.reflection_type.value
                sessions_by_type[type_key] = sessions_by_type.get(type_key, 0) + 1
                
                # By status
                status_key = session.status.value
                sessions_by_status[status_key] = sessions_by_status.get(status_key, 0) + 1
            
            # Calculate average confidence score
            completed_with_confidence = [s for s in self.reflection_sessions 
                                       if s.status == ReflectionStatus.COMPLETED and s.confidence_score is not None]
            avg_confidence = (sum(s.confidence_score for s in completed_with_confidence) / 
                            len(completed_with_confidence)) if completed_with_confidence else 0.0
            
            return {
                "total_sessions": total_sessions,
                "completed_sessions": completed_sessions,
                "active_sessions": active_sessions,
                "failed_sessions": failed_sessions,
                "sessions_by_type": sessions_by_type,
                "sessions_by_status": sessions_by_status,
                "average_confidence": avg_confidence,
                "reflection_config": self.reflection_config,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get reflection summary: {e}")
            return {"error": str(e)}
    
    def enhance_response(self, 
                        response: str, 
                        mode: ReflectionMode = ReflectionMode.STANDARD,
                        timeout: float = None) -> ReflectionResult:
        """Enhance response through reflection"""
        try:
            if timeout is None:
                timeout = self.config.max_latency_s
            
            result_id = f"result_{len(self.reflection_sessions) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            session_id = f"session_{len(self.reflection_sessions) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Simulate reflection process
            start_time = datetime.now()
            
            # Simple enhancement based on mode
            if mode == ReflectionMode.QUICK:
                enhanced_response = f"[Quick Reflection] {response}"
                steps_taken = 1
                confidence_score = 0.6
            elif mode == ReflectionMode.STANDARD:
                enhanced_response = f"[Standard Reflection] {response}"
                steps_taken = 2
                confidence_score = 0.8
            elif mode == ReflectionMode.DEEP:
                enhanced_response = f"[Deep Reflection] {response}"
                steps_taken = 3
                confidence_score = 0.9
            else:  # EMERGENCY
                enhanced_response = f"[Emergency Reflection] {response}"
                steps_taken = 1
                confidence_score = 0.7
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # Create reflection result
            result = ReflectionResult(
                result_id=result_id,
                session_id=session_id,
                enhanced_response=enhanced_response,
                confidence_score=confidence_score,
                processing_time=processing_time,
                steps_taken=steps_taken,
                insights=[f"Enhanced using {mode.value} mode"],
                metadata={
                    "original_response": response,
                    "mode": mode.value,
                    "timeout": timeout
                }
            )
            
            self.logger.info(f"✅ Response enhanced: {mode.value} mode, {processing_time:.3f}s")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Failed to enhance response: {e}")
            raise
    
    def clear_reflection_data(self):
        """Clear all reflection data"""
        self.reflection_sessions.clear()
        self.logger.info("🧹 All reflection data cleared")

# Global reflection controller instance
_reflection_controller_instance = None

def get_default_controller() -> ReflectionController:
    """Get default reflection controller instance"""
    global _reflection_controller_instance
    if _reflection_controller_instance is None:
        _reflection_controller_instance = ReflectionController()
    return _reflection_controller_instance