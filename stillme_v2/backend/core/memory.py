"""
Experience Memory System for StillMe V2
Lightweight version focusing on core learning functionality
"""

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import time
from collections import defaultdict
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ExperienceType(Enum):
    """Types of learning experiences"""

    LEARNING = "learning"
    SUCCESS = "success"
    FAILURE = "failure"
    PATTERN = "pattern"
    REASONING_STRATEGY = "reasoning_strategy"  # From ReasoningBank
    PITFALL_AVOIDANCE = "pitfall_avoidance"    # From ReasoningBank


class ExperienceCategory(Enum):
    """Learning categories"""

    RSS_CONTENT = "rss_content"
    USER_FEEDBACK = "user_feedback"
    SELF_ASSESSMENT = "self_assessment"
    KNOWLEDGE_ACQUISITION = "knowledge_acquisition"
    API_INTEGRATION = "api_integration"        # From Public APIs
    CONTENT_PROCESSING = "content_processing"  # From Public APIs
    FAILURE_ANALYSIS = "failure_analysis"      # From ReasoningBank


@dataclass
class Experience:
    """A single learning experience record"""

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


class ExperienceMemory:
    """
    Experience Memory Bank for StillMe V2
    Stores and learns from all learning experiences
    """

    def __init__(self, db_path: str = "data/experience_memory.db"):
        self.db_path = db_path
        self.experiences: list[Experience] = []
        self.patterns: list[LearningPattern] = []
        self.learning_stats: dict[str, Any] = {}

        self._initialize_database()
        self._load_experiences()
        self._load_patterns()
        self._initialize_learning_stats()

    def _initialize_database(self):
        """Initialize SQLite database for experience storage"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

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
                    impact_score REAL
                )
            """
            )

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
                    last_updated REAL
                )
            """
            )

            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_experiences_timestamp ON experiences(timestamp)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_experiences_category ON experiences(category)"
            )

            conn.commit()
            conn.close()
            logger.info("✅ Experience memory database initialized")

        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            raise

    def _load_experiences(self):
        """Load recent experiences from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM experiences ORDER BY timestamp DESC LIMIT 1000"
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
                )
                self.experiences.append(experience)

            conn.close()
            logger.info(f"📚 Loaded {len(self.experiences)} experiences")

        except Exception as e:
            logger.warning(f"⚠️ Failed to load experiences: {e}")

    def _load_patterns(self):
        """Load learning patterns from database"""
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
                )
                self.patterns.append(pattern)

            conn.close()
            logger.info(f"🧩 Loaded {len(self.patterns)} patterns")

        except Exception as e:
            logger.warning(f"⚠️ Failed to load patterns: {e}")

    def _initialize_learning_stats(self):
        """Initialize learning statistics"""
        self.learning_stats = {
            "total_experiences": len(self.experiences),
            "success_rate": 0.0,
            "categories": defaultdict(int),
            "types": defaultdict(int),
        }

        if self.experiences:
            successful = sum(1 for exp in self.experiences if exp.success)
            self.learning_stats["success_rate"] = successful / len(self.experiences)

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
        Store a new learning experience

        Returns:
            experience_id: Unique identifier for the stored experience
        """
        experience_id = self._generate_experience_id(context, action)
        timestamp = time.time()

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
        )

        self.experiences.append(experience)
        self._save_experience_to_db(experience)
        self._update_learning_stats(experience)
        self._learn_from_experience(experience)

        logger.info(f"📝 Experience stored: {action} (success={success})")
        
        # Learn from failure if this is a failure experience
        if not success and experience_type == ExperienceType.FAILURE:
            self._learn_from_failure(experience)
            
        return experience_id

    def _generate_experience_id(self, context: dict[str, Any], action: str) -> str:
        """Generate unique experience ID"""
        data_str = json.dumps(context, sort_keys=True) + action
        hash_str = hashlib.sha256(data_str.encode()).hexdigest()[:16]
        timestamp = int(time.time())
        return f"EXP_{timestamp}_{hash_str}"

    def _save_experience_to_db(self, experience: Experience):
        """Save experience to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO experiences VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"❌ Failed to save experience: {e}")

    def _update_learning_stats(self, experience: Experience):
        """Update learning statistics"""
        self.learning_stats["total_experiences"] += 1

        successful = sum(1 for exp in self.experiences if exp.success)
        self.learning_stats["success_rate"] = successful / len(self.experiences)

        self.learning_stats["categories"][experience.category.value] += 1
        self.learning_stats["types"][experience.experience_type.value] += 1

    def _learn_from_experience(self, experience: Experience):
        """Learn patterns from new experience"""
        similar_experiences = self._find_similar_experiences(experience)

        if len(similar_experiences) >= 3:
            pattern = self._extract_pattern(experience, similar_experiences)
            if pattern:
                self._update_or_create_pattern(pattern)

    def _find_similar_experiences(self, experience: Experience) -> list[Experience]:
        """Find experiences similar to the given one"""
        similar = []

        for exp in self.experiences:
            if exp.experience_id == experience.experience_id:
                continue

            if exp.category == experience.category:
                tag_overlap = len(set(exp.tags) & set(experience.tags))
                if tag_overlap >= 2:
                    similar.append(exp)

        return similar

    def _extract_pattern(
        self, experience: Experience, similar_experiences: list[Experience]
    ) -> LearningPattern | None:
        """Extract a learning pattern from similar experiences"""
        all_experiences = similar_experiences + [experience]
        successful = sum(1 for exp in all_experiences if exp.success)
        success_rate = successful / len(all_experiences)

        if success_rate < 0.3 or success_rate > 0.7:
            pattern_id = self._generate_pattern_id(experience.category.value)
            common_tags = set.intersection(*[set(exp.tags) for exp in all_experiences])

            pattern = LearningPattern(
                pattern_id=pattern_id,
                pattern_type="learning",
                description=f"Pattern for {experience.category.value}",
                conditions={"category": experience.category.value, "tags": list(common_tags)},
                expected_outcome={"success_rate": success_rate},
                confidence=success_rate,
                frequency=len(all_experiences),
                success_rate=success_rate,
                last_updated=time.time(),
            )

            return pattern

        return None

    def _generate_pattern_id(self, category: str) -> str:
        """Generate unique pattern ID"""
        hash_str = hashlib.sha256(category.encode()).hexdigest()[:16]
        timestamp = int(time.time())
        return f"PAT_{timestamp}_{hash_str}"

    def _update_or_create_pattern(self, new_pattern: LearningPattern):
        """Update existing pattern or create new one"""
        for i, existing_pattern in enumerate(self.patterns):
            if existing_pattern.pattern_type == new_pattern.pattern_type:
                self.patterns[i] = self._merge_patterns(existing_pattern, new_pattern)
                self._save_pattern_to_db(self.patterns[i])
                return

        self.patterns.append(new_pattern)
        self._save_pattern_to_db(new_pattern)

    def _merge_patterns(
        self, existing: LearningPattern, new: LearningPattern
    ) -> LearningPattern:
        """Merge two similar patterns"""
        total_frequency = existing.frequency + new.frequency
        total_success = (
            existing.success_rate * existing.frequency + new.success_rate * new.frequency
        )
        new_success_rate = total_success / total_frequency if total_frequency > 0 else 0.0
        new_confidence = (existing.confidence + new.confidence) / 2

        return LearningPattern(
            pattern_id=existing.pattern_id,
            pattern_type=existing.pattern_type,
            description=existing.description,
            conditions=existing.conditions,
            expected_outcome=existing.expected_outcome,
            confidence=new_confidence,
            frequency=total_frequency,
            success_rate=new_success_rate,
            last_updated=time.time(),
        )

    def _save_pattern_to_db(self, pattern: LearningPattern):
        """Save pattern to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO patterns VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"❌ Failed to save pattern: {e}")

    def get_learning_stats(self) -> dict[str, Any]:
        """Get comprehensive learning statistics"""
        stats = dict(self.learning_stats)

        stats["total_patterns"] = len(self.patterns)
        stats["pattern_accuracy"] = (
            sum(p.success_rate for p in self.patterns) / len(self.patterns)
            if self.patterns
            else 0.0
        )

        recent_experiences = [
            exp for exp in self.experiences if time.time() - exp.timestamp < 86400
        ]
        stats["recent_experiences"] = len(recent_experiences)

        if recent_experiences:
            recent_success_rate = sum(
                1 for exp in recent_experiences if exp.success
            ) / len(recent_experiences)
            stats["recent_success_rate"] = recent_success_rate

        return stats

    def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old experiences and patterns"""
        cutoff_time = time.time() - (days_to_keep * 86400)

        old_count = len(self.experiences)
        self.experiences = [
            exp for exp in self.experiences if exp.timestamp > cutoff_time
        ]
        removed_count = old_count - len(self.experiences)

        logger.info(f"🧹 Cleaned up {removed_count} old experiences")

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "DELETE FROM experiences WHERE timestamp < ?", (cutoff_time,)
            )
            cursor.execute(
                "DELETE FROM patterns WHERE frequency <= 2 AND last_updated < ?",
                (cutoff_time,),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"❌ Failed to cleanup database: {e}")

    def _learn_from_failure(self, failure_experience: Experience):
        """
        Learn from failure experience - inspired by ReasoningBank
        Extract lessons and create pitfall avoidance strategies
        """
        try:
            # Extract failure analysis
            failure_context = failure_experience.context
            failure_action = failure_experience.action
            failure_outcome = failure_experience.outcome
            
            # Generate pitfall avoidance strategy
            pitfall_strategy = self._generate_pitfall_strategy(
                failure_context, failure_action, failure_outcome
            )
            
            # Store as reasoning strategy
            strategy_id = self.store_experience(
                experience_type=ExperienceType.REASONING_STRATEGY,
                category=ExperienceCategory.FAILURE_ANALYSIS,
                context=failure_context,
                action=f"Pitfall Avoidance: {failure_action}",
                outcome={"strategy": pitfall_strategy, "source": "failure_analysis"},
                success=True,  # Strategy itself is successful
                lessons_learned=[pitfall_strategy],
                tags=["failure_learning", "pitfall_avoidance", "reasoning_strategy"],
                confidence=0.8,  # High confidence in learned strategy
                impact_score=0.9  # High impact for avoiding future failures
            )
            
            logger.info(f"🧠 Learned from failure: {pitfall_strategy}")
            return strategy_id
            
        except Exception as e:
            logger.error(f"❌ Failure learning error: {e}")
            return None

    def _generate_pitfall_strategy(self, context: dict, action: str, outcome: dict) -> str:
        """
        Generate pitfall avoidance strategy from failure
        Similar to ReasoningBank's memory extraction
        """
        # Simple strategy generation based on context
        if "rss" in action.lower() or "feed" in action.lower():
            return f"When processing RSS content, validate feed format before parsing to avoid: {outcome.get('error', 'unknown error')}"
        
        elif "api" in action.lower():
            return f"When calling external APIs, implement proper error handling and retry logic to avoid: {outcome.get('error', 'unknown error')}"
        
        elif "learning" in action.lower():
            return f"When processing learning content, check content quality and relevance before storing to avoid: {outcome.get('error', 'unknown error')}"
        
        else:
            return f"When performing '{action}', implement validation and error handling to avoid: {outcome.get('error', 'unknown error')}"

    def get_reasoning_strategies(self, context: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Retrieve relevant reasoning strategies for given context
        Similar to ReasoningBank's memory retrieval
        """
        try:
            relevant_strategies = []
            
            for experience in self.experiences:
                if (experience.experience_type == ExperienceType.REASONING_STRATEGY and 
                    experience.success and 
                    experience.confidence > 0.7):
                    
                    # Simple context matching
                    if self._is_context_relevant(experience.context, context):
                        relevant_strategies.append({
                            "strategy_id": experience.experience_id,
                            "description": experience.action,
                            "lessons": experience.lessons_learned,
                            "confidence": experience.confidence,
                            "impact_score": experience.impact_score
                        })
            
            # Sort by confidence and impact
            relevant_strategies.sort(key=lambda x: x["confidence"] * x["impact_score"], reverse=True)
            
            logger.info(f"🔍 Retrieved {len(relevant_strategies)} reasoning strategies")
            return relevant_strategies[:5]  # Return top 5 strategies
            
        except Exception as e:
            logger.error(f"❌ Strategy retrieval error: {e}")
            return []

    def _is_context_relevant(self, strategy_context: dict, current_context: dict) -> bool:
        """Check if strategy context is relevant to current context"""
        # Simple keyword matching for now
        strategy_keys = set(strategy_context.keys())
        current_keys = set(current_context.keys())
        
        # If they share common keys, consider relevant
        common_keys = strategy_keys.intersection(current_keys)
        return len(common_keys) > 0

# Advanced Memory Management System
@dataclass
class MemoryItem:
    """Advanced memory item with prioritization"""
    id: str
    content: str
    category: str
    priority: float
    access_count: int
    last_accessed: float
    created_at: float
    importance_score: float
    context_tags: list[str]
    memory_type: str  # episodic, semantic, procedural
    
    def __post_init__(self):
        if self.context_tags is None:
            self.context_tags = []

@dataclass
class MemoryCluster:
    """Cluster of related memories"""
    cluster_id: str
    topic: str
    memories: list[str]  # Memory IDs
    coherence_score: float
    last_updated: float
    access_frequency: float

class AdvancedMemoryManager:
    """Advanced memory management with prioritization and optimization"""
    
    def __init__(self, db_path: str = "data/memory.db"):
        """Initialize Advanced Memory Manager"""
        self.db_path = db_path
        self.memory_items = {}
        self.memory_clusters = {}
        self.access_patterns = defaultdict(list)
        
        # Memory management parameters
        self.max_memory_items = 10000
        self.memory_compression_threshold = 0.8
        self.priority_decay_factor = 0.95
        self.context_window_size = 5
        
        # Initialize database
        self._init_database()
        self._load_memories()
        
        logger.info("Advanced Memory Manager initialized")
    
    def _init_database(self):
        """Initialize memory database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create memory items table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memory_items (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    category TEXT NOT NULL,
                    priority REAL NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    last_accessed REAL NOT NULL,
                    created_at REAL NOT NULL,
                    importance_score REAL NOT NULL,
                    context_tags TEXT,
                    memory_type TEXT NOT NULL
                )
            """)
            
            # Create memory clusters table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memory_clusters (
                    cluster_id TEXT PRIMARY KEY,
                    topic TEXT NOT NULL,
                    memories TEXT NOT NULL,
                    coherence_score REAL NOT NULL,
                    last_updated REAL NOT NULL,
                    access_frequency REAL DEFAULT 0.0
                )
            """)
            
            # Create access patterns table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS access_patterns (
                    pattern_id TEXT PRIMARY KEY,
                    context TEXT NOT NULL,
                    accessed_memories TEXT NOT NULL,
                    frequency INTEGER DEFAULT 1,
                    last_accessed REAL NOT NULL
                )
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to initialize memory database: {e}")
    
    def _load_memories(self):
        """Load memories from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Load memory items
            cursor.execute("SELECT * FROM memory_items")
            for row in cursor.fetchall():
                memory_item = MemoryItem(
                    id=row[0],
                    content=row[1],
                    category=row[2],
                    priority=row[3],
                    access_count=row[4],
                    last_accessed=row[5],
                    created_at=row[6],
                    importance_score=row[7],
                    context_tags=json.loads(row[8]) if row[8] else [],
                    memory_type=row[9]
                )
                self.memory_items[memory_item.id] = memory_item
            
            # Load memory clusters
            cursor.execute("SELECT * FROM memory_clusters")
            for row in cursor.fetchall():
                cluster = MemoryCluster(
                    cluster_id=row[0],
                    topic=row[1],
                    memories=json.loads(row[2]),
                    coherence_score=row[3],
                    last_updated=row[4],
                    access_frequency=row[5]
                )
                self.memory_clusters[cluster.cluster_id] = cluster
            
            conn.close()
            logger.info(f"Loaded {len(self.memory_items)} memory items and {len(self.memory_clusters)} clusters")
            
        except Exception as e:
            logger.error(f"Failed to load memories: {e}")
    
    def _save_memory_item(self, memory_item: MemoryItem):
        """Save memory item to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO memory_items 
                (id, content, category, priority, access_count, last_accessed, 
                 created_at, importance_score, context_tags, memory_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                memory_item.id,
                memory_item.content,
                memory_item.category,
                memory_item.priority,
                memory_item.access_count,
                memory_item.last_accessed,
                memory_item.created_at,
                memory_item.importance_score,
                json.dumps(memory_item.context_tags),
                memory_item.memory_type
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to save memory item: {e}")
    
    def add_memory(self, content: str, category: str, context_tags: list[str] = None, 
                   memory_type: str = "semantic") -> str:
        """Add new memory with automatic prioritization"""
        try:
            # Generate memory ID
            memory_id = f"mem_{hashlib.md5(content.encode()).hexdigest()[:12]}"
            
            # Calculate importance score
            importance_score = self._calculate_importance_score(content, category, context_tags)
            
            # Create memory item
            memory_item = MemoryItem(
                id=memory_id,
                content=content,
                category=category,
                priority=importance_score,
                access_count=0,
                last_accessed=time.time(),
                created_at=time.time(),
                importance_score=importance_score,
                context_tags=context_tags or [],
                memory_type=memory_type
            )
            
            # Add to memory store
            self.memory_items[memory_id] = memory_item
            
            # Save to database
            self._save_memory_item(memory_item)
            
            # Check if we need to compress memory
            if len(self.memory_items) > self.max_memory_items:
                self._compress_memory()
            
            logger.info(f"Added memory: {memory_id} (importance: {importance_score:.3f})")
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to add memory: {e}")
            return ""
    
    def _calculate_importance_score(self, content: str, category: str, context_tags: list[str]) -> float:
        """Calculate importance score for memory"""
        score = 0.5  # Base score
        
        # Content length factor
        content_length = len(content)
        if content_length > 100:
            score += 0.1
        elif content_length < 20:
            score -= 0.1
        
        # Category importance
        important_categories = ["ai_research", "technology", "science", "learning"]
        if category in important_categories:
            score += 0.2
        
        # Context tags factor
        if context_tags:
            important_tags = ["learning", "research", "breakthrough", "innovation"]
            tag_bonus = sum(0.05 for tag in context_tags if tag in important_tags)
            score += min(0.2, tag_bonus)
        
        # Content quality indicators
        quality_indicators = ["algorithm", "method", "technique", "analysis", "result"]
        quality_bonus = sum(0.02 for indicator in quality_indicators if indicator in content.lower())
        score += min(0.1, quality_bonus)
        
        return min(1.0, max(0.0, score))
    
    def retrieve_memory(self, query: str, context: dict = None, limit: int = 10) -> list[dict]:
        """Retrieve relevant memories with context awareness"""
        try:
            query_lower = query.lower()
            relevant_memories = []
            
            for memory_item in self.memory_items.values():
                relevance_score = 0.0
                
                # Content relevance
                if query_lower in memory_item.content.lower():
                    relevance_score += 0.4
                
                # Category relevance
                if context and context.get("category") == memory_item.category:
                    relevance_score += 0.2
                
                # Context tags relevance
                if context and context.get("tags"):
                    context_tags = set(context["tags"])
                    memory_tags = set(memory_item.context_tags)
                    tag_overlap = len(context_tags.intersection(memory_tags))
                    relevance_score += min(0.3, tag_overlap * 0.1)
                
                # Priority and access count factor
                priority_factor = memory_item.priority * 0.1
                access_factor = min(0.1, memory_item.access_count * 0.01)
                relevance_score += priority_factor + access_factor
                
                if relevance_score > 0.1:  # Threshold for relevance
                    relevant_memories.append({
                        "id": memory_item.id,
                        "content": memory_item.content,
                        "category": memory_item.category,
                        "relevance_score": relevance_score,
                        "priority": memory_item.priority,
                        "access_count": memory_item.access_count,
                        "memory_type": memory_item.memory_type,
                        "context_tags": memory_item.context_tags
                    })
            
            # Sort by relevance score
            relevant_memories.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            # Update access patterns
            if context:
                self._update_access_patterns(context, [m["id"] for m in relevant_memories[:limit]])
            
            # Update access count for retrieved memories
            for memory in relevant_memories[:limit]:
                if memory["id"] in self.memory_items:
                    self.memory_items[memory["id"]].access_count += 1
                    self.memory_items[memory["id"]].last_accessed = time.time()
                    self._save_memory_item(self.memory_items[memory["id"]])
            
            logger.info(f"Retrieved {len(relevant_memories[:limit])} relevant memories")
            return relevant_memories[:limit]
            
        except Exception as e:
            logger.error(f"Failed to retrieve memory: {e}")
            return []
    
    def _update_access_patterns(self, context: dict, accessed_memories: list[str]):
        """Update access patterns for context-aware retrieval"""
        try:
            context_key = json.dumps(sorted(context.items()))
            pattern_id = hashlib.md5(context_key.encode()).hexdigest()[:12]
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if pattern exists
            cursor.execute("SELECT frequency FROM access_patterns WHERE pattern_id = ?", (pattern_id,))
            result = cursor.fetchone()
            
            if result:
                # Update existing pattern
                frequency = result[0] + 1
                cursor.execute("""
                    UPDATE access_patterns 
                    SET frequency = ?, last_accessed = ?
                    WHERE pattern_id = ?
                """, (frequency, time.time(), pattern_id))
            else:
                # Create new pattern
                cursor.execute("""
                    INSERT INTO access_patterns 
                    (pattern_id, context, accessed_memories, frequency, last_accessed)
                    VALUES (?, ?, ?, ?, ?)
                """, (pattern_id, context_key, json.dumps(accessed_memories), 1, time.time()))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to update access patterns: {e}")
    
    def _compress_memory(self):
        """Compress memory by removing low-priority items"""
        try:
            logger.info("Starting memory compression...")
            
            # Sort memories by priority and access count
            sorted_memories = sorted(
                self.memory_items.items(),
                key=lambda x: (x[1].priority * x[1].access_count, x[1].last_accessed),
                reverse=True
            )
            
            # Keep top 80% of memories
            keep_count = int(len(sorted_memories) * self.memory_compression_threshold)
            memories_to_keep = sorted_memories[:keep_count]
            memories_to_remove = sorted_memories[keep_count:]
            
            # Remove low-priority memories
            for memory_id, memory_item in memories_to_remove:
                del self.memory_items[memory_id]
                
                # Remove from database
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM memory_items WHERE id = ?", (memory_id,))
                conn.commit()
                conn.close()
            
            logger.info(f"Compressed memory: removed {len(memories_to_remove)} items, kept {len(memories_to_keep)}")
            
        except Exception as e:
            logger.error(f"Failed to compress memory: {e}")
    
    def update_memory_priority(self, memory_id: str, new_priority: float):
        """Update memory priority based on usage patterns"""
        try:
            if memory_id in self.memory_items:
                memory_item = self.memory_items[memory_id]
                memory_item.priority = new_priority
                memory_item.last_accessed = time.time()
                
                self._save_memory_item(memory_item)
                logger.debug(f"Updated priority for memory {memory_id}: {new_priority:.3f}")
                
        except Exception as e:
            logger.error(f"Failed to update memory priority: {e}")
    
    def get_memory_stats(self) -> dict:
        """Get memory management statistics"""
        try:
            total_memories = len(self.memory_items)
            total_clusters = len(self.memory_clusters)
            
            # Calculate average priority
            avg_priority = sum(m.priority for m in self.memory_items.values()) / total_memories if total_memories > 0 else 0
            
            # Calculate memory distribution by type
            memory_types = defaultdict(int)
            for memory in self.memory_items.values():
                memory_types[memory.memory_type] += 1
            
            # Calculate category distribution
            categories = defaultdict(int)
            for memory in self.memory_items.values():
                categories[memory.category] += 1
            
            return {
                "total_memories": total_memories,
                "total_clusters": total_clusters,
                "avg_priority": avg_priority,
                "memory_types": dict(memory_types),
                "categories": dict(categories),
                "compression_threshold": self.memory_compression_threshold,
                "max_memory_items": self.max_memory_items
            }
            
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {}
    
    def optimize_memory(self):
        """Optimize memory by clustering and prioritizing"""
        try:
            logger.info("Starting memory optimization...")
            
            # Group memories by category and context
            category_groups = defaultdict(list)
            for memory in self.memory_items.values():
                category_groups[memory.category].append(memory)
            
            # Create clusters for each category
            for category, memories in category_groups.items():
                if len(memories) >= 3:  # Minimum cluster size
                    self._create_memory_cluster(category, memories)
            
            # Update priorities based on access patterns
            self._update_priorities_from_access_patterns()
            
            logger.info("Memory optimization completed")
            
        except Exception as e:
            logger.error(f"Failed to optimize memory: {e}")
    
    def _create_memory_cluster(self, category: str, memories: list[MemoryItem]):
        """Create memory cluster from related memories"""
        try:
            cluster_id = f"cluster_{category}_{int(time.time())}"
            
            # Calculate coherence score
            coherence_score = self._calculate_coherence_score(memories)
            
            # Create cluster
            cluster = MemoryCluster(
                cluster_id=cluster_id,
                topic=category,
                memories=[m.id for m in memories],
                coherence_score=coherence_score,
                last_updated=time.time(),
                access_frequency=sum(m.access_count for m in memories) / len(memories)
            )
            
            self.memory_clusters[cluster_id] = cluster
            
            # Save to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO memory_clusters 
                (cluster_id, topic, memories, coherence_score, last_updated, access_frequency)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                cluster.cluster_id,
                cluster.topic,
                json.dumps(cluster.memories),
                cluster.coherence_score,
                cluster.last_updated,
                cluster.access_frequency
            ))
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to create memory cluster: {e}")
    
    def _calculate_coherence_score(self, memories: list[MemoryItem]) -> float:
        """Calculate coherence score for memory cluster"""
        if len(memories) < 2:
            return 1.0
        
        # Simple coherence based on shared context tags
        all_tags = set()
        for memory in memories:
            all_tags.update(memory.context_tags)
        
        shared_tags = set(memories[0].context_tags)
        for memory in memories[1:]:
            shared_tags = shared_tags.intersection(set(memory.context_tags))
        
        coherence = len(shared_tags) / len(all_tags) if all_tags else 0.0
        return min(1.0, coherence)
    
    def _update_priorities_from_access_patterns(self):
        """Update memory priorities based on access patterns"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get access patterns
            cursor.execute("SELECT accessed_memories, frequency FROM access_patterns")
            patterns = cursor.fetchall()
            
            # Update priorities based on access frequency
            for accessed_memories_json, frequency in patterns:
                accessed_memories = json.loads(accessed_memories_json)
                
                for memory_id in accessed_memories:
                    if memory_id in self.memory_items:
                        memory_item = self.memory_items[memory_id]
                        # Increase priority based on access frequency
                        priority_boost = min(0.1, frequency * 0.01)
                        memory_item.priority = min(1.0, memory_item.priority + priority_boost)
                        self._save_memory_item(memory_item)
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to update priorities from access patterns: {e}")

# Global advanced memory manager instance
advanced_memory_manager = AdvancedMemoryManager()

