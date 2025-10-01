#!/usr/bin/env python3
"""
Experience Learner - Senior Developer Experience Learning Module
Học hỏi từ kinh nghiệm như dev chuyên nghiệp thật

Tính năng:
1. Pattern Recognition - Nhận diện patterns từ kinh nghiệm
2. Success/Failure Analysis - Phân tích thành công/thất bại
3. Knowledge Accumulation - Tích lũy kiến thức
4. Strategy Evolution - Tiến hóa chiến lược
5. Error Pattern Learning - Học từ lỗi
6. Performance Optimization - Tối ưu hiệu suất
7. Best Practice Learning - Học best practices
8. Contextual Learning - Học theo ngữ cảnh
"""

import os
import json
import time
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from datetime import datetime, timedelta

class LearningType(Enum):
    """Loại học hỏi"""
    SUCCESS_PATTERN = "success_pattern"
    FAILURE_PATTERN = "failure_pattern"
    ERROR_PATTERN = "error_pattern"
    PERFORMANCE_PATTERN = "performance_pattern"
    SECURITY_PATTERN = "security_pattern"
    BUSINESS_PATTERN = "business_pattern"
    CODE_PATTERN = "code_pattern"
    ARCHITECTURE_PATTERN = "architecture_pattern"

class LearningConfidence(Enum):
    """Mức độ tin cậy của học hỏi"""
    HIGH = "high"           # Cao
    MEDIUM = "medium"       # Trung bình
    LOW = "low"             # Thấp
    EXPERIMENTAL = "experimental"  # Thử nghiệm

@dataclass
class Experience:
    """Kinh nghiệm"""
    experience_id: str
    learning_type: LearningType
    context: str
    action: str
    result: str
    success: bool
    performance_metrics: Dict[str, float]
    lessons_learned: List[str]
    confidence: LearningConfidence
    timestamp: datetime
    frequency: int = 1
    last_used: Optional[datetime] = None

@dataclass
class LearningPattern:
    """Pattern học hỏi"""
    pattern_id: str
    pattern_type: LearningType
    description: str
    conditions: List[str]
    actions: List[str]
    expected_outcomes: List[str]
    success_rate: float
    confidence: LearningConfidence
    examples: List[str]
    created_at: datetime
    last_updated: datetime
    usage_count: int = 0

@dataclass
class LearningInsight:
    """Insight từ học hỏi"""
    insight_id: str
    title: str
    description: str
    learning_type: LearningType
    confidence: LearningConfidence
    evidence: List[str]
    recommendations: List[str]
    impact_score: float
    created_at: datetime

@dataclass
class ExperienceLearningResult:
    """Kết quả học hỏi kinh nghiệm"""
    total_experiences: int
    learning_patterns: List[LearningPattern]
    insights: List[LearningInsight]
    success_patterns: List[LearningPattern]
    failure_patterns: List[LearningPattern]
    recommendations: List[str]
    learning_score: float
    analysis_time: float

