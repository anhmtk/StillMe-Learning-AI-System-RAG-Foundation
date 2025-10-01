"""
🧠 Experience Memory Integration - Security Learning System
==========================================================

Experience Memory Integration tích hợp hệ thống bảo mật với LayeredMemoryV1
để học hỏi từ kinh nghiệm, cải thiện hiệu quả, và tối ưu hóa chiến lược.

Tính năng chính:
- Security Experience Storage: Lưu trữ kinh nghiệm bảo mật
- Pattern Learning: Học pattern từ các cuộc tấn công và phòng thủ
- Strategy Optimization: Tối ưu hóa chiến lược dựa trên kinh nghiệm
- Predictive Analysis: Dự đoán các mối đe dọa tiềm ẩn
- Knowledge Transfer: Chuyển giao kiến thức giữa các module

Author: StillMe AI Security Team
Version: 2.0.0
"""

import asyncio
import hashlib
import json
import logging
import os
import statistics
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

# Import existing modules
try:
    from .blue_team_engine import AnomalyDetection, BlueTeamEngine, DefenseResult
    from .red_team_engine import AttackResult, RedTeamEngine
    from .security_orchestrator import ExerciseResult, SecurityOrchestrator
except ImportError as e:
    logging.warning(f"Some security modules not available: {e}")

# Import StillMe core modules
try:
    from ...common.logging import get_logger
    from ...common.retry import RetryManager
    from ...compat_circuitbreaker import SafeCircuitBreaker
    from ...modules.layered_memory_v1 import LayeredMemoryV1
    from ...modules.prediction_engine import PredictionEngine
except ImportError as e:
    logging.warning(f"StillMe core modules not available: {e}")


class ExperienceType(Enum):
    """Loại kinh nghiệm"""
    ATTACK_PATTERN = "attack_pattern"
    DEFENSE_STRATEGY = "defense_strategy"
    VULNERABILITY = "vulnerability"
    THREAT_INTELLIGENCE = "threat_intelligence"
    INCIDENT_RESPONSE = "incident_response"
    EXERCISE_RESULT = "exercise_result"
    PERFORMANCE_METRIC = "performance_metric"


class LearningCategory(Enum):
    """Danh mục học tập"""
    RED_TEAM = "red_team"
    BLUE_TEAM = "blue_team"
    COORDINATION = "coordination"
    INFRASTRUCTURE = "infrastructure"
    THREAT_LANDSCAPE = "threat_landscape"


@dataclass
class SecurityExperience:
    """Kinh nghiệm bảo mật"""
    id: str
    experience_type: ExperienceType
    category: LearningCategory
    title: str
    description: str
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    effectiveness_score: float
    confidence_level: float
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    access_count: int = 0
    success_count: int = 0


@dataclass
class LearningPattern:
    """Pattern học tập"""
    id: str
    pattern_type: str
    description: str
    conditions: Dict[str, Any]
    outcomes: Dict[str, Any]
    confidence: float
    frequency: int
    last_seen: datetime
    tags: List[str]


