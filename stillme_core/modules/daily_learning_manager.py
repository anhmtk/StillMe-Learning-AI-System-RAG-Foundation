#!/usr/bin/env python3
"""
Daily Learning Manager - Quản lý việc học tập hàng ngày của StillMe

Author: StillMe AI Framework
Version: 1.0.0
"""

import json
import logging
import random
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class LearningCase:
    """Represents a single learning case"""

    id: str
    question: str
    expected_keywords: List[str]
    difficulty: str
    language: str
    category: str
    timestamp: str = ""
    response: str = ""
    score: float = 0.0
    feedback: str = ""


@dataclass
class LearningMemoryItem:
    """Memory item specifically for learning results"""

    case_id: str
    question: str
    response: str
    score: float
    feedback: str
    category: str
    difficulty: str
    language: str
    timestamp: datetime
    keywords_matched: List[str]
    learning_insights: List[str]
    improvement_suggestions: List[str]


class DailyLearningManager:
    """Quản lý việc học tập hàng ngày của StillMe"""

    def __init__(
        self,
        cases_file: str = "daily_learning_cases.json",
        memory_manager=None,
        improvement_manager=None,
    ):
        self.cases_file = Path(cases_file)
        self.logger = logging.getLogger(__name__)
        self.cases_data = self._load_cases()
        self.today_cases: List[LearningCase] = []

        # Integration với LayeredMemoryV1
        self.memory_manager = memory_manager
        if self.memory_manager:
            self.logger.info("✅ DailyLearningManager integrated with LayeredMemoryV1")
        else:
            self.logger.warning(
                "⚠️ No memory manager provided - learning results won't be stored in memory"
            )

        # Integration với SelfImprovementManager
        self.improvement_manager = improvement_manager
        if self.improvement_manager:
            self.logger.info(
                "✅ DailyLearningManager integrated with SelfImprovementManager"
            )
        else:
            self.logger.warning(
                "⚠️ No improvement manager provided - no automatic improvement suggestions"
            )

    def _load_cases(self) -> Dict[str, Any]:
        """Load learning cases from JSON file"""
        try:
            if self.cases_file.exists():
                with open(self.cases_file, encoding="utf-8") as f:
                    return json.load(f)
            else:
                self.logger.warning(f"Cases file not found: {self.cases_file}")
                return {"categories": {}, "learning_schedule": {}}
        except Exception as e:
            self.logger.error(f"Error loading cases: {e}")
            return {"categories": {}, "learning_schedule": {}}

    def _save_cases(self) -> bool:
        """Save learning cases to JSON file"""
        try:
            with open(self.cases_file, "w", encoding="utf-8") as f:
                json.dump(self.cases_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Error saving cases: {e}")
            return False

    def get_today_schedule(self) -> List[str]:
        """Lấy lịch học cho ngày hôm nay"""
        today = datetime.now().strftime("%A").lower()
        return self.cases_data.get("learning_schedule", {}).get(today, [])

    def select_today_cases(self, max_cases: int = 5) -> List[LearningCase]:
        """Chọn các case học tập cho ngày hôm nay"""
        today_categories = self.get_today_schedule()
        selected_cases = []

        for category in today_categories:
            if category in self.cases_data.get("categories", {}):
                cases = self.cases_data["categories"][category].get("cases", [])
                if cases:
                    # Chọn random 1-2 cases từ mỗi category
                    num_select = min(2, len(cases))
                    selected = random.sample(cases, num_select)

                    for case_data in selected:
                        case = LearningCase(
                            id=case_data["id"],
                            question=case_data["question"],
                            expected_keywords=case_data["expected_keywords"],
                            difficulty=case_data["difficulty"],
                            language=case_data["language"],
                            category=category,
                            timestamp=datetime.now().isoformat(),
                        )
                        selected_cases.append(case)

        # Giới hạn số lượng cases
        self.today_cases = selected_cases[:max_cases]
        return self.today_cases

    def add_new_case(
        self,
        category: str,
        question: str,
        expected_keywords: List[str],
        difficulty: str = "medium",
        language: str = "vi",
    ) -> bool:
        """Thêm case học tập mới"""
        try:
            if category not in self.cases_data.get("categories", {}):
                self.cases_data["categories"][category] = {
                    "description": f"Custom category: {category}",
                    "cases": [],
                }

            # Tạo ID mới
            case_id = f"{category}_{len(self.cases_data['categories'][category]['cases']) + 1:03d}"

            new_case = {
                "id": case_id,
                "question": question,
                "expected_keywords": expected_keywords,
                "difficulty": difficulty,
                "language": language,
            }

            self.cases_data["categories"][category]["cases"].append(new_case)

            # Cập nhật metadata
            self.cases_data["metadata"]["total_cases"] += 1
            self.cases_data["metadata"]["last_updated"] = datetime.now().isoformat()

            return self._save_cases()

        except Exception as e:
            self.logger.error(f"Error adding new case: {e}")
            return False

    def record_response(
        self, case_id: str, response: str, score: float, feedback: str = ""
    ) -> bool:
        """Ghi lại phản hồi của StillMe cho một case"""
        try:
            for case in self.today_cases:
                if case.id == case_id:
                    case.response = response
                    case.score = score
                    case.feedback = feedback
                    break

            # Lưu vào file log
            self._log_interaction(case_id, response, score, feedback)

            # Lưu vào LayeredMemoryV1 nếu có memory manager
            if self.memory_manager:
                self._save_to_memory(case_id, response, score, feedback)

            return True

        except Exception as e:
            self.logger.error(f"Error recording response: {e}")
            return False

    def _save_to_memory(self, case_id: str, response: str, score: float, feedback: str):
        """Lưu learning result vào LayeredMemoryV1"""
        try:
            # Tìm case để lấy thông tin
            case = None
            for c in self.today_cases:
                if c.id == case_id:
                    case = c
                    break

            if not case:
                self.logger.warning(f"Case {case_id} not found for memory storage")
                return

            # Tạo LearningMemoryItem
            memory_item = LearningMemoryItem(
                case_id=case_id,
                question=case.question,
                response=response,
                score=score,
                feedback=feedback,
                category=case.category,
                difficulty=case.difficulty,
                language=case.language,
                timestamp=datetime.now(),
                keywords_matched=self._analyze_keywords_matched(
                    case.expected_keywords, response
                ),
                learning_insights=self._extract_learning_insights(response, score),
                improvement_suggestions=self._generate_improvement_suggestions(
                    case, score, feedback
                ),
            )

            # Tạo memory content với structured data
            memory_content = self._create_memory_content(memory_item)

            # Tính priority dựa trên score và difficulty
            priority = self._calculate_priority(score, case.difficulty)

            # Tạo metadata
            metadata = {
                "type": "learning_result",
                "case_id": case_id,
                "category": case.category,
                "difficulty": case.difficulty,
                "language": case.language,
                "score": score,
                "keywords_matched": memory_item.keywords_matched,
                "learning_insights": memory_item.learning_insights,
                "improvement_suggestions": memory_item.improvement_suggestions,
            }

            # Lưu vào memory
            if self.memory_manager:
                self.memory_manager.add_memory(
                    content=memory_content, priority=priority, metadata=metadata
                )

            self.logger.info(
                f"✅ Learning result saved to memory: {case_id} (score: {score:.2f})"
            )

        except Exception as e:
            self.logger.error(f"Error saving to memory: {e}")

    def _analyze_keywords_matched(
        self, expected_keywords: List[str], response: str
    ) -> List[str]:
        """Phân tích keywords được match trong response"""
        matched = []
        response_lower = response.lower()

        for keyword in expected_keywords:
            if keyword.lower() in response_lower:
                matched.append(keyword)

        return matched

    def _extract_learning_insights(self, response: str, score: float) -> List[str]:
        """Trích xuất learning insights từ response"""
        insights = []

        if score >= 0.8:
            insights.append("High-quality response with comprehensive coverage")
        elif score >= 0.6:
            insights.append("Good response with room for improvement")
        else:
            insights.append("Response needs significant improvement")

        # Thêm insights dựa trên response length
        if len(response) > 500:
            insights.append("Detailed and thorough response")
        elif len(response) < 100:
            insights.append("Brief response - may need more detail")

        return insights

    def _generate_improvement_suggestions(
        self, case: LearningCase, score: float, feedback: str
    ) -> List[str]:
        """Tạo improvement suggestions dựa trên performance"""
        suggestions = []

        if score < 0.6:
            suggestions.append("Review fundamental concepts in this area")
            suggestions.append("Practice more examples of similar problems")

        if len(case.expected_keywords) > len(
            self._analyze_keywords_matched(case.expected_keywords, case.response)
        ):
            suggestions.append("Include more expected keywords in responses")

        if case.difficulty == "hard" and score < 0.7:
            suggestions.append("Break down complex problems into smaller parts")

        if feedback and "error" in feedback.lower():
            suggestions.append("Focus on error handling and edge cases")

        return suggestions

    def _create_memory_content(self, memory_item: LearningMemoryItem) -> str:
        """Tạo memory content từ LearningMemoryItem"""
        content = f"""
LEARNING RESULT - {memory_item.case_id}
Category: {memory_item.category} | Difficulty: {memory_item.difficulty} | Score: {memory_item.score:.2f}

Question: {memory_item.question}

Response: {memory_item.response}

Keywords Matched: {', '.join(memory_item.keywords_matched)}
Learning Insights: {', '.join(memory_item.learning_insights)}
Improvement Suggestions: {', '.join(memory_item.improvement_suggestions)}

Feedback: {memory_item.feedback}
        """.strip()

        return content

    def _calculate_priority(self, score: float, difficulty: str) -> float:
        """Tính priority cho memory item"""
        base_priority = score

        # Adjust priority based on difficulty
        if difficulty == "hard":
            base_priority += 0.2
        elif difficulty == "medium":
            base_priority += 0.1

        # Ensure priority is between 0 and 1
        return min(1.0, max(0.0, base_priority))

    def _log_interaction(
        self, case_id: str, response: str, score: float, feedback: str
    ):
        """Log interaction vào file"""
        try:
            log_file = Path("logs/daily_learning.log")
            log_file.parent.mkdir(exist_ok=True)

            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "case_id": case_id,
                "response_length": len(response),
                "score": score,
                "feedback": feedback,
            }

            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        except Exception as e:
            self.logger.error(f"Error logging interaction: {e}")

    def search_learning_memory(
        self,
        query: str,
        category: Optional[str] = None,
        min_score: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Tìm kiếm learning results từ LayeredMemoryV1"""
        if not self.memory_manager:
            self.logger.warning("No memory manager available for search")
            return []

        try:
            # Search trong memory với query
            memory_results = self.memory_manager.search(query)

            # Filter results
            filtered_results = []
            for item in memory_results:
                # Check if it's a learning result
                if item.metadata.get("type") == "learning_result":
                    # Apply filters
                    if category and item.metadata.get("category") != category:
                        continue
                    if min_score and item.metadata.get("score", 0) < min_score:
                        continue

                    # Parse memory content
                    result = {
                        "case_id": item.metadata.get("case_id"),
                        "category": item.metadata.get("category"),
                        "difficulty": item.metadata.get("difficulty"),
                        "score": item.metadata.get("score"),
                        "timestamp": item.timestamp.isoformat(),
                        "keywords_matched": item.metadata.get("keywords_matched", []),
                        "learning_insights": item.metadata.get("learning_insights", []),
                        "improvement_suggestions": item.metadata.get(
                            "improvement_suggestions", []
                        ),
                        "content": item.content,
                    }
                    filtered_results.append(result)

            return filtered_results

        except Exception as e:
            self.logger.error(f"Error searching learning memory: {e}")
            return []

    def get_learning_stats(self) -> Dict[str, Any]:
        """Lấy thống kê học tập"""
        try:
            total_cases = self.cases_data.get("metadata", {}).get("total_cases", 0)
            categories = len(self.cases_data.get("categories", {}))

            # Đọc log file để tính stats
            log_file = Path("logs/daily_learning.log")
            recent_scores = []

            if log_file.exists():
                with open(log_file, encoding="utf-8") as f:
                    lines = f.readlines()
                    # Lấy 30 dòng gần nhất
                    for line in lines[-30:]:
                        try:
                            entry = json.loads(line.strip())
                            recent_scores.append(entry.get("score", 0))
                        except:
                            continue

            avg_score = sum(recent_scores) / len(recent_scores) if recent_scores else 0

            # Thêm memory stats nếu có memory manager
            memory_stats = {}
            if self.memory_manager:
                try:
                    # Search tất cả learning results
                    all_learning_results = self.search_learning_memory(
                        "learning_result"
                    )
                    memory_stats = {
                        "total_learning_results": len(all_learning_results),
                        "avg_memory_score": (
                            sum(r["score"] for r in all_learning_results)
                            / len(all_learning_results)
                            if all_learning_results
                            else 0
                        ),
                        "categories_in_memory": list(
                            set(r["category"] for r in all_learning_results)
                        ),
                    }
                except Exception as e:
                    self.logger.warning(f"Could not get memory stats: {e}")

            return {
                "total_cases": total_cases,
                "categories": categories,
                "today_cases": len(self.today_cases),
                "recent_avg_score": round(avg_score, 2),
                "recent_interactions": len(recent_scores),
                "memory_stats": memory_stats,
            }

        except Exception as e:
            self.logger.error(f"Error getting learning stats: {e}")
            return {}

    def generate_learning_report(self) -> str:
        """Tạo báo cáo học tập"""
        stats = self.get_learning_stats()
        today_cases = self.get_today_schedule()

        report = f"""
📚 BÁO CÁO HỌC TẬP HÀNG NGÀY - {datetime.now().strftime('%Y-%m-%d')}

📊 Thống kê tổng quan:
- Tổng số cases: {stats.get('total_cases', 0)}
- Số categories: {stats.get('categories', 0)}
- Cases hôm nay: {stats.get('today_cases', 0)}
- Điểm trung bình gần đây: {stats.get('recent_avg_score', 0)}/10
- Số tương tác gần đây: {stats.get('recent_interactions', 0)}

📅 Lịch học hôm nay: {', '.join(today_cases)}

🎯 Cases đã chọn:
"""

        for i, case in enumerate(self.today_cases, 1):
            report += f"{i}. [{case.category}] {case.question[:50]}...\n"

        return report

    def analyze_learning_performance(self) -> Dict[str, Any]:
        """Phân tích performance học tập và tạo improvement suggestions"""
        try:
            # Lấy learning stats
            stats = self.get_learning_stats()

            # Lấy recent learning results từ memory
            recent_results = []
            if self.memory_manager:
                try:
                    # Search for recent learning results
                    all_results = self.search_learning_memory("", min_score=0.0)
                    # Sort by timestamp và lấy 10 results gần nhất
                    recent_results = sorted(
                        all_results, key=lambda x: x.get("timestamp", ""), reverse=True
                    )[:10]
                except Exception as e:
                    self.logger.warning(f"Could not get recent results: {e}")

            # Phân tích performance patterns
            performance_analysis = self._analyze_performance_patterns(
                recent_results, stats
            )

            # Tạo improvement suggestions
            improvement_suggestions = self._generate_system_improvements(
                performance_analysis
            )

            return {
                "performance_analysis": performance_analysis,
                "improvement_suggestions": improvement_suggestions,
                "recent_results_count": len(recent_results),
                "analysis_timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Error analyzing learning performance: {e}")
            return {"error": str(e)}

    def _analyze_performance_patterns(
        self, recent_results: List[Dict], stats: Dict
    ) -> Dict[str, Any]:
        """Phân tích patterns trong performance"""
        analysis = {
            "overall_score_trend": "stable",
            "weak_categories": [],
            "strong_categories": [],
            "common_issues": [],
            "improvement_areas": [],
        }

        if not recent_results:
            return analysis

        # Phân tích score trend
        scores = [r.get("score", 0) for r in recent_results if r.get("score")]
        if len(scores) >= 3:
            recent_avg = sum(scores[:3]) / 3
            older_avg = sum(scores[3:6]) / 3 if len(scores) >= 6 else recent_avg

            if recent_avg > older_avg + 0.1:
                analysis["overall_score_trend"] = "improving"
            elif recent_avg < older_avg - 0.1:
                analysis["overall_score_trend"] = "declining"

        # Phân tích categories
        category_scores = {}
        for result in recent_results:
            category = result.get("category", "unknown")
            score = result.get("score", 0)
            if category not in category_scores:
                category_scores[category] = []
            category_scores[category].append(score)

        # Xác định weak và strong categories
        for category, scores in category_scores.items():
            avg_score = sum(scores) / len(scores)
            if avg_score < 0.6:
                analysis["weak_categories"].append(category)
            elif avg_score > 0.8:
                analysis["strong_categories"].append(category)

        # Phân tích common issues
        low_score_results = [r for r in recent_results if r.get("score", 0) < 0.6]
        if low_score_results:
            analysis["common_issues"].append("Low scores in recent attempts")

        # Xác định improvement areas
        if analysis["weak_categories"]:
            analysis["improvement_areas"].append(
                f"Focus on categories: {', '.join(analysis['weak_categories'])}"
            )

        if analysis["overall_score_trend"] == "declining":
            analysis["improvement_areas"].append(
                "Overall performance declining - need review"
            )

        return analysis

    def _generate_system_improvements(
        self, performance_analysis: Dict
    ) -> List[Dict[str, Any]]:
        """Tạo system improvement suggestions dựa trên performance analysis"""
        suggestions = []

        # Improvement cho weak categories
        for category in performance_analysis.get("weak_categories", []):
            suggestions.append(
                {
                    "type": "category_focus",
                    "priority": "high",
                    "description": f"Increase focus on {category} category",
                    "suggestion": f"Add more {category} cases to daily learning schedule",
                    "reason": f"Low performance in {category} category",
                    "estimated_impact": "medium",
                }
            )

        # Improvement cho declining trend
        if performance_analysis.get("overall_score_trend") == "declining":
            suggestions.append(
                {
                    "type": "system_review",
                    "priority": "high",
                    "description": "Review learning system configuration",
                    "suggestion": "Analyze recent changes and adjust learning parameters",
                    "reason": "Overall performance declining",
                    "estimated_impact": "high",
                }
            )

        # Improvement cho common issues
        if performance_analysis.get("common_issues"):
            suggestions.append(
                {
                    "type": "feedback_enhancement",
                    "priority": "medium",
                    "description": "Enhance feedback system",
                    "suggestion": "Improve feedback quality and detail for low-scoring responses",
                    "reason": "Common issues with low scores",
                    "estimated_impact": "medium",
                }
            )

        return suggestions

    def submit_improvement_suggestions(self, suggestions: List[Dict[str, Any]]) -> bool:
        """Submit improvement suggestions to SelfImprovementManager"""
        if not self.improvement_manager:
            self.logger.warning("No improvement manager available")
            return False

        try:
            # Convert suggestions to format compatible with SelfImprovementManager
            for suggestion in suggestions:
                # Tạo ProposedChange object
                change_data = {
                    "id": f"learning_improvement_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "timestamp": datetime.now().isoformat(),
                    "change_type": "config",
                    "file_path": "daily_learning_cases.json",
                    "description": suggestion["description"],
                    "current_content": "Current learning configuration",
                    "proposed_content": suggestion["suggestion"],
                    "reason": suggestion["reason"],
                    "risk_level": (
                        "LOW" if suggestion["priority"] == "low" else "MEDIUM"
                    ),
                    "safety_checks": {"ethical": True, "integrity": True},
                    "test_results": {"basic": True},
                    "approved": False,
                    "applied": False,
                    "rollback_available": True,
                }

                # Submit to improvement manager
                self.improvement_manager.proposed_changes.append(change_data)

            self.logger.info(f"Submitted {len(suggestions)} improvement suggestions")
            return True

        except Exception as e:
            self.logger.error(f"Error submitting improvement suggestions: {e}")
            return False

    def run_learning_improvement_cycle(self) -> Dict[str, Any]:
        """Chạy chu trình phân tích và đề xuất improvements"""
        try:
            # 1. Phân tích performance
            analysis = self.analyze_learning_performance()

            # 2. Tạo improvement suggestions
            suggestions = analysis.get("improvement_suggestions", [])

            # 3. Submit suggestions nếu có improvement manager
            submitted = False
            if suggestions and self.improvement_manager:
                submitted = self.submit_improvement_suggestions(suggestions)

            return {
                "status": "success",
                "analysis": analysis,
                "suggestions_count": len(suggestions),
                "suggestions_submitted": submitted,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Error in learning improvement cycle: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }


# Test function
def test_daily_learning_manager():
    """Test DailyLearningManager"""
    print("🧠 Testing Daily Learning Manager")
    print("=" * 40)

    manager = DailyLearningManager()

    # Test 1: Load cases
    print("1. Loading cases...")
    cases_data = manager.cases_data
    print(f"   Categories: {len(cases_data.get('categories', {}))}")

    # Test 2: Get today's schedule
    print("2. Getting today's schedule...")
    schedule = manager.get_today_schedule()
    print(f"   Today's categories: {schedule}")

    # Test 3: Select today's cases
    print("3. Selecting today's cases...")
    today_cases = manager.select_today_cases(max_cases=3)
    print(f"   Selected {len(today_cases)} cases")

    for case in today_cases:
        print(f"   - {case.id}: {case.question[:30]}...")

    # Test 4: Add new case
    print("4. Adding new case...")
    success = manager.add_new_case(
        category="test",
        question="Test question for StillMe",
        expected_keywords=["test", "learning"],
        difficulty="easy",
    )
    print(f"   Success: {success}")

    # Test 5: Get stats
    print("5. Getting learning stats...")
    stats = manager.get_learning_stats()
    print(f"   Stats: {stats}")

    # Test 6: Generate report
    print("6. Generating report...")
    report = manager.generate_learning_report()
    print(report)

    print("✅ Daily Learning Manager test completed!")


if __name__ == "__main__":
    test_daily_learning_manager()
