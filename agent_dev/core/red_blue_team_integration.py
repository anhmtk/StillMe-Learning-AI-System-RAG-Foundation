#!/usr/bin/env python3
"""
Red Team/Blue Team Integration - AgentDev Unified Security Module
Tích hợp Red Team/Blue Team vào AgentDev Unified

Tính năng:
1. Red Team Engine - Mô phỏng tấn công để học hỏi
2. Blue Team Engine - Phòng thủ và phát hiện bất thường
3. Security Orchestrator - Điều phối Red/Blue Team
4. Experience Integration - Học hỏi từ kinh nghiệm bảo mật
5. Safe Attack Simulation - Mô phỏng tấn công an toàn
6. Adaptive Defense - Phòng thủ thích ứng
"""

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class AttackType(Enum):
    """Loại tấn công"""

    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    CSRF = "csrf"
    BRUTE_FORCE = "brute_force"
    CODE_INJECTION = "code_injection"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXFILTRATION = "data_exfiltration"


class DefenseType(Enum):
    """Loại phòng thủ"""

    INPUT_VALIDATION = "input_validation"
    OUTPUT_ENCODING = "output_encoding"
    RATE_LIMITING = "rate_limiting"
    ACCESS_CONTROL = "access_control"
    ENCRYPTION = "encryption"
    MONITORING = "monitoring"
    ANOMALY_DETECTION = "anomaly_detection"


