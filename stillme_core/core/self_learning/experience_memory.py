# stillme_core/self_learning/experience_memory.py
"""
Experience Memory Bank for AgentDev
Stores and learns from all decisions, outcomes, and lessons
"""

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ExperienceType(Enum):
    """Types of experiences"""

    DECISION = "decision"
    ACTION = "action"
    OUTCOME = "outcome"
    FAILURE = "failure"
    SUCCESS = "success"
    LEARNING = "learning"
    PATTERN = "pattern"
    TEST = "test"


class ExperienceCategory(Enum):
    """Categories of experiences"""

    SECURITY = "security"
    PERFORMANCE = "performance"
    QUALITY = "quality"
    USER_EXPERIENCE = "user_experience"
    BUSINESS = "business"
    TECHNICAL = "technical"
    OPERATIONAL = "operational"


@dataclass
class Experience:
    """A single experience record"""

    experience_id: str
    timestamp: float
    experience_type: ExperienceType
    category: ExperienceCategory
    context: dict[str, Any]
    action: str
    outcome: dict[str, Any]
    success: bool
    lessons_learned: list[str]
    tags: list[str]
    confidence: float
    impact_score: float
    related_experiences: list[str] | None = None


@dataclass
class LearningPattern:
    """A learned pattern from experiences"""

    pattern_id: str
    pattern_type: str
    description: str
    conditions: dict[str, Any]
    expected_outcome: dict[str, Any]
    confidence: float
    frequency: int
    success_rate: float
    last_updated: float
    examples: list[str] | None = None


@dataclass
class ExperienceQuery:
    """Query for searching experiences"""

    categories: list[ExperienceCategory] | None = None
    types: list[ExperienceType] | None = None
    tags: list[str] | None = None
    time_range: tuple[float, float] | None = None
    success_only: bool = False
    min_confidence: float = 0.0
    min_impact: float = 0.0
    limit: int = 100