class ExperienceLearner:
    """Senior Developer Experience Learner"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.experience_db = self.project_root / "data" / "experience_learning.json"
        self.patterns_db = self.project_root / "data" / "learning_patterns.json"
        self.insights_db = self.project_root / "data" / "learning_insights.json"

        # Ensure data directory exists
        self.experience_db.parent.mkdir(parents=True, exist_ok=True)

        # Load existing data
        self.experiences = self._load_experiences()
        self.patterns = self._load_patterns()
        self.insights = self._load_insights()

        # Learning configuration
        self.min_confidence_threshold = 0.6
        self.pattern_min_frequency = 3
        self.insight_min_evidence = 2

    def _load_experiences(self) -> List[Experience]:
        """Load experiences from database"""
        if not self.experience_db.exists():
            return []

        try:
            with open(self.experience_db, 'r', encoding='utf-8') as f:
                data = json.load(f)

            experiences = []
            for exp_data in data:
                exp_data['timestamp'] = datetime.fromisoformat(exp_data['timestamp'])
                if exp_data.get('last_used'):
                    exp_data['last_used'] = datetime.fromisoformat(exp_data['last_used'])
                experiences.append(Experience(**exp_data))

            return experiences
        except Exception as e:
            print(f"Error loading experiences: {e}")
            return []

    def _load_patterns(self) -> List[LearningPattern]:
        """Load learning patterns from database"""
        if not self.patterns_db.exists():
            return []

        try:
            with open(self.patterns_db, 'r', encoding='utf-8') as f:
                data = json.load(f)

            patterns = []
            for pattern_data in data:
                pattern_data['created_at'] = datetime.fromisoformat(pattern_data['created_at'])
                pattern_data['last_updated'] = datetime.fromisoformat(pattern_data['last_updated'])
                patterns.append(LearningPattern(**pattern_data))

            return patterns
        except Exception as e:
            print(f"Error loading patterns: {e}")
            return []

    def _load_insights(self) -> List[LearningInsight]:
        """Load learning insights from database"""
        if not self.insights_db.exists():
            return []

        try:
            with open(self.insights_db, 'r', encoding='utf-8') as f:
                data = json.load(f)

            insights = []
            for insight_data in data:
                insight_data['created_at'] = datetime.fromisoformat(insight_data['created_at'])
                insights.append(LearningInsight(**insight_data))

            return insights
        except Exception as e:
            print(f"Error loading insights: {e}")
            return []

    def _save_experiences(self):
        """Save experiences to database"""
        try:
            data = []
            for exp in self.experiences:
                exp_dict = asdict(exp)
                exp_dict['timestamp'] = exp.timestamp.isoformat()
                if exp.last_used:
                    exp_dict['last_used'] = exp.last_used.isoformat()
                data.append(exp_dict)

            with open(self.experience_db, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving experiences: {e}")

    def _save_patterns(self):
        """Save patterns to database"""
        try:
            data = []
            for pattern in self.patterns:
                pattern_dict = asdict(pattern)
                pattern_dict['created_at'] = pattern.created_at.isoformat()
                pattern_dict['last_updated'] = pattern.last_updated.isoformat()
                data.append(pattern_dict)

            with open(self.patterns_db, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving patterns: {e}")

    def _save_insights(self):
        """Save insights to database"""
        try:
            data = []
            for insight in self.insights:
                insight_dict = asdict(insight)
                insight_dict['created_at'] = insight.created_at.isoformat()
                data.append(insight_dict)

            with open(self.insights_db, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving insights: {e}")

    def record_experience(self, context: str, action: str, result: str,
                         success: bool, performance_metrics: Dict[str, float] = None,
                         learning_type: LearningType = LearningType.SUCCESS_PATTERN) -> str:
        """Record a new experience"""
        if performance_metrics is None:
            performance_metrics = {}

        # Generate experience ID
        experience_id = hashlib.md5(f"{context}_{action}_{result}".encode()).hexdigest()[:12]

        # Check if similar experience exists
        existing_exp = None
        for exp in self.experiences:
            if (exp.context == context and exp.action == action and
                exp.result == result and exp.success == success):
                existing_exp = exp
                break

        if existing_exp:
            # Update existing experience
            existing_exp.frequency += 1
            existing_exp.last_used = datetime.now()
            existing_exp.performance_metrics.update(performance_metrics)
            experience_id = existing_exp.experience_id
        else:
            # Create new experience
            experience = Experience(
                experience_id=experience_id,
                learning_type=learning_type,
                context=context,
                action=action,
                result=result,
                success=success,
                performance_metrics=performance_metrics,
                lessons_learned=[],
                confidence=LearningConfidence.MEDIUM,
                timestamp=datetime.now(),
                frequency=1,
                last_used=datetime.now()
            )
            self.experiences.append(experience)

        # Save to database
        self._save_experiences()

        return experience_id

    def analyze_patterns(self) -> List[LearningPattern]:
        """Analyze experiences to identify patterns"""
        patterns = []

        # Group experiences by type and context
        experience_groups = {}
        for exp in self.experiences:
            key = f"{exp.learning_type.value}_{exp.context}"
            if key not in experience_groups:
                experience_groups[key] = []
            experience_groups[key].append(exp)

        # Identify patterns
        for key, exps in experience_groups.items():
            if len(exps) < self.pattern_min_frequency:
                continue

            # Calculate success rate
            success_count = sum(1 for exp in exps if exp.success)
            success_rate = success_count / len(exps)

            # Determine confidence
            if len(exps) >= 10 and success_rate > 0.8:
                confidence = LearningConfidence.HIGH
            elif len(exps) >= 5 and success_rate > 0.6:
                confidence = LearningConfidence.MEDIUM
            else:
                confidence = LearningConfidence.LOW

            # Create pattern
            pattern_id = hashlib.md5(key.encode()).hexdigest()[:12]
            pattern = LearningPattern(
                pattern_id=pattern_id,
                pattern_type=exps[0].learning_type,
                description=f"Pattern for {exps[0].context}",
                conditions=[exp.context for exp in exps[:3]],
                actions=[exp.action for exp in exps[:3]],
                expected_outcomes=[exp.result for exp in exps[:3]],
                success_rate=success_rate,
                confidence=confidence,
                examples=[f"{exp.action} -> {exp.result}" for exp in exps[:5]],
                created_at=datetime.now(),
                last_updated=datetime.now(),
                usage_count=len(exps)
            )
            patterns.append(pattern)

        return patterns

    def generate_insights(self) -> List[LearningInsight]:
        """Generate insights from experiences and patterns"""
        insights = []

        # Analyze success patterns
        success_experiences = [exp for exp in self.experiences if exp.success]
        if len(success_experiences) >= self.insight_min_evidence:
            insight = LearningInsight(
                insight_id=hashlib.md5("success_insight".encode()).hexdigest()[:12],
                title="Success Pattern Analysis",
                description=f"Analyzed {len(success_experiences)} successful experiences",
                learning_type=LearningType.SUCCESS_PATTERN,
                confidence=LearningConfidence.HIGH,
                evidence=[f"Success rate: {len(success_experiences)/len(self.experiences)*100:.1f}%"],
                recommendations=[
                    "Continue using successful patterns",
                    "Document best practices",
                    "Share knowledge with team"
                ],
                impact_score=0.8,
                created_at=datetime.now()
            )
            insights.append(insight)

        # Analyze failure patterns
        failure_experiences = [exp for exp in self.experiences if not exp.success]
        if len(failure_experiences) >= self.insight_min_evidence:
            insight = LearningInsight(
                insight_id=hashlib.md5("failure_insight".encode()).hexdigest()[:12],
                title="Failure Pattern Analysis",
                description=f"Analyzed {len(failure_experiences)} failed experiences",
                learning_type=LearningType.FAILURE_PATTERN,
                confidence=LearningConfidence.HIGH,
                evidence=[f"Failure rate: {len(failure_experiences)/len(self.experiences)*100:.1f}%"],
                recommendations=[
                    "Avoid repeating failed patterns",
                    "Investigate root causes",
                    "Implement preventive measures"
                ],
                impact_score=0.7,
                created_at=datetime.now()
            )
            insights.append(insight)

        return insights

    def learn_from_experience(self) -> ExperienceLearningResult:
        """Main learning function - learn from all experiences"""
        start_time = time.time()

        # Analyze patterns
        patterns = self.analyze_patterns()

        # Generate insights
        insights = self.generate_insights()

        # Categorize patterns
        success_patterns = [p for p in patterns if p.success_rate > 0.7]
        failure_patterns = [p for p in patterns if p.success_rate < 0.3]

        # Generate recommendations
        recommendations = []
        if success_patterns:
            recommendations.append(f"Continue using {len(success_patterns)} successful patterns")
        if failure_patterns:
            recommendations.append(f"Avoid {len(failure_patterns)} failure patterns")
        if insights:
            recommendations.append(f"Apply {len(insights)} key insights")

        # Calculate learning score
        learning_score = min(1.0, len(patterns) * 0.1 + len(insights) * 0.2)

        # Update patterns database
        self.patterns = patterns
        self.insights = insights
        self._save_patterns()
        self._save_insights()

        return ExperienceLearningResult(
            total_experiences=len(self.experiences),
            learning_patterns=patterns,
            insights=insights,
            success_patterns=success_patterns,
            failure_patterns=failure_patterns,
            recommendations=recommendations,
            learning_score=learning_score,
            analysis_time=time.time() - start_time
        )

    def get_recommendations(self, context: str) -> List[str]:
        """Get recommendations based on learned patterns"""
        recommendations = []

        # Find relevant patterns
        relevant_patterns = []
        for pattern in self.patterns:
            if any(context.lower() in condition.lower() for condition in pattern.conditions):
                relevant_patterns.append(pattern)

        # Generate recommendations
        for pattern in relevant_patterns:
            if pattern.success_rate > 0.7:
                recommendations.append(f"✅ Use pattern: {pattern.description}")
            elif pattern.success_rate < 0.3:
                recommendations.append(f"❌ Avoid pattern: {pattern.description}")

        return recommendations

# Test function
if __name__ == "__main__":
    learner = ExperienceLearner()

    # Record some sample experiences
    learner.record_experience(
        context="Code conflict resolution",
        action="Used auto-resolve strategy",
        result="Successfully resolved 2/3 conflicts",
        success=True,
        performance_metrics={"time_taken": 30, "success_rate": 0.67}
    )

    learner.record_experience(
        context="Security analysis",
        action="Implemented security recommendations",
        result="Security score improved to 0.85",
        success=True,
        performance_metrics={"security_score": 0.85, "time_taken": 45}
    )

    # Learn from experiences
    result = learner.learn_from_experience()

    print(f"📚 Experience Learning Results:")
    print(f"   📊 Total Experiences: {result.total_experiences}")
    print(f"   🎯 Learning Patterns: {len(result.learning_patterns)}")
    print(f"   💡 Insights: {len(result.insights)}")
    print(f"   ✅ Success Patterns: {len(result.success_patterns)}")
    print(f"   ❌ Failure Patterns: {len(result.failure_patterns)}")
    print(f"   📈 Learning Score: {result.learning_score:.2f}")
    print(f"   ⏱️ Analysis Time: {result.analysis_time:.3f}s")
    print(f"   💡 Recommendations: {len(result.recommendations)}")
