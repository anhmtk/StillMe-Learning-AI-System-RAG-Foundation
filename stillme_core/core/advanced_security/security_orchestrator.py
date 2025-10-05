"""
🎭 Security Orchestrator - Red/Blue Team Coordination System
============================================================

Security Orchestrator điều phối hoạt động của Red Team và Blue Team,
quản lý scheduling, tạo báo cáo, và đảm bảo tính hiệu quả của hệ thống
bảo mật tự động.

Tính năng chính:
- Red/Blue Team Coordination: Điều phối hoạt động tấn công và phòng thủ
- Automated Scheduling: Lên lịch tự động cho các cuộc tập trận
- Report Generation: Tạo báo cáo chi tiết về kết quả
- Performance Monitoring: Giám sát hiệu suất của hệ thống
- Integration Management: Quản lý tích hợp với các module khác

Author: StillMe AI Security Team
Version: 2.0.0
"""

import asyncio
import logging
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

# Import existing modules
try:
    from .blue_team_engine import BlueTeamEngine
    from .red_team_engine import RedTeamEngine
    from .sandbox_controller import SandboxController
except ImportError as e:
    logging.warning(f"Some security modules not available: {e}")

# Import StillMe core modules
try:
    from ...common.logging import get_logger
    from ...compat_circuitbreaker import SafeCircuitBreaker
    from ...modules.layered_memory_v1 import LayeredMemoryV1
    from ...modules.prediction_engine import PredictionEngine
except ImportError as e:
    logging.warning(f"StillMe core modules not available: {e}")


class ExerciseType(Enum):
    """Loại bài tập bảo mật"""

    PENETRATION_TEST = "penetration_test"
    VULNERABILITY_ASSESSMENT = "vulnerability_assessment"
    INCIDENT_RESPONSE = "incident_response"
    RED_TEAM_EXERCISE = "red_team_exercise"
    BLUE_TEAM_TRAINING = "blue_team_training"
    COMBINED_EXERCISE = "combined_exercise"


class ExerciseStatus(Enum):
    """Trạng thái bài tập"""

    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class SecurityExercise:
    """Bài tập bảo mật"""

    id: str
    name: str
    exercise_type: ExerciseType
    description: str
    scheduled_time: datetime
    duration_minutes: int
    status: ExerciseStatus
    red_team_config: dict[str, Any]
    blue_team_config: dict[str, Any]
    sandbox_config: dict[str, Any]
    created_at: datetime
    updated_at: datetime


@dataclass
class ExerciseResult:
    """Kết quả bài tập"""

    exercise_id: str
    start_time: datetime
    end_time: datetime
    status: ExerciseStatus
    red_team_results: list[dict[str, Any]]
    blue_team_results: list[dict[str, Any]]
    overall_score: float
    recommendations: list[str]
    metadata: dict[str, Any]