class ExperienceMemory:
    """
    Experience Memory Bank with pattern recognition and learning capabilities
    """

    def __init__(self, db_path: str = ".experience_memory.db"):
        self.db_path = db_path
        self.experiences: list[Experience] = []
        self.patterns: list[LearningPattern] = []
        self.pattern_cache: dict[str, list[LearningPattern]] = {}
        self.learning_stats: dict[str, Any] = {}

        # Initialize database
        self._initialize_database()

        # Load existing data
        self._load_experiences()
        self._load_patterns()

        # Initialize learning stats
        self._initialize_learning_stats()

    def _initialize_database(self):
        """Initialize SQLite database for experience storage"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create experiences table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS experiences (
                    experience_id TEXT PRIMARY KEY,
                    timestamp REAL,
                    experience_type TEXT,
                    category TEXT,
                    context TEXT,
                    action TEXT,
                    outcome TEXT,
                    success INTEGER,
                    lessons_learned TEXT,
                    tags TEXT,
                    confidence REAL,
                    impact_score REAL,
                    related_experiences TEXT
                )
            """
            )

            # Create patterns table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS patterns (
                    pattern_id TEXT PRIMARY KEY,
                    pattern_type TEXT,
                    description TEXT,
                    conditions TEXT,
                    expected_outcome TEXT,
                    confidence REAL,
                    frequency INTEGER,
                    success_rate REAL,
                    last_updated REAL,
                    examples TEXT
                )
            """
            )

            # Create indexes for better performance
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_experiences_timestamp ON experiences(timestamp)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_experiences_category ON experiences(category)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_experiences_type ON experiences(experience_type)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_experiences_success ON experiences(success)"
            )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")

    def _load_experiences(self):
        """Load experiences from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM experiences ORDER BY timestamp DESC LIMIT 10000"
            )
            rows = cursor.fetchall()

            for row in rows:
                experience = Experience(
                    experience_id=row[0],
                    timestamp=row[1],
                    experience_type=ExperienceType(row[2]),
                    category=ExperienceCategory(row[3]),
                    context=json.loads(row[4]),
                    action=row[5],
                    outcome=json.loads(row[6]),
                    success=bool(row[7]),
                    lessons_learned=json.loads(row[8]),
                    tags=json.loads(row[9]),
                    confidence=row[10],
                    impact_score=row[11],
                    related_experiences=json.loads(row[12]) if row[12] else [],
                )
                self.experiences.append(experience)

            conn.close()
            logger.info(f"Loaded {len(self.experiences)} experiences from database")

        except Exception as e:
            logger.error(f"Failed to load experiences: {e}")

    def _load_patterns(self):
        """Load patterns from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM patterns")
            rows = cursor.fetchall()

            for row in rows:
                pattern = LearningPattern(
                    pattern_id=row[0],
                    pattern_type=row[1],
                    description=row[2],
                    conditions=json.loads(row[3]),
                    expected_outcome=json.loads(row[4]),
                    confidence=row[5],
                    frequency=row[6],
                    success_rate=row[7],
                    last_updated=row[8],
                    examples=json.loads(row[9]) if row[9] else [],
                )
                self.patterns.append(pattern)

            conn.close()
            logger.info(f"Loaded {len(self.patterns)} patterns from database")

        except Exception as e:
            logger.error(f"Failed to load patterns: {e}")

    def _initialize_learning_stats(self):
        """Initialize learning statistics"""
        self.learning_stats = {
            "total_experiences": len(self.experiences),
            "success_rate": 0.0,
            "categories": defaultdict(int),
            "types": defaultdict(int),
            "recent_activity": deque(maxlen=100),
            "learning_velocity": 0.0,
            "pattern_accuracy": 0.0,
        }

        if self.experiences:
            # Calculate success rate
            successful = sum(1 for exp in self.experiences if exp.success)
            self.learning_stats["success_rate"] = successful / len(self.experiences)

            # Count by category and type
            for exp in self.experiences:
                self.learning_stats["categories"][exp.category.value] += 1
                self.learning_stats["types"][exp.experience_type.value] += 1

    def store_experience(
        self,
        experience_type: ExperienceType,
        category: ExperienceCategory,
        context: dict[str, Any],
        action: str,
        outcome: dict[str, Any],
        success: bool,
        lessons_learned: list[str],
        tags: list[str],
        confidence: float = 0.5,
        impact_score: float = 0.5,
    ) -> str:
        """
        Store a new experience

        Returns:
            experience_id: Unique identifier for the stored experience
        """
        experience_id = self._generate_experience_id(context, action)
        timestamp = time.time()

        # Find related experiences
        related_experiences = self._find_related_experiences(context, action, tags)

        experience = Experience(
            experience_id=experience_id,
            timestamp=timestamp,
            experience_type=experience_type,
            category=category,
            context=context,
            action=action,
            outcome=outcome,
            success=success,
            lessons_learned=lessons_learned,
            tags=tags,
            confidence=confidence,
            impact_score=impact_score,
            related_experiences=related_experiences,
        )

        # Store in memory
        self.experiences.append(experience)

        # Store in database
        self._save_experience_to_db(experience)

        # Update learning stats
        self._update_learning_stats(experience)

        # Trigger pattern learning
        self._learn_from_experience(experience)

        # Log the experience
        self._log_experience(experience)

        return experience_id

    def _generate_experience_id(self, context: dict[str, Any], action: str) -> str:
        """Generate unique experience ID"""
        data_str = json.dumps(context, sort_keys=True) + action
        hash_str = hashlib.sha256(data_str.encode()).hexdigest()[:16]
        timestamp = int(time.time())
        return f"EXP_{timestamp}_{hash_str}"

    def _find_related_experiences(
        self, context: dict[str, Any], action: str, tags: list[str]
    ) -> list[str]:
        """Find related experiences based on context and tags"""
        related = []

        for exp in self.experiences[-100:]:  # Check recent experiences
            similarity_score = self._calculate_similarity(context, action, tags, exp)
            if similarity_score > 0.7:  # High similarity threshold
                related.append(exp.experience_id)

        return related[:5]  # Limit to 5 related experiences

    def _calculate_similarity(
        self, context1: dict[str, Any], action1: str, tags1: list[str], exp2: Experience
    ) -> float:
        """Calculate similarity between two experiences"""
        similarity = 0.0

        # Context similarity
        context_similarity = self._calculate_context_similarity(context1, exp2.context)
        similarity += context_similarity * 0.4

        # Action similarity
        action_similarity = self._calculate_action_similarity(action1, exp2.action)
        similarity += action_similarity * 0.3

        # Tag similarity
        tag_similarity = self._calculate_tag_similarity(tags1, exp2.tags)
        similarity += tag_similarity * 0.3

        return similarity

    def _calculate_context_similarity(
        self, context1: dict[str, Any], context2: dict[str, Any]
    ) -> float:
        """Calculate similarity between contexts"""
        if not context1 or not context2:
            return 0.0

        # Simple Jaccard similarity for context keys
        keys1 = set(context1.keys())
        keys2 = set(context2.keys())

        if not keys1 and not keys2:
            return 1.0

        intersection = len(keys1.intersection(keys2))
        union = len(keys1.union(keys2))

        return intersection / union if union > 0 else 0.0

    def _calculate_action_similarity(self, action1: str, action2: str) -> float:
        """Calculate similarity between actions"""
        if action1 == action2:
            return 1.0

        # Simple word-based similarity
        words1 = set(action1.lower().split())
        words2 = set(action2.lower().split())

        if not words1 and not words2:
            return 1.0

        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        return intersection / union if union > 0 else 0.0

    def _calculate_tag_similarity(self, tags1: list[str], tags2: list[str]) -> float:
        """Calculate similarity between tag lists"""
        if not tags1 and not tags2:
            return 1.0

        set1 = set(tags1)
        set2 = set(tags2)

        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))

        return intersection / union if union > 0 else 0.0

    def _save_experience_to_db(self, experience: Experience):
        """Save experience to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO experiences VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    experience.experience_id,
                    experience.timestamp,
                    experience.experience_type.value,
                    experience.category.value,
                    json.dumps(experience.context),
                    experience.action,
                    json.dumps(experience.outcome),
                    int(experience.success),
                    json.dumps(experience.lessons_learned),
                    json.dumps(experience.tags),
                    experience.confidence,
                    experience.impact_score,
                    json.dumps(experience.related_experiences),
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to save experience to database: {e}")

    def _update_learning_stats(self, experience: Experience):
        """Update learning statistics"""
        self.learning_stats["total_experiences"] += 1

        # Update success rate
        successful = sum(1 for exp in self.experiences if exp.success)
        self.learning_stats["success_rate"] = successful / len(self.experiences)

        # Update category and type counts
        self.learning_stats["categories"][experience.category.value] += 1
        self.learning_stats["types"][experience.experience_type.value] += 1

        # Add to recent activity
        self.learning_stats["recent_activity"].append(
            {
                "timestamp": experience.timestamp,
                "type": experience.experience_type.value,
                "category": experience.category.value,
                "success": experience.success,
            }
        )

        # Calculate learning velocity (experiences per hour)
        if len(self.learning_stats["recent_activity"]) > 1:
            time_span = (
                self.learning_stats["recent_activity"][-1]["timestamp"]
                - self.learning_stats["recent_activity"][0]["timestamp"]
            )
            if time_span > 0:
                self.learning_stats["learning_velocity"] = len(
                    self.learning_stats["recent_activity"]
                ) / (time_span / 3600)

    def _learn_from_experience(self, experience: Experience):
        """Learn patterns from new experience"""
        # Find similar experiences
        similar_experiences = self._find_similar_experiences(experience)

        if (
            len(similar_experiences) >= 3
        ):  # Need at least 3 similar experiences to form a pattern
            pattern = self._extract_pattern(experience, similar_experiences)
            if pattern:
                self._update_or_create_pattern(pattern)

    def _find_similar_experiences(self, experience: Experience) -> list[Experience]:
        """Find experiences similar to the given one"""
        similar = []

        for exp in self.experiences:
            if exp.experience_id == experience.experience_id:
                continue

            similarity = self._calculate_similarity(
                experience.context, experience.action, experience.tags, exp
            )

            if similarity > 0.6:  # Similarity threshold
                similar.append(exp)

        return similar

    def _extract_pattern(
        self, experience: Experience, similar_experiences: list[Experience]
    ) -> LearningPattern | None:
        """Extract a learning pattern from similar experiences"""
        if not similar_experiences:
            return None

        # Analyze common conditions
        common_conditions = self._find_common_conditions(
            experience, similar_experiences
        )

        # Analyze outcomes
        outcomes = [exp.outcome for exp in similar_experiences + [experience]]
        expected_outcome = self._analyze_outcomes(outcomes)

        # Calculate success rate
        all_experiences = similar_experiences + [experience]
        successful = sum(1 for exp in all_experiences if exp.success)
        success_rate = successful / len(all_experiences)

        # Only create pattern if success rate is meaningful
        if success_rate < 0.3 or success_rate > 0.7:
            pattern_id = self._generate_pattern_id(common_conditions)

            pattern = LearningPattern(
                pattern_id=pattern_id,
                pattern_type="behavioral",
                description=f"Pattern for {experience.category.value} actions",
                conditions=common_conditions,
                expected_outcome=expected_outcome,
                confidence=success_rate,
                frequency=len(all_experiences),
                success_rate=success_rate,
                last_updated=time.time(),
                examples=[exp.experience_id for exp in all_experiences[:5]],
            )

            return pattern

        return None

    def _find_common_conditions(
        self, experience: Experience, similar_experiences: list[Experience]
    ) -> dict[str, Any]:
        """Find common conditions across similar experiences"""
        all_contexts = [exp.context for exp in similar_experiences + [experience]]

        # Find common keys
        all_keys = set()
        for context in all_contexts:
            all_keys.update(context.keys())

        common_conditions = {}
        for key in all_keys:
            values = [context.get(key) for context in all_contexts if key in context]
            if (
                len(values) >= len(all_contexts) * 0.7
            ):  # 70% of experiences have this key
                # Find most common value
                value_counts = defaultdict(int)
                for value in values:
                    value_counts[str(value)] += 1

                most_common_value = (
                    max(value_counts.items(), key=lambda x: x[1])[0]
                    if value_counts
                    else ""
                )
                common_conditions[key] = most_common_value

        return common_conditions

    def _analyze_outcomes(self, outcomes: list[dict[str, Any]]) -> dict[str, Any]:
        """Analyze outcomes to find common patterns"""
        if not outcomes:
            return {}

        # Find common outcome keys
        all_keys = set()
        for outcome in outcomes:
            all_keys.update(outcome.keys())

        expected_outcome = {}
        for key in all_keys:
            values = [outcome.get(key) for outcome in outcomes if key in outcome]
            if values:
                # Use most common value or average for numeric values
                non_none_values = [v for v in values if v is not None]
                if non_none_values:
                    if all(isinstance(v, (int, float)) for v in non_none_values):
                        expected_outcome[key] = sum(non_none_values) / len(
                            non_none_values
                        )
                    else:
                        value_counts = defaultdict(int)
                        for value in non_none_values:
                            value_counts[str(value)] += 1
                        expected_outcome[key] = (
                            max(value_counts.items(), key=lambda x: x[1])[0]
                            if value_counts
                            else ""
                        )

        return expected_outcome

    def _generate_pattern_id(self, conditions: dict[str, Any]) -> str:
        """Generate unique pattern ID"""
        conditions_str = json.dumps(conditions, sort_keys=True)
        hash_str = hashlib.sha256(conditions_str.encode()).hexdigest()[:16]
        timestamp = int(time.time())
        return f"PAT_{timestamp}_{hash_str}"

    def _update_or_create_pattern(self, new_pattern: LearningPattern):
        """Update existing pattern or create new one"""
        # Check if similar pattern exists
        for i, existing_pattern in enumerate(self.patterns):
            if self._patterns_similar(new_pattern, existing_pattern):
                # Update existing pattern
                self.patterns[i] = self._merge_patterns(existing_pattern, new_pattern)
                self._save_pattern_to_db(self.patterns[i])
                return

        # Create new pattern
        self.patterns.append(new_pattern)
        self._save_pattern_to_db(new_pattern)

    def _patterns_similar(
        self, pattern1: LearningPattern, pattern2: LearningPattern
    ) -> bool:
        """Check if two patterns are similar"""
        # Compare conditions
        conditions_similarity = self._calculate_context_similarity(
            pattern1.conditions, pattern2.conditions
        )

        return conditions_similarity > 0.8

    def _merge_patterns(
        self, existing: LearningPattern, new: LearningPattern
    ) -> LearningPattern:
        """Merge two similar patterns"""
        # Combine examples
        all_examples = existing.examples + new.examples  # type: ignore
        unique_examples = list(set(all_examples))

        # Update frequency and success rate
        total_frequency = existing.frequency + new.frequency
        total_success = (
            existing.success_rate * existing.frequency
            + new.success_rate * new.frequency
        )
        new_success_rate = (
            total_success / total_frequency if total_frequency > 0 else 0.0
        )

        # Update confidence based on combined data
        new_confidence = (existing.confidence + new.confidence) / 2

        return LearningPattern(
            pattern_id=existing.pattern_id,
            pattern_type=existing.pattern_type,
            description=existing.description,
            conditions=existing.conditions,  # Keep existing conditions
            expected_outcome=existing.expected_outcome,  # Keep existing outcome
            confidence=new_confidence,
            frequency=total_frequency,
            success_rate=new_success_rate,
            last_updated=time.time(),
            examples=unique_examples[:10],  # Limit examples
        )

    def _save_pattern_to_db(self, pattern: LearningPattern):
        """Save pattern to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO patterns VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    pattern.pattern_id,
                    pattern.pattern_type,
                    pattern.description,
                    json.dumps(pattern.conditions),
                    json.dumps(pattern.expected_outcome),
                    pattern.confidence,
                    pattern.frequency,
                    pattern.success_rate,
                    pattern.last_updated,
                    json.dumps(pattern.examples),
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to save pattern to database: {e}")

    def _log_experience(self, experience: Experience):
        """Log experience for debugging"""
        log_data = {
            "experience_id": experience.experience_id,
            "type": experience.experience_type.value,
            "category": experience.category.value,
            "success": experience.success,
            "confidence": experience.confidence,
            "impact_score": experience.impact_score,
            "lessons_count": len(experience.lessons_learned),
        }

        logger.info(f"Experience stored: {log_data}")

    def query_experiences(self, query: ExperienceQuery) -> list[Experience]:
        """Query experiences based on criteria"""
        results = []

        for experience in self.experiences:
            # Apply filters
            if query.categories and experience.category not in query.categories:
                continue

            if query.types and experience.experience_type not in query.types:
                continue

            if query.tags and not any(tag in experience.tags for tag in query.tags):
                continue

            if query.time_range:
                if not (
                    query.time_range[0] <= experience.timestamp <= query.time_range[1]
                ):
                    continue

            if query.success_only and not experience.success:
                continue

            if experience.confidence < query.min_confidence:
                continue

            if experience.impact_score < query.min_impact:
                continue

            results.append(experience)

            if len(results) >= query.limit:
                break

        return results

    def get_recommendations(
        self, context: dict[str, Any], action: str, tags: list[str]
    ) -> list[dict[str, Any]]:
        """Get recommendations based on similar experiences"""
        recommendations = []

        # Find similar experiences
        similar_experiences = []
        for exp in self.experiences:
            similarity = self._calculate_similarity(context, action, tags, exp)
            if similarity > 0.6:
                similar_experiences.append((exp, similarity))

        # Sort by similarity
        similar_experiences.sort(key=lambda x: x[1], reverse=True)

        # Generate recommendations
        for exp, similarity in similar_experiences[:5]:
            if exp.success:
                recommendation = {
                    "type": "success_pattern",
                    "description": f"Similar successful action: {exp.action}",
                    "confidence": similarity * exp.confidence,
                    "lessons": exp.lessons_learned,
                    "context": exp.context,
                    "outcome": exp.outcome,
                }
                recommendations.append(recommendation)
            else:
                recommendation = {
                    "type": "failure_warning",
                    "description": f"Similar failed action: {exp.action}",
                    "confidence": similarity * exp.confidence,
                    "lessons": exp.lessons_learned,
                    "context": exp.context,
                    "outcome": exp.outcome,
                }
                recommendations.append(recommendation)

        # Add pattern-based recommendations
        for pattern in self.patterns:
            if self._pattern_matches_context(pattern, context):
                recommendation = {
                    "type": "pattern_based",
                    "description": f"Pattern: {pattern.description}",
                    "confidence": pattern.confidence,
                    "expected_outcome": pattern.expected_outcome,
                    "success_rate": pattern.success_rate,
                    "frequency": pattern.frequency,
                }
                recommendations.append(recommendation)

        return recommendations

    def _pattern_matches_context(
        self, pattern: LearningPattern, context: dict[str, Any]
    ) -> bool:
        """Check if a pattern matches the given context"""
        for key, expected_value in pattern.conditions.items():
            if key not in context:
                return False

            actual_value = context[key]
            if str(actual_value) != str(expected_value):
                return False

        return True

    def get_learning_stats(self) -> dict[str, Any]:
        """Get comprehensive learning statistics"""
        stats = dict(self.learning_stats)

        # Add pattern statistics
        stats["total_patterns"] = len(self.patterns)
        stats["pattern_accuracy"] = (
            sum(p.success_rate for p in self.patterns) / len(self.patterns)
            if self.patterns
            else 0.0
        )

        # Add recent trends
        recent_experiences = [
            exp for exp in self.experiences if time.time() - exp.timestamp < 86400
        ]  # Last 24 hours
        stats["recent_experiences"] = len(recent_experiences)

        if recent_experiences:
            recent_success_rate = sum(
                1 for exp in recent_experiences if exp.success
            ) / len(recent_experiences)
            stats["recent_success_rate"] = recent_success_rate

        return stats

    def export_experiences(self, file_path: str):
        """Export experiences to JSON file"""
        try:
            export_data = {
                "experiences": [asdict(exp) for exp in self.experiences],
                "patterns": [asdict(pattern) for pattern in self.patterns],
                "stats": self.get_learning_stats(),
                "export_timestamp": time.time(),
            }

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, default=str)

            logger.info(f"Exported {len(self.experiences)} experiences to {file_path}")

        except Exception as e:
            logger.error(f"Failed to export experiences: {e}")

    def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old experiences and patterns"""
        cutoff_time = time.time() - (days_to_keep * 86400)

        # Remove old experiences
        old_count = len(self.experiences)
        self.experiences = [
            exp for exp in self.experiences if exp.timestamp > cutoff_time
        ]
        removed_count = old_count - len(self.experiences)

        # Remove old patterns with low frequency
        old_pattern_count = len(self.patterns)
        self.patterns = [
            p for p in self.patterns if p.frequency > 2 or p.last_updated > cutoff_time
        ]
        removed_pattern_count = old_pattern_count - len(self.patterns)

        logger.info(
            f"Cleaned up {removed_count} old experiences and {removed_pattern_count} old patterns"
        )

        # Update database
        self._cleanup_database(cutoff_time)

    def _cleanup_database(self, cutoff_time: float):
        """Clean up old data from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Remove old experiences
            cursor.execute(
                "DELETE FROM experiences WHERE timestamp < ?", (cutoff_time,)
            )

            # Remove low-frequency patterns
            cursor.execute(
                "DELETE FROM patterns WHERE frequency <= 2 AND last_updated < ?",
                (cutoff_time,),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to cleanup database: {e}")
