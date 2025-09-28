"""
🎯 StillMe Learning Assessment System
===================================

Hệ thống đánh giá và kiểm tra việc học của StillMe.
Fine-tune kiểu nhà nghèo: Tối ưu hóa parameters dựa trên performance
mà không cần GPU hay tài nguyên lớn.

Tính năng:
- Self-assessment: Tự đánh giá bản thân
- Performance tracking: Theo dõi hiệu suất
- Parameter optimization: Tối ưu hóa tham số
- Knowledge validation: Kiểm tra kiến thức
- Learning curve analysis: Phân tích đường cong học tập

Author: StillMe AI Framework
Version: 2.0.0
Date: 2025-09-27
"""

import asyncio
import json
import logging
import math
import statistics
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import numpy as np
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class AssessmentType(Enum):
    """Loại đánh giá"""
    QUICK = "quick"           # Đánh giá nhanh (5 phút)
    STANDARD = "standard"     # Đánh giá chuẩn (15 phút)
    COMPREHENSIVE = "comprehensive"  # Đánh giá toàn diện (30 phút)
    CUSTOM = "custom"         # Đánh giá tùy chỉnh

class AssessmentCategory(Enum):
    """Danh mục đánh giá"""
    KNOWLEDGE = "knowledge"           # Kiến thức
    REASONING = "reasoning"           # Lý luận
    CREATIVITY = "creativity"         # Sáng tạo
    CONSISTENCY = "consistency"       # Nhất quán
    ADAPTATION = "adaptation"         # Thích ứng
    PERFORMANCE = "performance"       # Hiệu suất

@dataclass
class AssessmentResult:
    """Kết quả đánh giá"""
    assessment_id: str
    timestamp: float
    assessment_type: AssessmentType
    category: AssessmentCategory
    score: float  # 0.0 - 1.0
    max_possible_score: float
    questions_answered: int
    correct_answers: int
    time_taken_seconds: float
    detailed_results: Dict[str, Any]
    recommendations: List[str]
    improvement_areas: List[str]

@dataclass
class LearningCurve:
    """Đường cong học tập"""
    timestamps: List[float]
    scores: List[float]
    trend: str  # "improving", "stable", "declining"
    slope: float
    r_squared: float
    volatility: float

@dataclass
class ParameterOptimization:
    """Tối ưu hóa tham số"""
    parameter_name: str
    current_value: float
    optimal_value: float
    improvement_potential: float
    confidence: float
    adjustment_recommendation: str