class SecurityOrchestrator:
    """Security Orchestrator - Điều phối Red/Blue Team"""

    def __init__(self, config: dict[str, Any] = None):
        self.config = config or {}
        self.logger = get_logger(__name__)

        # Initialize components
        self.red_team_engine = None
        self.blue_team_engine = None
        self.sandbox_controller = None

        try:
            self.red_team_engine = RedTeamEngine(self.config)
            self.blue_team_engine = BlueTeamEngine(self.config)
            self.sandbox_controller = SandboxController(self.config)
        except Exception as e:
            self.logger.warning(f"Could not initialize security engines: {e}")

        # Integration with StillMe modules
        self.memory_manager = None
        self.prediction_engine = None

        try:
            self.memory_manager = LayeredMemoryV1()
            self.prediction_engine = PredictionEngine()
        except Exception as e:
            self.logger.warning(f"Could not initialize StillMe modules: {e}")

        # Exercise management
        self.scheduled_exercises = {}
        self.exercise_history = deque(maxlen=1000)
        self.active_exercises = {}

        # Circuit breaker for resilience
        self.circuit_breaker = SafeCircuitBreaker(
            failure_threshold=5, recovery_timeout=60, expected_exception=Exception
        )

        # Statistics
        self.stats = {
            "total_exercises": 0,
            "completed_exercises": 0,
            "failed_exercises": 0,
            "average_score": 0.0,
            "total_runtime": 0.0,
        }

    async def schedule_exercise(self, exercise: SecurityExercise) -> bool:
        """Lên lịch bài tập bảo mật"""
        try:
            # Validate exercise configuration
            if not self._validate_exercise_config(exercise):
                self.logger.error(f"Invalid exercise configuration: {exercise.id}")
                return False

            # Store exercise
            self.scheduled_exercises[exercise.id] = exercise

            # Schedule execution
            delay = (exercise.scheduled_time - datetime.now()).total_seconds()
            if delay > 0:
                asyncio.create_task(self._execute_exercise_delayed(exercise, delay))
            else:
                asyncio.create_task(self._execute_exercise(exercise))

            self.logger.info(
                f"Scheduled exercise: {exercise.name} at {exercise.scheduled_time}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Error scheduling exercise {exercise.id}: {e}")
            return False

    async def _execute_exercise_delayed(self, exercise: SecurityExercise, delay: float):
        """Thực hiện bài tập sau delay"""
        await asyncio.sleep(delay)
        await self._execute_exercise(exercise)

    async def _execute_exercise(self, exercise: SecurityExercise):
        """Thực hiện bài tập bảo mật"""
        exercise_id = exercise.id

        try:
            # Update status
            exercise.status = ExerciseStatus.RUNNING
            self.active_exercises[exercise_id] = exercise

            self.logger.info(f"Starting exercise: {exercise.name}")

            # Create sandbox environment
            sandbox_id = await self._create_exercise_sandbox(exercise)

            # Execute Red Team activities
            red_team_results = await self._execute_red_team_activities(
                exercise, sandbox_id
            )

            # Execute Blue Team activities
            blue_team_results = await self._execute_blue_team_activities(
                exercise, sandbox_id
            )

            # Analyze results
            overall_score = await self._analyze_exercise_results(
                red_team_results, blue_team_results
            )

            # Generate recommendations
            recommendations = await self._generate_recommendations(
                red_team_results, blue_team_results
            )

            # Create result
            result = ExerciseResult(
                exercise_id=exercise_id,
                start_time=datetime.now(),
                end_time=datetime.now(),
                status=ExerciseStatus.COMPLETED,
                red_team_results=red_team_results,
                blue_team_results=blue_team_results,
                overall_score=overall_score,
                recommendations=recommendations,
                metadata={"sandbox_id": sandbox_id},
            )

            # Store result
            self.exercise_history.append(result)
            exercise.status = ExerciseStatus.COMPLETED

            # Update statistics
            self._update_statistics(result)

            # Store in memory
            await self._store_exercise_in_memory(result)

            # Cleanup
            await self._cleanup_exercise_sandbox(sandbox_id)
            if exercise_id in self.active_exercises:
                del self.active_exercises[exercise_id]

            self.logger.info(
                f"Completed exercise: {exercise.name} (score: {overall_score:.2f})"
            )

        except Exception as e:
            self.logger.error(f"Error executing exercise {exercise_id}: {e}")
            exercise.status = ExerciseStatus.FAILED

            # Update statistics
            self.stats["failed_exercises"] += 1

            # Cleanup
            if exercise_id in self.active_exercises:
                del self.active_exercises[exercise_id]

    def _validate_exercise_config(self, exercise: SecurityExercise) -> bool:
        """Kiểm tra cấu hình bài tập"""
        # Check required fields
        if not exercise.id or not exercise.name:
            return False

        # Check scheduled time
        if exercise.scheduled_time < datetime.now():
            return False

        # Check duration
        if exercise.duration_minutes <= 0:
            return False

        return True

    async def _create_exercise_sandbox(self, exercise: SecurityExercise) -> str:
        """Tạo sandbox cho bài tập"""
        try:
            sandbox_config = {
                "name": f"exercise_{exercise.id}",
                "image": "stillme-security-sandbox",
                "resources": exercise.sandbox_config.get("resources", {}),
                "network": exercise.sandbox_config.get("network", {}),
                "security": exercise.sandbox_config.get("security", {}),
            }

            sandbox_id = await self.sandbox_controller.create_sandbox(sandbox_config)
            return sandbox_id

        except Exception as e:
            self.logger.error(f"Error creating sandbox for exercise {exercise.id}: {e}")
            raise

    async def _execute_red_team_activities(
        self, exercise: SecurityExercise, sandbox_id: str
    ) -> list[dict[str, Any]]:
        """Thực hiện hoạt động Red Team"""
        try:
            if not self.red_team_engine:
                return []

            # Configure Red Team
            red_team_config = exercise.red_team_config

            # Execute attacks
            results = []

            # Pattern-based attacks
            if red_team_config.get("pattern_attacks", False):
                pattern_results = await self.red_team_engine.execute_pattern_attacks(
                    sandbox_id
                )
                results.extend(pattern_results)

            # AI-powered attacks
            if red_team_config.get("ai_attacks", False):
                ai_results = await self.red_team_engine.execute_ai_powered_attacks(
                    sandbox_id
                )
                results.extend(ai_results)

            # Adaptive attacks
            if red_team_config.get("adaptive_attacks", False):
                adaptive_results = await self.red_team_engine.execute_adaptive_attacks(
                    sandbox_id
                )
                results.extend(adaptive_results)

            return results

        except Exception as e:
            self.logger.error(f"Error executing Red Team activities: {e}")
            return []

    async def _execute_blue_team_activities(
        self, exercise: SecurityExercise, sandbox_id: str
    ) -> list[dict[str, Any]]:
        """Thực hiện hoạt động Blue Team"""
        try:
            if not self.blue_team_engine:
                return []

            # Configure Blue Team
            blue_team_config = exercise.blue_team_config

            # Execute defense activities
            results = []

            # Anomaly detection
            if blue_team_config.get("anomaly_detection", False):
                anomaly_results = await self.blue_team_engine.analyze_system_state()
                results.extend(anomaly_results)

            # Defense execution
            if blue_team_config.get("defense_execution", False):
                defense_results = await self.blue_team_engine.execute_defense_strategy(
                    anomaly_results
                )
                results.extend(defense_results)

            return results

        except Exception as e:
            self.logger.error(f"Error executing Blue Team activities: {e}")
            return []

    async def _analyze_exercise_results(
        self,
        red_team_results: list[dict[str, Any]],
        blue_team_results: list[dict[str, Any]],
    ) -> float:
        """Phân tích kết quả bài tập"""
        try:
            # Calculate Red Team effectiveness
            red_team_score = 0.0
            if red_team_results:
                successful_attacks = len(
                    [r for r in red_team_results if r.get("success", False)]
                )
                red_team_score = successful_attacks / len(red_team_results)

            # Calculate Blue Team effectiveness
            blue_team_score = 0.0
            if blue_team_results:
                successful_defenses = len(
                    [r for r in blue_team_results if r.get("success", False)]
                )
                blue_team_score = successful_defenses / len(blue_team_results)

            # Calculate overall score (balanced approach)
            overall_score = (red_team_score + blue_team_score) / 2.0

            return overall_score

        except Exception as e:
            self.logger.error(f"Error analyzing exercise results: {e}")
            return 0.0

    async def _generate_recommendations(
        self,
        red_team_results: list[dict[str, Any]],
        blue_team_results: list[dict[str, Any]],
    ) -> list[str]:
        """Tạo khuyến nghị từ kết quả"""
        recommendations = []

        try:
            # Analyze Red Team results
            failed_attacks = [
                r for r in red_team_results if not r.get("success", False)
            ]
            if failed_attacks:
                recommendations.append(
                    "Strengthen defense mechanisms for identified attack vectors"
                )

            # Analyze Blue Team results
            failed_defenses = [
                r for r in blue_team_results if not r.get("success", False)
            ]
            if failed_defenses:
                recommendations.append("Improve detection and response capabilities")

            # General recommendations
            if len(red_team_results) > len(blue_team_results):
                recommendations.append("Increase Blue Team resources and training")
            elif len(blue_team_results) > len(red_team_results):
                recommendations.append("Enhance Red Team attack sophistication")

            return recommendations

        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return ["Review exercise configuration and results"]

    def _update_statistics(self, result: ExerciseResult):
        """Cập nhật thống kê"""
        self.stats["total_exercises"] += 1
        self.stats["completed_exercises"] += 1

        # Update average score
        total_score = self.stats["average_score"] * (
            self.stats["completed_exercises"] - 1
        )
        self.stats["average_score"] = (total_score + result.overall_score) / self.stats[
            "completed_exercises"
        ]

        # Update runtime
        runtime = (result.end_time - result.start_time).total_seconds()
        self.stats["total_runtime"] += runtime

    async def _store_exercise_in_memory(self, result: ExerciseResult):
        """Lưu kết quả bài tập vào memory"""
        try:
            if not self.memory_manager:
                return

            memory_data = {
                "type": "SECURITY_EXERCISE",
                "exercise_id": result.exercise_id,
                "overall_score": result.overall_score,
                "status": result.status.value,
                "recommendations": result.recommendations,
                "timestamp": result.start_time.isoformat(),
                "metadata": result.metadata,
            }

            await self.memory_manager.store_experience(
                experience_type="SECURITY_TESTING",
                data=memory_data,
                tags=["exercise", "security", "red_team", "blue_team"],
            )

        except Exception as e:
            self.logger.error(f"Error storing exercise in memory: {e}")

    async def _cleanup_exercise_sandbox(self, sandbox_id: str):
        """Dọn dẹp sandbox sau bài tập"""
        try:
            if self.sandbox_controller:
                await self.sandbox_controller.destroy_sandbox(sandbox_id)
        except Exception as e:
            self.logger.error(f"Error cleaning up sandbox {sandbox_id}: {e}")

    def get_exercise_statistics(self) -> dict[str, Any]:
        """Lấy thống kê bài tập"""
        return {
            "stats": self.stats.copy(),
            "scheduled_exercises": len(self.scheduled_exercises),
            "active_exercises": len(self.active_exercises),
            "completed_exercises": len(self.exercise_history),
            "success_rate": self.stats["completed_exercises"]
            / max(self.stats["total_exercises"], 1),
        }

    async def generate_exercise_report(self, exercise_id: str) -> dict[str, Any]:
        """Tạo báo cáo bài tập"""
        try:
            # Find exercise result
            result = None
            for r in self.exercise_history:
                if r.exercise_id == exercise_id:
                    result = r
                    break

            if not result:
                return {"error": "Exercise result not found"}

            # Generate report
            report = {
                "exercise_id": exercise_id,
                "summary": {
                    "overall_score": result.overall_score,
                    "status": result.status.value,
                    "duration": (result.end_time - result.start_time).total_seconds(),
                    "recommendations": result.recommendations,
                },
                "red_team_results": result.red_team_results,
                "blue_team_results": result.blue_team_results,
                "metadata": result.metadata,
                "generated_at": datetime.now().isoformat(),
            }

            return report

        except Exception as e:
            self.logger.error(f"Error generating exercise report: {e}")
            return {"error": str(e)}

    async def run_continuous_monitoring(self, interval: int = 300):
        """Chạy giám sát liên tục"""
        self.logger.info("Starting continuous monitoring...")

        while True:
            try:
                # Check for scheduled exercises
                current_time = datetime.now()
                for _exercise_id, exercise in list(self.scheduled_exercises.items()):
                    if (
                        exercise.scheduled_time <= current_time
                        and exercise.status == ExerciseStatus.SCHEDULED
                    ):
                        await self._execute_exercise(exercise)

                # Monitor active exercises
                for exercise_id, exercise in list(self.active_exercises.items()):
                    # Check for timeout
                    if (
                        current_time - exercise.scheduled_time
                    ).total_seconds() > exercise.duration_minutes * 60:
                        exercise.status = ExerciseStatus.FAILED
                        del self.active_exercises[exercise_id]
                        self.stats["failed_exercises"] += 1

                # Wait for next check
                await asyncio.sleep(interval)

            except Exception as e:
                self.logger.error(f"Error in continuous monitoring: {e}")
                await asyncio.sleep(interval)


