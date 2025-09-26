#!/usr/bin/env python3
"""
AgentDev Self-Improvement Loop
Learn from feedback, update knowledge base, pattern recognition
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import hashlib

@dataclass
class FeedbackEntry:
    """Feedback entry"""
    timestamp: str
    user_id: str
    action: str
    feedback_type: str
    feedback_content: str
    context: Dict[str, Any]
    improvement_suggestion: str

@dataclass
class Pattern:
    """Code pattern"""
    pattern_id: str
    pattern_type: str
    frequency: int
    examples: List[str]
    confidence: float
    improvement_potential: float

@dataclass
class KnowledgeEntry:
    """Knowledge base entry"""
    entry_id: str
    category: str
    content: str
    confidence: float
    last_updated: str
    usage_count: int

class SelfImprovementEngine:
    """Self-improvement engine for AgentDev"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.feedback_file = self.project_root / "data" / "feedback.json"
        self.patterns_file = self.project_root / "data" / "patterns.json"
        self.knowledge_file = self.project_root / "data" / "knowledge.json"
        self.learning_file = self.project_root / "data" / "learning.json"
        
        # Ensure data directory exists
        self.project_root / "data" / "mkdir" / "parents" / "exist_ok" = True
        
        self.feedback_history = []
        self.patterns = {}
        self.knowledge_base = {}
        self.learning_stats = {
            "total_feedback": 0,
            "patterns_learned": 0,
            "improvements_made": 0,
            "success_rate": 0.0
        }
    
    async def initialize(self):
        """Initialize self-improvement engine"""
        print("🧠 Initializing Self-Improvement Engine...")
        
        # Load existing data
        await self._load_feedback_history()
        await self._load_patterns()
        await self._load_knowledge_base()
        await self._load_learning_stats()
        
        print("✅ Self-Improvement Engine initialized")
    
    async def _load_feedback_history(self):
        """Load feedback history"""
        if self.feedback_file.exists():
            try:
                with open(self.feedback_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.feedback_history = [FeedbackEntry(**entry) for entry in data]
            except Exception as e:
                print(f"⚠️ Could not load feedback history: {e}")
                self.feedback_history = []
    
    async def _load_patterns(self):
        """Load learned patterns"""
        if self.patterns_file.exists():
            try:
                with open(self.patterns_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.patterns = {k: Pattern(**v) for k, v in data.items()}
            except Exception as e:
                print(f"⚠️ Could not load patterns: {e}")
                self.patterns = {}
    
    async def _load_knowledge_base(self):
        """Load knowledge base"""
        if self.knowledge_file.exists():
            try:
                with open(self.knowledge_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.knowledge_base = {k: KnowledgeEntry(**v) for k, v in data.items()}
            except Exception as e:
                print(f"⚠️ Could not load knowledge base: {e}")
                self.knowledge_base = {}
    
    async def _load_learning_stats(self):
        """Load learning statistics"""
        if self.learning_file.exists():
            try:
                with open(self.learning_file, 'r', encoding='utf-8') as f:
                    self.learning_stats = json.load(f)
            except Exception as e:
                print(f"⚠️ Could not load learning stats: {e}")
    
    async def record_feedback(self, user_id: str, action: str, feedback_type: str, 
                            feedback_content: str, context: Dict[str, Any] = None):
        """Record user feedback"""
        print(f"📝 Recording feedback: {feedback_type}")
        
        feedback = FeedbackEntry(
            timestamp=datetime.now().isoformat(),
            user_id=user_id,
            action=action,
            feedback_type=feedback_type,
            feedback_content=feedback_content,
            context=context or {},
            improvement_suggestion=""
        )
        
        # Analyze feedback for improvement suggestions
        improvement = await self._analyze_feedback(feedback)
        feedback.improvement_suggestion = improvement
        
        # Add to history
        self.feedback_history.append(feedback)
        
        # Update learning stats
        self.learning_stats["total_feedback"] += 1
        
        # Save feedback
        await self._save_feedback_history()
        
        # Learn from feedback
        await self._learn_from_feedback(feedback)
        
        print(f"✅ Feedback recorded and analyzed")
    
    async def _analyze_feedback(self, feedback: FeedbackEntry) -> str:
        """Analyze feedback for improvement suggestions"""
        content = feedback.feedback_content.lower()
        
        # Pattern-based analysis
        if "slow" in content or "performance" in content:
            return "Consider optimizing performance-critical code paths"
        elif "error" in content or "bug" in content:
            return "Review error handling and add more robust validation"
        elif "confusing" in content or "unclear" in content:
            return "Improve code documentation and add more comments"
        elif "security" in content:
            return "Review security practices and add input validation"
        elif "test" in content:
            return "Add more comprehensive test coverage"
        else:
            return "Consider general code quality improvements"
    
    async def _learn_from_feedback(self, feedback: FeedbackEntry):
        """Learn from feedback to improve future performance"""
        print("🎓 Learning from feedback...")
        
        # Extract patterns from feedback
        patterns = await self._extract_patterns_from_feedback(feedback)
        
        # Update knowledge base
        await self._update_knowledge_base(feedback)
        
        # Update patterns
        for pattern in patterns:
            await self._update_pattern(pattern)
        
        # Update learning stats
        self.learning_stats["patterns_learned"] += len(patterns)
        self.learning_stats["improvements_made"] += 1
        
        # Calculate success rate
        positive_feedback = len([f for f in self.feedback_history if f.feedback_type == "positive"])
        total_feedback = len(self.feedback_history)
        if total_feedback > 0:
            self.learning_stats["success_rate"] = positive_feedback / total_feedback
        
        # Save learning stats
        await self._save_learning_stats()
        
        print(f"✅ Learned {len(patterns)} patterns from feedback")
    
    async def _extract_patterns_from_feedback(self, feedback: FeedbackEntry) -> List[Pattern]:
        """Extract patterns from feedback"""
        patterns = []
        
        # Analyze feedback content for patterns
        content = feedback.feedback_content
        
        # Common error patterns
        if "import" in content.lower():
            patterns.append(Pattern(
                pattern_id=f"import_issue_{hashlib.sha256(content.encode()).hexdigest()[:8]}",
                pattern_type="import_error",
                frequency=1,
                examples=[content],
                confidence=0.8,
                improvement_potential=0.7
            ))
        
        if "async" in content.lower():
            patterns.append(Pattern(
                pattern_id=f"async_issue_{hashlib.sha256(content.encode()).hexdigest()[:8]}",
                pattern_type="async_error",
                frequency=1,
                examples=[content],
                confidence=0.9,
                improvement_potential=0.8
            ))
        
        if "test" in content.lower():
            patterns.append(Pattern(
                pattern_id=f"test_issue_{hashlib.sha256(content.encode()).hexdigest()[:8]}",
                pattern_type="test_error",
                frequency=1,
                examples=[content],
                confidence=0.7,
                improvement_potential=0.6
            ))
        
        return patterns
    
    async def _update_knowledge_base(self, feedback: FeedbackEntry):
        """Update knowledge base with feedback"""
        # Create knowledge entry
        entry_id = f"feedback_{hashlib.sha256(feedback.feedback_content.encode()).hexdigest()[:8]}"
        
        knowledge_entry = KnowledgeEntry(
            entry_id=entry_id,
            category=feedback.feedback_type,
            content=feedback.feedback_content,
            confidence=0.8,
            last_updated=datetime.now().isoformat(),
            usage_count=1
        )
        
        # Add or update knowledge base
        if entry_id in self.knowledge_base:
            self.knowledge_base[entry_id].usage_count += 1
            self.knowledge_base[entry_id].last_updated = datetime.now().isoformat()
        else:
            self.knowledge_base[entry_id] = knowledge_entry
        
        # Save knowledge base
        await self._save_knowledge_base()
    
    async def _update_pattern(self, pattern: Pattern):
        """Update pattern database"""
        pattern_id = pattern.pattern_id
        
        if pattern_id in self.patterns:
            # Update existing pattern
            existing = self.patterns[pattern_id]
            existing.frequency += pattern.frequency
            existing.examples.extend(pattern.examples)
            existing.confidence = (existing.confidence + pattern.confidence) / 2
        else:
            # Add new pattern
            self.patterns[pattern_id] = pattern
        
        # Save patterns
        await self._save_patterns()
    
    async def get_improvement_suggestions(self, context: Dict[str, Any]) -> List[str]:
        """Get improvement suggestions based on learned patterns"""
        suggestions = []
        
        # Analyze context for known patterns
        for pattern_id, pattern in self.patterns.items():
            if pattern.confidence > 0.7 and pattern.improvement_potential > 0.6:
                suggestions.append(f"Consider addressing {pattern.pattern_type} pattern: {pattern.examples[0]}")
        
        # Get suggestions from knowledge base
        for entry_id, entry in self.knowledge_base.items():
            if entry.confidence > 0.8 and entry.usage_count > 1:
                suggestions.append(f"Apply learned knowledge: {entry.content}")
        
        return suggestions[:5]  # Return top 5 suggestions
    
    async def _save_feedback_history(self):
        """Save feedback history"""
        data = [asdict(feedback) for feedback in self.feedback_history]
        with open(self.feedback_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    async def _save_patterns(self):
        """Save patterns"""
        data = {k: asdict(v) for k, v in self.patterns.items()}
        with open(self.patterns_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    async def _save_knowledge_base(self):
        """Save knowledge base"""
        data = {k: asdict(v) for k, v in self.knowledge_base.items()}
        with open(self.knowledge_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    async def _save_learning_stats(self):
        """Save learning statistics"""
        with open(self.learning_file, 'w', encoding='utf-8') as f:
            json.dump(self.learning_stats, f, indent=2, ensure_ascii=False)
    
    def get_learning_summary(self) -> Dict[str, Any]:
        """Get learning summary"""
        return {
            "total_feedback": self.learning_stats["total_feedback"],
            "patterns_learned": self.learning_stats["patterns_learned"],
            "improvements_made": self.learning_stats["improvements_made"],
            "success_rate": self.learning_stats["success_rate"],
            "knowledge_entries": len(self.knowledge_base),
            "active_patterns": len(self.patterns)
        }
    
    async def export_learning_report(self, output_path: str):
        """Export learning report"""
        report_data = {
            "learning_summary": self.get_learning_summary(),
            "recent_feedback": [
                {
                    "timestamp": feedback.timestamp,
                    "type": feedback.feedback_type,
                    "content": feedback.feedback_content[:100] + "..." if len(feedback.feedback_content) > 100 else feedback.feedback_content,
                    "improvement": feedback.improvement_suggestion
                }
                for feedback in self.feedback_history[-10:]  # Last 10 feedback entries
            ],
            "top_patterns": [
                {
                    "pattern_type": pattern.pattern_type,
                    "frequency": pattern.frequency,
                    "confidence": pattern.confidence,
                    "improvement_potential": pattern.improvement_potential
                }
                for pattern in sorted(self.patterns.values(), key=lambda x: x.frequency, reverse=True)[:5]
            ]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Learning report exported to {output_path}")

# Example usage
async def main():
    """Example usage of SelfImprovementEngine"""
    engine = SelfImprovementEngine(".")
    await engine.initialize()
    
    # Record some example feedback
    await engine.record_feedback(
        user_id="user1",
        action="code_review",
        feedback_type="negative",
        feedback_content="The async function is not properly awaited, causing runtime errors",
        context={"file": "test_file.py", "line": 42}
    )
    
    await engine.record_feedback(
        user_id="user2",
        action="testing",
        feedback_type="positive",
        feedback_content="Great test coverage and clear documentation",
        context={"file": "test_file.py"}
    )
    
    # Get improvement suggestions
    suggestions = await engine.get_improvement_suggestions({"file": "test_file.py"})
    print(f"Improvement suggestions: {suggestions}")
    
    # Export learning report
    await engine.export_learning_report("reports/learning_report.json")
    
    # Print learning summary
    summary = engine.get_learning_summary()
    print(f"Learning Summary: {summary}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