class LearningAssessmentSystem:
    """
    Hệ thống đánh giá học tập của StillMe
    
    Fine-tune kiểu nhà nghèo:
    - Sử dụng statistical analysis thay vì deep learning
    - Gradient-free optimization
    - Rule-based parameter adjustment
    - Performance-based learning rate adaptation
    """
    
    def __init__(self, assessment_db_path: str = ".learning_assessment.db"):
        self.assessment_db_path = assessment_db_path
        self.logger = logging.getLogger(__name__)
        
        # Assessment data
        self.assessment_history = []
        self.learning_curves = {}
        self.parameter_optimizations = {}
        
        # Performance tracking
        self.performance_metrics = defaultdict(list)
        self.knowledge_validation_results = []
        
        # Optimization state
        self.current_parameters = {
            'learning_rate': 0.1,
            'confidence_threshold': 0.7,
            'creativity_factor': 0.5,
            'consistency_weight': 0.8,
            'adaptation_speed': 0.6,
            'knowledge_retention': 0.9
        }
        
        # Load existing data
        self._load_assessment_data()
        
        self.logger.info("Learning Assessment System initialized")
    
    async def run_assessment(self, 
                           assessment_type: AssessmentType = AssessmentType.STANDARD,
                           category: AssessmentCategory = AssessmentCategory.KNOWLEDGE) -> AssessmentResult:
        """
        Chạy đánh giá học tập
        
        Args:
            assessment_type: Loại đánh giá
            category: Danh mục đánh giá
            
        Returns:
            AssessmentResult: Kết quả đánh giá
        """
        assessment_id = f"assessment_{int(time.time())}"
        start_time = time.time()
        
        self.logger.info(f"Starting {assessment_type.value} assessment for {category.value}")
        
        # Generate questions based on type and category
        questions = self._generate_questions(assessment_type, category)
        
        # Run assessment
        results = await self._run_questions(questions, category)
        
        # Calculate score
        score = self._calculate_score(results)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(results, category)
        
        # Identify improvement areas
        improvement_areas = self._identify_improvement_areas(results, category)
        
        # Create assessment result
        time_taken = time.time() - start_time
        result = AssessmentResult(
            assessment_id=assessment_id,
            timestamp=start_time,
            assessment_type=assessment_type,
            category=category,
            score=score,
            max_possible_score=len(questions),
            questions_answered=len(questions),
            correct_answers=results['correct_count'],
            time_taken_seconds=time_taken,
            detailed_results=results,
            recommendations=recommendations,
            improvement_areas=improvement_areas
        )
        
        # Store result
        self.assessment_history.append(result)
        self._update_performance_metrics(result)
        self._update_learning_curve(category, result)
        
        # Save to database
        await self._save_assessment_result(result)
        
        self.logger.info(f"Assessment completed: {assessment_id}, Score: {score:.2f}")
        return result
    
    def _generate_questions(self, assessment_type: AssessmentType, category: AssessmentCategory) -> List[Dict[str, Any]]:
        """Generate questions based on assessment type and category"""
        questions = []
        
        # Determine number of questions based on type
        question_counts = {
            AssessmentType.QUICK: 5,
            AssessmentType.STANDARD: 15,
            AssessmentType.COMPREHENSIVE: 30,
            AssessmentType.CUSTOM: 10
        }
        
        num_questions = question_counts.get(assessment_type, 10)
        
        # Generate questions based on category
        if category == AssessmentCategory.KNOWLEDGE:
            questions = self._generate_knowledge_questions(num_questions)
        elif category == AssessmentCategory.REASONING:
            questions = self._generate_reasoning_questions(num_questions)
        elif category == AssessmentCategory.CREATIVITY:
            questions = self._generate_creativity_questions(num_questions)
        elif category == AssessmentCategory.CONSISTENCY:
            questions = self._generate_consistency_questions(num_questions)
        elif category == AssessmentCategory.ADAPTATION:
            questions = self._generate_adaptation_questions(num_questions)
        elif category == AssessmentCategory.PERFORMANCE:
            questions = self._generate_performance_questions(num_questions)
        
        return questions
    
    def _generate_knowledge_questions(self, count: int) -> List[Dict[str, Any]]:
        """Generate knowledge-based questions"""
        questions = [
            {
                'id': 'knowledge_1',
                'question': 'What is the capital of Vietnam?',
                'options': ['Hanoi', 'Ho Chi Minh City', 'Da Nang', 'Hue'],
                'correct_answer': 0,
                'difficulty': 'easy',
                'category': 'geography'
            },
            {
                'id': 'knowledge_2',
                'question': 'What is the largest planet in our solar system?',
                'options': ['Earth', 'Jupiter', 'Saturn', 'Neptune'],
                'correct_answer': 1,
                'difficulty': 'medium',
                'category': 'astronomy'
            },
            {
                'id': 'knowledge_3',
                'question': 'Who wrote "Romeo and Juliet"?',
                'options': ['Charles Dickens', 'William Shakespeare', 'Mark Twain', 'Jane Austen'],
                'correct_answer': 1,
                'difficulty': 'medium',
                'category': 'literature'
            },
            {
                'id': 'knowledge_4',
                'question': 'What is the chemical symbol for gold?',
                'options': ['Go', 'Gd', 'Au', 'Ag'],
                'correct_answer': 2,
                'difficulty': 'easy',
                'category': 'chemistry'
            },
            {
                'id': 'knowledge_5',
                'question': 'In which year did World War II end?',
                'options': ['1944', '1945', '1946', '1947'],
                'correct_answer': 1,
                'difficulty': 'medium',
                'category': 'history'
            }
        ]
        
        # Return requested number of questions
        return questions[:count]
    
    def _generate_reasoning_questions(self, count: int) -> List[Dict[str, Any]]:
        """Generate reasoning-based questions"""
        questions = [
            {
                'id': 'reasoning_1',
                'question': 'If all roses are flowers and some flowers are red, can we conclude that some roses are red?',
                'options': ['Yes', 'No', 'Maybe', 'Cannot determine'],
                'correct_answer': 0,
                'difficulty': 'medium',
                'category': 'logic'
            },
            {
                'id': 'reasoning_2',
                'question': 'A train travels 120 km in 2 hours. What is its average speed?',
                'options': ['60 km/h', '120 km/h', '240 km/h', '30 km/h'],
                'correct_answer': 0,
                'difficulty': 'easy',
                'category': 'mathematics'
            },
            {
                'id': 'reasoning_3',
                'question': 'If it is raining, then the ground is wet. The ground is wet. Can we conclude it is raining?',
                'options': ['Yes', 'No', 'Maybe', 'Cannot determine'],
                'correct_answer': 1,
                'difficulty': 'medium',
                'category': 'logic'
            }
        ]
        
        return questions[:count]
    
    def _generate_creativity_questions(self, count: int) -> List[Dict[str, Any]]:
        """Generate creativity-based questions"""
        questions = [
            {
                'id': 'creativity_1',
                'question': 'How many uses can you think of for a paperclip?',
                'type': 'open_ended',
                'difficulty': 'medium',
                'category': 'divergent_thinking'
            },
            {
                'id': 'creativity_2',
                'question': 'Create a story title that combines "robot" and "garden"',
                'type': 'open_ended',
                'difficulty': 'easy',
                'category': 'creative_writing'
            },
            {
                'id': 'creativity_3',
                'question': 'What would happen if gravity worked backwards?',
                'type': 'open_ended',
                'difficulty': 'hard',
                'category': 'imagination'
            }
        ]
        
        return questions[:count]
    
    def _generate_consistency_questions(self, count: int) -> List[Dict[str, Any]]:
        """Generate consistency-based questions"""
        questions = [
            {
                'id': 'consistency_1',
                'question': 'What is 2 + 2?',
                'options': ['3', '4', '5', '6'],
                'correct_answer': 1,
                'difficulty': 'easy',
                'category': 'basic_math'
            },
            {
                'id': 'consistency_2',
                'question': 'What is the color of the sky on a clear day?',
                'options': ['Red', 'Blue', 'Green', 'Yellow'],
                'correct_answer': 1,
                'difficulty': 'easy',
                'category': 'basic_knowledge'
            }
        ]
        
        return questions[:count]
    
    def _generate_adaptation_questions(self, count: int) -> List[Dict[str, Any]]:
        """Generate adaptation-based questions"""
        questions = [
            {
                'id': 'adaptation_1',
                'question': 'If you learned that a previously correct answer is now wrong, how would you adapt?',
                'type': 'open_ended',
                'difficulty': 'medium',
                'category': 'learning_adaptation'
            },
            {
                'id': 'adaptation_2',
                'question': 'How would you handle conflicting information from two reliable sources?',
                'type': 'open_ended',
                'difficulty': 'hard',
                'category': 'conflict_resolution'
            }
        ]
        
        return questions[:count]
    
    def _generate_performance_questions(self, count: int) -> List[Dict[str, Any]]:
        """Generate performance-based questions"""
        questions = [
            {
                'id': 'performance_1',
                'question': 'How quickly can you solve: 15 × 8 = ?',
                'options': ['120', '130', '140', '150'],
                'correct_answer': 0,
                'difficulty': 'easy',
                'category': 'speed_math'
            },
            {
                'id': 'performance_2',
                'question': 'What is the next number in the sequence: 2, 4, 8, 16, ?',
                'options': ['24', '32', '40', '48'],
                'correct_answer': 1,
                'difficulty': 'medium',
                'category': 'pattern_recognition'
            }
        ]
        
        return questions[:count]
    
    async def _run_questions(self, questions: List[Dict[str, Any]], category: AssessmentCategory) -> Dict[str, Any]:
        """Run questions and collect answers"""
        results = {
            'questions': questions,
            'answers': [],
            'correct_count': 0,
            'total_time': 0,
            'category_scores': defaultdict(int),
            'difficulty_scores': defaultdict(int)
        }
        
        start_time = time.time()
        
        for question in questions:
            question_start = time.time()
            
            # Simulate answering (in real implementation, this would be actual AI response)
            answer = await self._simulate_answer(question, category)
            
            question_time = time.time() - question_start
            
            # Check if answer is correct
            is_correct = self._check_answer(question, answer)
            
            if is_correct:
                results['correct_count'] += 1
                results['category_scores'][question.get('category', 'unknown')] += 1
                results['difficulty_scores'][question.get('difficulty', 'unknown')] += 1
            
            results['answers'].append({
                'question_id': question['id'],
                'answer': answer,
                'is_correct': is_correct,
                'time_taken': question_time
            })
            
            results['total_time'] += question_time
        
        return results
    
    async def _simulate_answer(self, question: Dict[str, Any], category: AssessmentCategory) -> Any:
        """Simulate AI answering a question"""
        # This is a simulation - in real implementation, this would call the actual AI
        
        # Simulate thinking time based on difficulty
        difficulty_times = {
            'easy': 0.1,
            'medium': 0.3,
            'hard': 0.5
        }
        
        thinking_time = difficulty_times.get(question.get('difficulty', 'medium'), 0.3)
        await asyncio.sleep(thinking_time)
        
        # Simulate answer based on current parameters and category
        if question.get('type') == 'open_ended':
            # For open-ended questions, simulate creativity score
            creativity_score = self.current_parameters.get('creativity_factor', 0.5)
            if np.random.random() < creativity_score:
                return f"Creative answer for {question['id']}"
            else:
                return f"Standard answer for {question['id']}"
        else:
            # For multiple choice, simulate accuracy based on confidence threshold
            confidence = self.current_parameters.get('confidence_threshold', 0.7)
            if np.random.random() < confidence:
                return question.get('correct_answer', 0)
            else:
                # Return wrong answer
                options = question.get('options', [])
                wrong_answers = [i for i in range(len(options)) if i != question.get('correct_answer', 0)]
                return np.random.choice(wrong_answers) if wrong_answers else 0
    
    def _check_answer(self, question: Dict[str, Any], answer: Any) -> bool:
        """Check if answer is correct"""
        if question.get('type') == 'open_ended':
            # For open-ended questions, use a simple heuristic
            return len(str(answer)) > 10  # Assume longer answers are better
        else:
            correct_answer = question.get('correct_answer')
            return answer == correct_answer
    
    def _calculate_score(self, results: Dict[str, Any]) -> float:
        """Calculate overall score"""
        total_questions = len(results['questions'])
        correct_answers = results['correct_count']
        
        if total_questions == 0:
            return 0.0
        
        return correct_answers / total_questions
    
    def _generate_recommendations(self, results: Dict[str, Any], category: AssessmentCategory) -> List[str]:
        """Generate recommendations based on results"""
        recommendations = []
        score = self._calculate_score(results)
        
        if score < 0.6:
            recommendations.append("Focus on fundamental knowledge building")
            recommendations.append("Increase practice frequency")
        elif score < 0.8:
            recommendations.append("Continue current learning approach")
            recommendations.append("Focus on weak areas identified")
        else:
            recommendations.append("Excellent performance - consider advanced topics")
            recommendations.append("Share knowledge with others")
        
        # Category-specific recommendations
        if category == AssessmentCategory.CREATIVITY:
            if score < 0.7:
                recommendations.append("Practice divergent thinking exercises")
                recommendations.append("Explore creative writing and art")
        
        return recommendations
    
    def _identify_improvement_areas(self, results: Dict[str, Any], category: AssessmentCategory) -> List[str]:
        """Identify areas for improvement"""
        improvement_areas = []
        
        # Analyze category scores
        for cat, score in results['category_scores'].items():
            if score == 0:  # No correct answers in this category
                improvement_areas.append(f"Improve {cat} knowledge")
        
        # Analyze difficulty scores
        for difficulty, score in results['difficulty_scores'].items():
            if difficulty == 'hard' and score == 0:
                improvement_areas.append("Focus on advanced topics")
        
        return improvement_areas
    
    def _update_performance_metrics(self, result: AssessmentResult):
        """Update performance metrics"""
        self.performance_metrics[result.category.value].append({
            'timestamp': result.timestamp,
            'score': result.score,
            'time_taken': result.time_taken_seconds
        })
    
    def _update_learning_curve(self, category: AssessmentCategory, result: AssessmentResult):
        """Update learning curve for category"""
        if category.value not in self.learning_curves:
            self.learning_curves[category.value] = LearningCurve(
                timestamps=[],
                scores=[],
                trend="stable",
                slope=0.0,
                r_squared=0.0,
                volatility=0.0
            )
        
        curve = self.learning_curves[category.value]
        curve.timestamps.append(result.timestamp)
        curve.scores.append(result.score)
        
        # Calculate trend and statistics
        if len(curve.scores) >= 3:
            curve.trend = self._calculate_trend(curve.scores)
            curve.slope = self._calculate_slope(curve.timestamps, curve.scores)
            curve.r_squared = self._calculate_r_squared(curve.timestamps, curve.scores)
            curve.volatility = self._calculate_volatility(curve.scores)
    
    def _calculate_trend(self, scores: List[float]) -> str:
        """Calculate trend from scores"""
        if len(scores) < 3:
            return "stable"
        
        recent_scores = scores[-3:]
        if recent_scores[-1] > recent_scores[0]:
            return "improving"
        elif recent_scores[-1] < recent_scores[0]:
            return "declining"
        else:
            return "stable"
    
    def _calculate_slope(self, timestamps: List[float], scores: List[float]) -> float:
        """Calculate slope of learning curve"""
        if len(timestamps) < 2:
            return 0.0
        
        # Simple linear regression
        n = len(timestamps)
        sum_x = sum(timestamps)
        sum_y = sum(scores)
        sum_xy = sum(x * y for x, y in zip(timestamps, scores))
        sum_x2 = sum(x * x for x in timestamps)
        
        if n * sum_x2 - sum_x * sum_x == 0:
            return 0.0
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        return slope
    
    def _calculate_r_squared(self, timestamps: List[float], scores: List[float]) -> float:
        """Calculate R-squared for learning curve"""
        if len(timestamps) < 3:
            return 0.0
        
        # Calculate linear regression
        slope = self._calculate_slope(timestamps, scores)
        intercept = statistics.mean(scores) - slope * statistics.mean(timestamps)
        
        # Calculate predicted values
        predicted = [slope * x + intercept for x in timestamps]
        
        # Calculate R-squared
        ss_res = sum((y - pred) ** 2 for y, pred in zip(scores, predicted))
        ss_tot = sum((y - statistics.mean(scores)) ** 2 for y in scores)
        
        if ss_tot == 0:
            return 0.0
        
        r_squared = 1 - (ss_res / ss_tot)
        return max(0.0, r_squared)
    
    def _calculate_volatility(self, scores: List[float]) -> float:
        """Calculate volatility of scores"""
        if len(scores) < 2:
            return 0.0
        
        return statistics.stdev(scores) if len(scores) > 1 else 0.0
    
    async def optimize_parameters(self) -> List[ParameterOptimization]:
        """
        Optimize parameters based on performance data
        
        Fine-tune kiểu nhà nghèo:
        - Statistical analysis thay vì gradient descent
        - Rule-based parameter adjustment
        - Performance correlation analysis
        """
        optimizations = []
        
        # Analyze each parameter
        for param_name, current_value in self.current_parameters.items():
            optimization = self._optimize_parameter(param_name, current_value)
            if optimization:
                optimizations.append(optimization)
        
        # Apply optimizations
        for opt in optimizations:
            if opt.confidence > 0.7:  # Only apply high-confidence optimizations
                self.current_parameters[opt.parameter_name] = opt.optimal_value
                self.logger.info(f"Optimized {opt.parameter_name}: {opt.current_value} -> {opt.optimal_value}")
        
        return optimizations
    
    def _optimize_parameter(self, param_name: str, current_value: float) -> Optional[ParameterOptimization]:
        """Optimize a single parameter"""
        # Get performance data for this parameter
        performance_data = self._get_parameter_performance_data(param_name)
        
        if not performance_data:
            return None
        
        # Analyze correlation between parameter value and performance
        correlation = self._calculate_parameter_correlation(param_name, performance_data)
        
        if abs(correlation) < 0.3:  # Weak correlation
            return None
        
        # Determine optimal value
        optimal_value = self._find_optimal_parameter_value(param_name, performance_data, correlation)
        
        # Calculate improvement potential
        improvement_potential = abs(optimal_value - current_value) / current_value
        
        # Calculate confidence
        confidence = min(0.9, abs(correlation) * 1.2)
        
        # Generate adjustment recommendation
        if optimal_value > current_value:
            recommendation = f"Increase {param_name} by {improvement_potential:.1%}"
        else:
            recommendation = f"Decrease {param_name} by {improvement_potential:.1%}"
        
        return ParameterOptimization(
            parameter_name=param_name,
            current_value=current_value,
            optimal_value=optimal_value,
            improvement_potential=improvement_potential,
            confidence=confidence,
            adjustment_recommendation=recommendation
        )
    
    def _get_parameter_performance_data(self, param_name: str) -> List[Dict[str, Any]]:
        """Get performance data related to parameter"""
        # This would analyze historical performance data
        # For now, return mock data
        return [
            {'value': 0.1, 'performance': 0.6},
            {'value': 0.3, 'performance': 0.7},
            {'value': 0.5, 'performance': 0.8},
            {'value': 0.7, 'performance': 0.75},
            {'value': 0.9, 'performance': 0.7}
        ]
    
    def _calculate_parameter_correlation(self, param_name: str, data: List[Dict[str, Any]]) -> float:
        """Calculate correlation between parameter and performance"""
        if len(data) < 3:
            return 0.0
        
        values = [d['value'] for d in data]
        performances = [d['performance'] for d in data]
        
        # Calculate Pearson correlation
        n = len(values)
        sum_x = sum(values)
        sum_y = sum(performances)
        sum_xy = sum(x * y for x, y in zip(values, performances))
        sum_x2 = sum(x * x for x in values)
        sum_y2 = sum(y * y for y in performances)
        
        numerator = n * sum_xy - sum_x * sum_y
        denominator = math.sqrt((n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y))
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def _find_optimal_parameter_value(self, param_name: str, data: List[Dict[str, Any]], correlation: float) -> float:
        """Find optimal parameter value"""
        if not data:
            return 0.5
        
        # Find value with highest performance
        best_performance = max(data, key=lambda x: x['performance'])
        return best_performance['value']
    
    async def _save_assessment_result(self, result: AssessmentResult):
        """Save assessment result to database"""
        # Implementation would save to SQLite or other database
        pass
    
    def _load_assessment_data(self):
        """Load assessment data from database"""
        # Implementation would load from database
        pass
    
    def get_assessment_summary(self) -> Dict[str, Any]:
        """Get summary of all assessments"""
        if not self.assessment_history:
            return {'message': 'No assessments completed yet'}
        
        # Calculate overall statistics
        total_assessments = len(self.assessment_history)
        avg_score = statistics.mean(r.score for r in self.assessment_history)
        best_score = max(r.score for r in self.assessment_history)
        worst_score = min(r.score for r in self.assessment_history)
        
        # Category breakdown
        category_scores = defaultdict(list)
        for result in self.assessment_history:
            category_scores[result.category.value].append(result.score)
        
        category_averages = {
            cat: statistics.mean(scores) for cat, scores in category_scores.items()
        }
        
        # Learning curves
        curve_summaries = {}
        for category, curve in self.learning_curves.items():
            curve_summaries[category] = {
                'trend': curve.trend,
                'slope': curve.slope,
                'r_squared': curve.r_squared,
                'volatility': curve.volatility
            }
        
        return {
            'total_assessments': total_assessments,
            'average_score': avg_score,
            'best_score': best_score,
            'worst_score': worst_score,
            'category_averages': category_averages,
            'learning_curves': curve_summaries,
            'current_parameters': self.current_parameters
        }


# Global instance
_assessment_system = None

def get_assessment_system() -> LearningAssessmentSystem:
    """Get global assessment system instance"""
    global _assessment_system
    if _assessment_system is None:
        _assessment_system = LearningAssessmentSystem()
    return _assessment_system

def initialize_assessment_system(db_path: str = None):
    """Initialize assessment system"""
    global _assessment_system
    _assessment_system = LearningAssessmentSystem(db_path)
    return _assessment_system