# Demo và testing
async def demo_security_orchestrator():
    """Demo Security Orchestrator"""
    print("🎭 Security Orchestrator Demo")
    print("=" * 50)

    # Initialize orchestrator
    config = {
        "monitoring_interval": 60,
        "max_concurrent_exercises": 3,
        "default_duration": 30,
    }

    orchestrator = SecurityOrchestrator(config)

    # Create sample exercise
    exercise = SecurityExercise(
        id="demo_exercise_001",
        name="Demo Security Exercise",
        exercise_type=ExerciseType.COMBINED_EXERCISE,
        description="Demonstration of Red/Blue Team coordination",
        scheduled_time=datetime.now() + timedelta(seconds=5),
        duration_minutes=10,
        status=ExerciseStatus.SCHEDULED,
        red_team_config={
            "pattern_attacks": True,
            "ai_attacks": True,
            "adaptive_attacks": False,
        },
        blue_team_config={"anomaly_detection": True, "defense_execution": True},
        sandbox_config={
            "resources": {"cpu": "1", "memory": "512M"},
            "network": {"isolated": True},
            "security": {"strict": True},
        },
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    # Schedule exercise
    print("📅 Scheduling exercise...")
    success = await orchestrator.schedule_exercise(exercise)

    if success:
        print(f"✅ Exercise scheduled: {exercise.name}")

        # Wait for exercise to complete
        print("⏳ Waiting for exercise to complete...")
        await asyncio.sleep(15)

        # Generate report
        print("📊 Generating exercise report...")
        report = await orchestrator.generate_exercise_report(exercise.id)

        if "error" not in report:
            print(f"📈 Overall Score: {report['summary']['overall_score']:.2f}")
            print(f"📋 Recommendations: {len(report['summary']['recommendations'])}")
        else:
            print(f"❌ Error generating report: {report['error']}")

    # Show statistics
    stats = orchestrator.get_exercise_statistics()
    print("\n📊 Orchestrator Statistics:")
    print(f"  - Total exercises: {stats['stats']['total_exercises']}")
    print(f"  - Completed exercises: {stats['stats']['completed_exercises']}")
    print(f"  - Success rate: {stats['success_rate']:.2f}")
    print(f"  - Average score: {stats['stats']['average_score']:.2f}")


if __name__ == "__main__":
    asyncio.run(demo_security_orchestrator())
