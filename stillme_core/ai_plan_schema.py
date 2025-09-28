"""AI Plan Schema for StillMe Framework"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class PlanStep:
    """Single step in an AI plan"""
    id: str
    action: str
    parameters: Dict[str, Any]
    expected_output: Optional[str] = None
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

@dataclass
class PlanItem:
    """Complete AI plan item"""
    id: str
    title: str
    description: str
    steps: List[PlanStep]
    priority: int = 1
    status: str = "pending"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

# Default AI Plan Schema
AI_PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "title": {"type": "string"},
        "description": {"type": "string"},
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "action": {"type": "string"},
                    "parameters": {"type": "object"},
                    "expected_output": {"type": "string"},
                    "dependencies": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["id", "action", "parameters"]
            }
        },
        "priority": {"type": "integer", "minimum": 1, "maximum": 10},
        "status": {"type": "string", "enum": ["pending", "in_progress", "completed", "failed"]},
        "created_at": {"type": "string"},
        "updated_at": {"type": "string"}
    },
    "required": ["id", "title", "description", "steps"]
}