class SecurityLevel(Enum):
    """Mức độ bảo mật"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AttackScenario:
    """Kịch bản tấn công"""

    scenario_id: str
    attack_type: AttackType
    description: str
    payload: str
    target: str
    expected_impact: SecurityLevel
    success_criteria: list[str]
    created_at: datetime


@dataclass
class DefenseStrategy:
    """Chiến lược phòng thủ"""

    strategy_id: str
    defense_type: DefenseType
    description: str
    implementation: str
    effectiveness_score: float
    resource_cost: float
    created_at: datetime


@dataclass
class SecurityExercise:
    """Bài tập bảo mật"""

    exercise_id: str
    title: str
    description: str
    attack_scenarios: list[AttackScenario]
    defense_strategies: list[DefenseStrategy]
    learning_objectives: list[str]
    difficulty_level: SecurityLevel
    created_at: datetime


@dataclass
class SecurityLearningResult:
    """Kết quả học hỏi bảo mật"""

    total_exercises: int
    attack_scenarios_tested: int
    defense_strategies_implemented: int
    vulnerabilities_discovered: int
    security_improvements: list[str]
    learning_score: float
    recommendations: list[str]
    analysis_time: float


class RedBlueTeamIntegration:
    """Red Team/Blue Team Integration cho AgentDev Unified"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.exercises_db = self.project_root / "data" / "security_exercises.json"
        self.learning_db = self.project_root / "data" / "security_learning.json"

        # Ensure data directory exists
        self.exercises_db.parent.mkdir(parents=True, exist_ok=True)

        # Load existing data
        self.exercises = self._load_exercises()
        self.learning_history = self._load_learning_history()

        # Initialize default exercises if none exist
        if not self.exercises:
            self._initialize_default_exercises()

    def _load_exercises(self) -> list[SecurityExercise]:
        """Load security exercises from database"""
        if not self.exercises_db.exists():
            return []

        try:
            with open(self.exercises_db, encoding="utf-8") as f:
                data = json.load(f)

            exercises: list[SecurityExercise] = []
            for exercise_data in data:
                # Convert attack scenarios
                attack_scenarios: list[AttackScenario] = []
                for scenario_data in exercise_data.get("attack_scenarios", []):
                    scenario_data["created_at"] = datetime.fromisoformat(
                        scenario_data["created_at"]
                    )
                    attack_scenarios.append(AttackScenario(**scenario_data))

                # Convert defense strategies
                defense_strategies: list[DefenseStrategy] = []
                for strategy_data in exercise_data.get("defense_strategies", []):
                    strategy_data["created_at"] = datetime.fromisoformat(
                        strategy_data["created_at"]
                    )
                    defense_strategies.append(DefenseStrategy(**strategy_data))

                exercise_data["attack_scenarios"] = attack_scenarios
                exercise_data["defense_strategies"] = defense_strategies
                exercise_data["created_at"] = datetime.fromisoformat(
                    exercise_data["created_at"]
                )
                exercises.append(SecurityExercise(**exercise_data))

            return exercises
        except Exception as e:
            print(f"Error loading exercises: {e}")
            return []

    def _load_learning_history(self) -> list[dict[str, Any]]:
        """Load learning history from database"""
        if not self.learning_db.exists():
            return []

        try:
            with open(self.learning_db, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading learning history: {e}")
            return []

    def _save_exercises(self):
        """Save exercises to database"""
        try:
            data: list[dict[str, Any]] = []
            for exercise in self.exercises:
                exercise_dict = asdict(exercise)
                exercise_dict["created_at"] = exercise.created_at.isoformat()

                # Convert attack scenarios
                attack_scenarios: list[dict[str, Any]] = []
                for scenario in exercise.attack_scenarios:
                    scenario_dict = asdict(scenario)
                    scenario_dict["created_at"] = scenario.created_at.isoformat()
                    attack_scenarios.append(scenario_dict)
                exercise_dict["attack_scenarios"] = attack_scenarios

                # Convert defense strategies
                defense_strategies: list[dict[str, Any]] = []
                for strategy in exercise.defense_strategies:
                    strategy_dict = asdict(strategy)
                    strategy_dict["created_at"] = strategy.created_at.isoformat()
                    defense_strategies.append(strategy_dict)
                exercise_dict["defense_strategies"] = defense_strategies

                data.append(exercise_dict)

            with open(self.exercises_db, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving exercises: {e}")

    def _save_learning_history(self):
        """Save learning history to database"""
        try:
            with open(self.learning_db, "w", encoding="utf-8") as f:
                json.dump(self.learning_history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving learning history: {e}")

    def _initialize_default_exercises(self):
        """Initialize default security exercises"""
        default_exercises = [
            SecurityExercise(
                exercise_id="web_security_basics",
                title="Web Security Basics",
                description="Basic web security vulnerabilities and defenses",
                attack_scenarios=[
                    AttackScenario(
                        scenario_id="sql_injection_basic",
                        attack_type=AttackType.SQL_INJECTION,
                        description="Basic SQL injection attack",
                        payload="' OR '1'='1",
                        target="login_form",
                        expected_impact=SecurityLevel.HIGH,
                        success_criteria=["Bypass authentication", "Access user data"],
                        created_at=datetime.now(),
                    ),
                    AttackScenario(
                        scenario_id="xss_basic",
                        attack_type=AttackType.XSS,
                        description="Basic XSS attack",
                        payload="<script>alert('XSS')</script>",
                        target="comment_form",
                        expected_impact=SecurityLevel.MEDIUM,
                        success_criteria=["Execute JavaScript", "Steal session"],
                        created_at=datetime.now(),
                    ),
                ],
                defense_strategies=[
                    DefenseStrategy(
                        strategy_id="input_validation",
                        defense_type=DefenseType.INPUT_VALIDATION,
                        description="Validate and sanitize all inputs",
                        implementation="Use parameterized queries and input validation",
                        effectiveness_score=0.9,
                        resource_cost=0.3,
                        created_at=datetime.now(),
                    ),
                    DefenseStrategy(
                        strategy_id="output_encoding",
                        defense_type=DefenseType.OUTPUT_ENCODING,
                        description="Encode all outputs to prevent XSS",
                        implementation="HTML encode all user-generated content",
                        effectiveness_score=0.8,
                        resource_cost=0.2,
                        created_at=datetime.now(),
                    ),
                ],
                learning_objectives=[
                    "Understand common web vulnerabilities",
                    "Learn basic defense strategies",
                    "Practice secure coding",
                ],
                difficulty_level=SecurityLevel.LOW,
                created_at=datetime.now(),
            ),
            SecurityExercise(
                exercise_id="advanced_security",
                title="Advanced Security Testing",
                description="Advanced security testing scenarios",
                attack_scenarios=[
                    AttackScenario(
                        scenario_id="privilege_escalation",
                        attack_type=AttackType.PRIVILEGE_ESCALATION,
                        description="Privilege escalation attack",
                        payload="sudo -u root /bin/bash",
                        target="user_account",
                        expected_impact=SecurityLevel.CRITICAL,
                        success_criteria=["Gain root access", "Bypass access controls"],
                        created_at=datetime.now(),
                    )
                ],
                defense_strategies=[
                    DefenseStrategy(
                        strategy_id="access_control",
                        defense_type=DefenseType.ACCESS_CONTROL,
                        description="Implement proper access controls",
                        implementation="Role-based access control and least privilege",
                        effectiveness_score=0.95,
                        resource_cost=0.5,
                        created_at=datetime.now(),
                    )
                ],
                learning_objectives=[
                    "Understand advanced attack vectors",
                    "Learn defense in depth",
                    "Practice security testing",
                ],
                difficulty_level=SecurityLevel.HIGH,
                created_at=datetime.now(),
            ),
        ]

        self.exercises = default_exercises
        self._save_exercises()

    def run_security_exercise(self, exercise_id: str) -> dict[str, Any]:
        """Run a security exercise"""
        exercise = None
        for ex in self.exercises:
            if ex.exercise_id == exercise_id:
                exercise = ex
                break

        if not exercise:
            return {"error": "Exercise not found"}

        print(f"🎯 Running Security Exercise: {exercise.title}")
        print(f"📝 Description: {exercise.description}")
        print(f"🎯 Learning Objectives: {', '.join(exercise.learning_objectives)}")
        print(f"⚠️ Difficulty: {exercise.difficulty_level.value}")

        # Simulate attack scenarios
        attack_results: list[dict[str, Any]] = []
        for scenario in exercise.attack_scenarios:
            print(f"\n🔴 Testing Attack: {scenario.description}")
            print(f"   Payload: {scenario.payload}")
            print(f"   Target: {scenario.target}")
            print(f"   Expected Impact: {scenario.expected_impact.value}")

            # Simulate attack execution
            success = self._simulate_attack(scenario)
            attack_results.append(
                {
                    "scenario_id": scenario.scenario_id,
                    "success": success,
                    "impact": scenario.expected_impact.value,
                }
            )

        # Simulate defense strategies
        defense_results: list[dict[str, Any]] = []
        for strategy in exercise.defense_strategies:
            print(f"\n🔵 Testing Defense: {strategy.description}")
            print(f"   Implementation: {strategy.implementation}")
            print(f"   Effectiveness: {strategy.effectiveness_score:.2f}")

            # Simulate defense implementation
            effectiveness = self._simulate_defense(strategy)
            defense_results.append(
                {
                    "strategy_id": strategy.strategy_id,
                    "effectiveness": effectiveness,
                    "cost": strategy.resource_cost,
                }
            )

        # Calculate learning results
        vulnerabilities_discovered = len([r for r in attack_results if r["success"]])
        security_improvements = [s.description for s in exercise.defense_strategies]
        learning_score = min(
            1.0, (vulnerabilities_discovered * 0.3 + len(defense_results) * 0.2)
        )

        result = {
            "exercise_id": exercise_id,
            "attack_results": attack_results,
            "defense_results": defense_results,
            "vulnerabilities_discovered": vulnerabilities_discovered,
            "security_improvements": security_improvements,
            "learning_score": learning_score,
            "recommendations": self._generate_security_recommendations(
                exercise, attack_results, defense_results
            ),
        }

        # Store learning history
        self.learning_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "exercise_id": exercise_id,
                "result": result,
            }
        )
        self._save_learning_history()

        return result

    def _simulate_attack(self, scenario: AttackScenario) -> bool:
        """Simulate attack execution"""
        # Simple simulation based on attack type and difficulty
        base_success_rate = {
            AttackType.SQL_INJECTION: 0.7,
            AttackType.XSS: 0.6,
            AttackType.CSRF: 0.5,
            AttackType.BRUTE_FORCE: 0.4,
            AttackType.CODE_INJECTION: 0.3,
            AttackType.PRIVILEGE_ESCALATION: 0.2,
            AttackType.DATA_EXFILTRATION: 0.3,
        }

        success_rate = base_success_rate.get(scenario.attack_type, 0.5)

        # Adjust based on difficulty
        if scenario.expected_impact == SecurityLevel.CRITICAL:
            success_rate *= 0.5
        elif scenario.expected_impact == SecurityLevel.HIGH:
            success_rate *= 0.7
        elif scenario.expected_impact == SecurityLevel.MEDIUM:
            success_rate *= 0.8

        # Simulate random success
        import random

        return random.random() < success_rate

    def _simulate_defense(self, strategy: DefenseStrategy) -> float:
        """Simulate defense effectiveness"""
        # Base effectiveness with some variation
        base_effectiveness = strategy.effectiveness_score

        # Add some random variation
        import random

        variation = random.uniform(-0.1, 0.1)
        effectiveness = max(0.0, min(1.0, base_effectiveness + variation))

        return effectiveness

    def _generate_security_recommendations(
        self,
        exercise: SecurityExercise,
        attack_results: list[dict[str, Any]],
        defense_results: list[dict[str, Any]],
    ) -> list[str]:
        """Generate security recommendations"""
        recommendations: list[str] = []

        # Analyze attack results
        successful_attacks: list[dict[str, Any]] = [
            r for r in attack_results if r["success"]
        ]
        if successful_attacks:
            recommendations.append(
                f"Implement additional defenses for {len(successful_attacks)} successful attack scenarios"
            )

        # Analyze defense results
        effective_defenses: list[dict[str, Any]] = [
            r for r in defense_results if r["effectiveness"] > 0.8
        ]
        if effective_defenses:
            recommendations.append(
                f"Deploy {len(effective_defenses)} highly effective defense strategies"
            )

        # General recommendations
        recommendations.extend(
            [
                "Conduct regular security assessments",
                "Implement defense in depth strategy",
                "Monitor for new attack vectors",
                "Keep security tools updated",
            ]
        )

        return recommendations

    def learn_from_security_experience(self) -> SecurityLearningResult:
        """Learn from security experiences"""
        start_time = time.time()

        # Analyze learning history
        total_exercises = len(self.learning_history)
        attack_scenarios_tested = sum(
            len(ex.get("result", {}).get("attack_results", []))
            for ex in self.learning_history
        )
        defense_strategies_implemented = sum(
            len(ex.get("result", {}).get("defense_results", []))
            for ex in self.learning_history
        )
        vulnerabilities_discovered = sum(
            ex.get("result", {}).get("vulnerabilities_discovered", 0)
            for ex in self.learning_history
        )

        # Generate security improvements
        security_improvements: list[str] = []
        for exercise in self.exercises:
            security_improvements.extend(
                [s.description for s in exercise.defense_strategies]
            )

        # Calculate learning score
        learning_score = min(
            1.0, (total_exercises * 0.1 + vulnerabilities_discovered * 0.2)
        )

        # Generate recommendations
        recommendations = [
            "Continue practicing security exercises",
            "Focus on high-impact vulnerabilities",
            "Implement defense in depth",
            "Regular security assessments",
        ]

        return SecurityLearningResult(
            total_exercises=total_exercises,
            attack_scenarios_tested=attack_scenarios_tested,
            defense_strategies_implemented=defense_strategies_implemented,
            vulnerabilities_discovered=vulnerabilities_discovered,
            security_improvements=security_improvements,
            learning_score=learning_score,
            recommendations=recommendations,
            analysis_time=time.time() - start_time,
        )


# Test function
if __name__ == "__main__":
    red_blue_team = RedBlueTeamIntegration()

    # Run a security exercise
    result = red_blue_team.run_security_exercise("web_security_basics")

    print("\n🎯 Security Exercise Results:")
    print(f"   📊 Vulnerabilities Discovered: {result['vulnerabilities_discovered']}")
    print(f"   🔒 Security Improvements: {len(result['security_improvements'])}")
    print(f"   📈 Learning Score: {result['learning_score']:.2f}")
    print(f"   💡 Recommendations: {len(result['recommendations'])}")

    # Learn from experience
    learning_result = red_blue_team.learn_from_security_experience()

    print("\n📚 Security Learning Results:")
    print(f"   📊 Total Exercises: {learning_result.total_exercises}")
    print(f"   🎯 Attack Scenarios Tested: {learning_result.attack_scenarios_tested}")
    print(f"   🔒 Defense Strategies: {learning_result.defense_strategies_implemented}")
    print(
        f"   🚨 Vulnerabilities Discovered: {learning_result.vulnerabilities_discovered}"
    )
    print(f"   📈 Learning Score: {learning_result.learning_score:.2f}")
    print(f"   ⏱️ Analysis Time: {learning_result.analysis_time:.3f}s")