class ExperienceMemoryIntegration:
    """Experience Memory Integration - Tích hợp bộ nhớ kinh nghiệm"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = get_logger(__name__)

        # Initialize memory manager
        self.memory_manager = None
        try:
            self.memory_manager = LayeredMemoryV1()
        except Exception as e:
            self.logger.warning(f"Could not initialize memory manager: {e}")

        # Initialize prediction engine
        self.prediction_engine = None
        try:
            self.prediction_engine = PredictionEngine()
        except Exception as e:
            self.logger.warning(f"Could not initialize prediction engine: {e}")

        # Security engines
        self.red_team_engine = None
        self.blue_team_engine = None
        self.security_orchestrator = None

        # Experience storage
        self.experience_cache = {}
        self.learning_patterns = {}
        self.pattern_frequency = defaultdict(int)

        # Circuit breaker for resilience
        self.circuit_breaker = SafeCircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=Exception
        )

        # Statistics
        self.stats = {
            'total_experiences': 0,
            'stored_experiences': 0,
            'retrieved_experiences': 0,
            'learning_patterns': 0,
            'prediction_accuracy': 0.0
        }

    def set_security_engines(self, red_team: RedTeamEngine = None,
                           blue_team: BlueTeamEngine = None,
                           orchestrator: SecurityOrchestrator = None):
        """Thiết lập security engines"""
        self.red_team_engine = red_team
        self.blue_team_engine = blue_team
        self.security_orchestrator = orchestrator

    async def store_attack_experience(self, attack_result: AttackResult) -> bool:
        """Lưu trữ kinh nghiệm tấn công"""
        try:
            experience = SecurityExperience(
                id=self._generate_experience_id(attack_result),
                experience_type=ExperienceType.ATTACK_PATTERN,
                category=LearningCategory.RED_TEAM,
                title=f"Attack: {attack_result.attack_type.value}",
                description=f"Attack result: {attack_result.status.value}",
                data={
                    "attack_type": attack_result.attack_type.value,
                    "status": attack_result.status.value,
                    "payload": attack_result.payload,
                    "response": attack_result.response,
                    "execution_time": attack_result.execution_time,
                    "effectiveness": attack_result.effectiveness_score
                },
                metadata={
                    "target": attack_result.target,
                    "timestamp": attack_result.timestamp.isoformat(),
                    "environment": attack_result.environment
                },
                effectiveness_score=attack_result.effectiveness_score,
                confidence_level=0.8,
                tags=["attack", "red_team", attack_result.attack_type.value],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            return await self._store_experience(experience)

        except Exception as e:
            self.logger.error(f"Error storing attack experience: {e}")
            return False

    async def store_defense_experience(self, defense_result: DefenseResult) -> bool:
        """Lưu trữ kinh nghiệm phòng thủ"""
        try:
            experience = SecurityExperience(
                id=self._generate_experience_id(defense_result),
                experience_type=ExperienceType.DEFENSE_STRATEGY,
                category=LearningCategory.BLUE_TEAM,
                title=f"Defense: {defense_result.action.value}",
                description=f"Defense result: {defense_result.status}",
                data={
                    "action": defense_result.action.value,
                    "status": defense_result.status,
                    "effectiveness_score": defense_result.effectiveness_score,
                    "details": defense_result.details
                },
                metadata={
                    "rule_id": defense_result.rule_id,
                    "timestamp": defense_result.timestamp.isoformat()
                },
                effectiveness_score=defense_result.effectiveness_score,
                confidence_level=0.8,
                tags=["defense", "blue_team", defense_result.action.value],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            return await self._store_experience(experience)

        except Exception as e:
            self.logger.error(f"Error storing defense experience: {e}")
            return False

    async def store_anomaly_experience(self, anomaly: AnomalyDetection) -> bool:
        """Lưu trữ kinh nghiệm bất thường"""
        try:
            experience = SecurityExperience(
                id=self._generate_experience_id(anomaly),
                experience_type=ExperienceType.THREAT_INTELLIGENCE,
                category=LearningCategory.BLUE_TEAM,
                title=f"Anomaly: {anomaly.anomaly_type.value}",
                description=f"Anomaly detected: {anomaly.description}",
                data={
                    "anomaly_type": anomaly.anomaly_type.value,
                    "threat_level": anomaly.threat_level.value,
                    "indicators": anomaly.indicators,
                    "confidence": anomaly.confidence
                },
                metadata={
                    "source": anomaly.source,
                    "timestamp": anomaly.timestamp.isoformat(),
                    "metadata": anomaly.metadata
                },
                effectiveness_score=anomaly.confidence,
                confidence_level=anomaly.confidence,
                tags=["anomaly", "detection", anomaly.anomaly_type.value],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            return await self._store_experience(experience)

        except Exception as e:
            self.logger.error(f"Error storing anomaly experience: {e}")
            return False

    async def store_exercise_experience(self, exercise_result: ExerciseResult) -> bool:
        """Lưu trữ kinh nghiệm bài tập"""
        try:
            experience = SecurityExperience(
                id=self._generate_experience_id(exercise_result),
                experience_type=ExperienceType.EXERCISE_RESULT,
                category=LearningCategory.COORDINATION,
                title=f"Exercise: {exercise_result.exercise_id}",
                description=f"Exercise result: {exercise_result.overall_score:.2f}",
                data={
                    "overall_score": exercise_result.overall_score,
                    "status": exercise_result.status.value,
                    "recommendations": exercise_result.recommendations,
                    "red_team_results": len(exercise_result.red_team_results),
                    "blue_team_results": len(exercise_result.blue_team_results)
                },
                metadata={
                    "exercise_id": exercise_result.exercise_id,
                    "start_time": exercise_result.start_time.isoformat(),
                    "end_time": exercise_result.end_time.isoformat(),
                    "metadata": exercise_result.metadata
                },
                effectiveness_score=exercise_result.overall_score,
                confidence_level=0.9,
                tags=["exercise", "coordination", "red_team", "blue_team"],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            return await self._store_experience(experience)

        except Exception as e:
            self.logger.error(f"Error storing exercise experience: {e}")
            return False

    async def _store_experience(self, experience: SecurityExperience) -> bool:
        """Lưu trữ kinh nghiệm vào memory"""
        try:
            # Store in cache
            self.experience_cache[experience.id] = experience

            # Store in layered memory
            if self.memory_manager:
                await self.memory_manager.store_experience(
                    experience_type='SECURITY_TESTING',
                    data=asdict(experience),
                    tags=experience.tags
                )

            # Update statistics
            self.stats['total_experiences'] += 1
            self.stats['stored_experiences'] += 1

            # Extract learning patterns
            await self._extract_learning_patterns(experience)

            self.logger.info(f"Stored experience: {experience.title}")
            return True

        except Exception as e:
            self.logger.error(f"Error storing experience: {e}")
            return False

    async def retrieve_experiences(self,
                                 experience_type: ExperienceType = None,
                                 category: LearningCategory = None,
                                 tags: List[str] = None,
                                 min_effectiveness: float = 0.0,
                                 limit: int = 100) -> List[SecurityExperience]:
        """Truy xuất kinh nghiệm"""
        try:
            experiences = []

            # Filter experiences
            for exp in self.experience_cache.values():
                if experience_type and exp.experience_type != experience_type:
                    continue
                if category and exp.category != category:
                    continue
                if tags and not any(tag in exp.tags for tag in tags):
                    continue
                if exp.effectiveness_score < min_effectiveness:
                    continue

                experiences.append(exp)

            # Sort by effectiveness and recency
            experiences.sort(key=lambda x: (x.effectiveness_score, x.created_at), reverse=True)

            # Limit results
            experiences = experiences[:limit]

            # Update access count
            for exp in experiences:
                exp.access_count += 1

            # Update statistics
            self.stats['retrieved_experiences'] += len(experiences)

            return experiences

        except Exception as e:
            self.logger.error(f"Error retrieving experiences: {e}")
            return []

    async def _extract_learning_patterns(self, experience: SecurityExperience):
        """Trích xuất pattern học tập"""
        try:
            # Analyze data for patterns
            data = experience.data

            # Extract attack patterns
            if experience.experience_type == ExperienceType.ATTACK_PATTERN:
                pattern_id = f"attack_{data.get('attack_type', 'unknown')}"
                if pattern_id not in self.learning_patterns:
                    self.learning_patterns[pattern_id] = LearningPattern(
                        id=pattern_id,
                        pattern_type="attack",
                        description=f"Attack pattern: {data.get('attack_type', 'unknown')}",
                        conditions={"attack_type": data.get('attack_type')},
                        outcomes={"effectiveness": data.get('effectiveness', 0.0)},
                        confidence=0.5,
                        frequency=1,
                        last_seen=datetime.now(),
                        tags=["attack", "pattern"]
                    )
                else:
                    pattern = self.learning_patterns[pattern_id]
                    pattern.frequency += 1
                    pattern.last_seen = datetime.now()
                    pattern.confidence = min(pattern.confidence + 0.1, 1.0)

            # Extract defense patterns
            elif experience.experience_type == ExperienceType.DEFENSE_STRATEGY:
                pattern_id = f"defense_{data.get('action', 'unknown')}"
                if pattern_id not in self.learning_patterns:
                    self.learning_patterns[pattern_id] = LearningPattern(
                        id=pattern_id,
                        pattern_type="defense",
                        description=f"Defense pattern: {data.get('action', 'unknown')}",
                        conditions={"action": data.get('action')},
                        outcomes={"effectiveness": data.get('effectiveness_score', 0.0)},
                        confidence=0.5,
                        frequency=1,
                        last_seen=datetime.now(),
                        tags=["defense", "pattern"]
                    )
                else:
                    pattern = self.learning_patterns[pattern_id]
                    pattern.frequency += 1
                    pattern.last_seen = datetime.now()
                    pattern.confidence = min(pattern.confidence + 0.1, 1.0)

            # Update pattern frequency
            self.pattern_frequency[pattern_id] += 1
            self.stats['learning_patterns'] = len(self.learning_patterns)

        except Exception as e:
            self.logger.error(f"Error extracting learning patterns: {e}")

    async def predict_threat_likelihood(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Dự đoán khả năng đe dọa"""
        try:
            if not self.prediction_engine:
                return {"unknown": 0.5}

            # Get relevant experiences
            experiences = await self.retrieve_experiences(
                experience_type=ExperienceType.THREAT_INTELLIGENCE,
                limit=50
            )

            # Analyze patterns
            threat_scores = {}

            for exp in experiences:
                data = exp.data
                anomaly_type = data.get('anomaly_type', 'unknown')
                confidence = data.get('confidence', 0.0)

                if anomaly_type not in threat_scores:
                    threat_scores[anomaly_type] = []
                threat_scores[anomaly_type].append(confidence)

            # Calculate average scores
            for anomaly_type in threat_scores:
                scores = threat_scores[anomaly_type]
                threat_scores[anomaly_type] = statistics.mean(scores)

            return threat_scores

        except Exception as e:
            self.logger.error(f"Error predicting threat likelihood: {e}")
            return {"unknown": 0.5}

    async def recommend_attack_strategy(self, target: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Khuyến nghị chiến lược tấn công"""
        try:
            # Get successful attack experiences
            experiences = await self.retrieve_experiences(
                experience_type=ExperienceType.ATTACK_PATTERN,
                category=LearningCategory.RED_TEAM,
                min_effectiveness=0.7,
                limit=20
            )

            recommendations = []

            for exp in experiences:
                data = exp.data
                if data.get('effectiveness', 0.0) > 0.7:
                    recommendations.append({
                        "attack_type": data.get('attack_type'),
                        "effectiveness": data.get('effectiveness'),
                        "confidence": exp.confidence_level,
                        "description": exp.description,
                        "tags": exp.tags
                    })

            # Sort by effectiveness
            recommendations.sort(key=lambda x: x['effectiveness'], reverse=True)

            return recommendations[:5]  # Top 5 recommendations

        except Exception as e:
            self.logger.error(f"Error recommending attack strategy: {e}")
            return []

    async def recommend_defense_strategy(self, threat_type: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Khuyến nghị chiến lược phòng thủ"""
        try:
            # Get successful defense experiences
            experiences = await self.retrieve_experiences(
                experience_type=ExperienceType.DEFENSE_STRATEGY,
                category=LearningCategory.BLUE_TEAM,
                min_effectiveness=0.7,
                limit=20
            )

            recommendations = []

            for exp in experiences:
                data = exp.data
                if data.get('effectiveness_score', 0.0) > 0.7:
                    recommendations.append({
                        "action": data.get('action'),
                        "effectiveness": data.get('effectiveness_score'),
                        "confidence": exp.confidence_level,
                        "description": exp.description,
                        "tags": exp.tags
                    })

            # Sort by effectiveness
            recommendations.sort(key=lambda x: x['effectiveness'], reverse=True)

            return recommendations[:5]  # Top 5 recommendations

        except Exception as e:
            self.logger.error(f"Error recommending defense strategy: {e}")
            return []

    def _generate_experience_id(self, obj: Any) -> str:
        """Tạo ID cho kinh nghiệm"""
        try:
            # Create hash from object data
            obj_str = str(obj.__dict__) if hasattr(obj, '__dict__') else str(obj)
            obj_hash = hashlib.sha256(obj_str.encode()).hexdigest()[:12]
            timestamp = int(time.time())
            return f"exp_{timestamp}_{obj_hash}"
        except Exception:
            return f"exp_{int(time.time())}_{id(obj)}"

    def get_learning_statistics(self) -> Dict[str, Any]:
        """Lấy thống kê học tập"""
        return {
            'stats': self.stats.copy(),
            'cached_experiences': len(self.experience_cache),
            'learning_patterns': len(self.learning_patterns),
            'pattern_frequency': dict(self.pattern_frequency),
            'memory_available': self.memory_manager is not None,
            'prediction_available': self.prediction_engine is not None
        }

    async def export_experiences(self, file_path: str) -> bool:
        """Xuất kinh nghiệm ra file"""
        try:
            export_data = {
                'experiences': [asdict(exp) for exp in self.experience_cache.values()],
                'patterns': [asdict(pattern) for pattern in self.learning_patterns.values()],
                'statistics': self.stats,
                'exported_at': datetime.now().isoformat()
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)

            self.logger.info(f"Exported experiences to: {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error exporting experiences: {e}")
            return False

    async def import_experiences(self, file_path: str) -> bool:
        """Nhập kinh nghiệm từ file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)

            # Import experiences
            for exp_data in import_data.get('experiences', []):
                experience = SecurityExperience(**exp_data)
                self.experience_cache[experience.id] = experience

            # Import patterns
            for pattern_data in import_data.get('patterns', []):
                pattern = LearningPattern(**pattern_data)
                self.learning_patterns[pattern.id] = pattern

            self.logger.info(f"Imported experiences from: {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error importing experiences: {e}")
            return False


# Demo và testing
async def demo_experience_memory_integration():
    """Demo Experience Memory Integration"""
    print("🧠 Experience Memory Integration Demo")
    print("=" * 50)

    # Initialize integration
    config = {
        'cache_size': 1000,
        'pattern_threshold': 0.7,
        'learning_rate': 0.1
    }

    integration = ExperienceMemoryIntegration(config)

    # Simulate storing experiences
    print("📚 Storing sample experiences...")

    # Mock attack result
    class MockAttackResult:
        def __init__(self):
            self.attack_type = type('AttackType', (), {'value': 'sql_injection'})()
            self.status = type('Status', (), {'value': 'success'})()
            self.payload = "SELECT * FROM users"
            self.response = "200 OK"
            self.execution_time = 1.5
            self.effectiveness_score = 0.8
            self.target = "web_app"
            self.timestamp = datetime.now()
            self.environment = "sandbox"

    # Mock defense result
    class MockDefenseResult:
        def __init__(self):
            self.action = type('Action', (), {'value': 'block_ip'})()
            self.status = "success"
            self.effectiveness_score = 0.9
            self.details = {"blocked_ip": "192.168.1.100"}
            self.rule_id = "rule_001"
            self.timestamp = datetime.now()

    # Store experiences
    attack_result = MockAttackResult()
    defense_result = MockDefenseResult()

    await integration.store_attack_experience(attack_result)
    await integration.store_defense_experience(defense_result)

    # Retrieve experiences
    print("🔍 Retrieving experiences...")
    experiences = await integration.retrieve_experiences(limit=10)

    print(f"📊 Retrieved {len(experiences)} experiences:")
    for exp in experiences:
        print(f"  - {exp.title}: {exp.effectiveness_score:.2f}")

    # Get recommendations
    print("\n💡 Getting recommendations...")
    attack_recs = await integration.recommend_attack_strategy("web_app", {})
    defense_recs = await integration.recommend_defense_strategy("sql_injection", {})

    print(f"🎯 Attack recommendations: {len(attack_recs)}")
    for rec in attack_recs:
        print(f"  - {rec['attack_type']}: {rec['effectiveness']:.2f}")

    print(f"🛡️ Defense recommendations: {len(defense_recs)}")
    for rec in defense_recs:
        print(f"  - {rec['action']}: {rec['effectiveness']:.2f}")

    # Show statistics
    stats = integration.get_learning_statistics()
    print(f"\n📈 Learning Statistics:")
    print(f"  - Total experiences: {stats['stats']['total_experiences']}")
    print(f"  - Stored experiences: {stats['stats']['stored_experiences']}")
    print(f"  - Learning patterns: {stats['learning_patterns']}")
    print(f"  - Memory available: {stats['memory_available']}")


if __name__ == "__main__":
    asyncio.run(demo_experience_memory_integration())
