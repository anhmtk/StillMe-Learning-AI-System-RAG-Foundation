"""Experience Memory for StillMe Framework"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class ExperienceCategory(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    LEARNING = "learning"
    FEEDBACK = "feedback"
    ERROR = "error"
    IMPROVEMENT = "improvement"

class ExperienceType(Enum):
    TASK_COMPLETION = "task_completion"
    ERROR_HANDLING = "error_handling"
    USER_INTERACTION = "user_interaction"
    SYSTEM_OPTIMIZATION = "system_optimization"
    SECURITY_INCIDENT = "security_incident"
    ETHICS_VIOLATION = "ethics_violation"

@dataclass
class ExperienceQuery:
    """Experience query parameters"""
    category: Optional[ExperienceCategory] = None
    experience_type: Optional[ExperienceType] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 10
    metadata_filter: Optional[Dict[str, Any]] = None

@dataclass
class Experience:
    """Experience record"""
    experience_id: str
    category: ExperienceCategory
    experience_type: ExperienceType
    title: str
    description: str
    outcome: str
    lessons_learned: List[str]
    timestamp: datetime
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.lessons_learned is None:
            self.lessons_learned = []

class ExperienceMemory:
    """Experience memory system for StillMe Framework"""
    
    def __init__(self):
        self.logger = logger
        self.experiences: List[Experience] = []
        self.logger.info("✅ ExperienceMemory initialized")
    
    def add_experience(self, 
                      category: ExperienceCategory,
                      experience_type: ExperienceType,
                      title: str,
                      description: str,
                      outcome: str,
                      lessons_learned: List[str] = None,
                      metadata: Dict[str, Any] = None) -> Experience:
        """Add a new experience"""
        try:
            experience_id = f"exp_{len(self.experiences) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            experience = Experience(
                experience_id=experience_id,
                category=category,
                experience_type=experience_type,
                title=title,
                description=description,
                outcome=outcome,
                lessons_learned=lessons_learned or [],
                timestamp=datetime.now(),
                metadata=metadata or {}
            )
            
            self.experiences.append(experience)
            self.logger.info(f"📝 Experience added: {title} ({category.value})")
            return experience
            
        except Exception as e:
            self.logger.error(f"❌ Failed to add experience: {e}")
            raise
    
    def query_experiences(self, query: ExperienceQuery) -> List[Experience]:
        """Query experiences based on criteria"""
        try:
            results = self.experiences
            
            # Filter by category
            if query.category:
                results = [exp for exp in results if exp.category == query.category]
            
            # Filter by experience type
            if query.experience_type:
                results = [exp for exp in results if exp.experience_type == query.experience_type]
            
            # Filter by date range
            if query.start_date:
                results = [exp for exp in results if exp.timestamp >= query.start_date]
            
            if query.end_date:
                results = [exp for exp in results if exp.timestamp <= query.end_date]
            
            # Filter by metadata
            if query.metadata_filter:
                filtered_results = []
                for exp in results:
                    match = True
                    for key, value in query.metadata_filter.items():
                        if exp.metadata.get(key) != value:
                            match = False
                            break
                    if match:
                        filtered_results.append(exp)
                results = filtered_results
            
            # Sort by timestamp (newest first)
            results.sort(key=lambda x: x.timestamp, reverse=True)
            
            # Apply limit
            if query.limit > 0:
                results = results[:query.limit]
            
            self.logger.info(f"🔍 Experience query returned {len(results)} results")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Failed to query experiences: {e}")
            return []
    
    def get_experience_by_id(self, experience_id: str) -> Optional[Experience]:
        """Get experience by ID"""
        try:
            for experience in self.experiences:
                if experience.experience_id == experience_id:
                    return experience
            
            self.logger.warning(f"⚠️ Experience not found: {experience_id}")
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get experience by ID: {e}")
            return None
    
    def get_experience_summary(self) -> Dict[str, Any]:
        """Get experience memory summary"""
        try:
            total_experiences = len(self.experiences)
            
            experiences_by_category = {}
            experiences_by_type = {}
            
            for experience in self.experiences:
                # By category
                category_key = experience.category.value
                experiences_by_category[category_key] = experiences_by_category.get(category_key, 0) + 1
                
                # By type
                type_key = experience.experience_type.value
                experiences_by_type[type_key] = experiences_by_type.get(type_key, 0) + 1
            
            return {
                "total_experiences": total_experiences,
                "experiences_by_category": experiences_by_category,
                "experiences_by_type": experiences_by_type,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get experience summary: {e}")
            return {"error": str(e)}
    
    def clear_experiences(self):
        """Clear all experiences"""
        self.experiences.clear()
        self.logger.info("🧹 All experiences cleared")