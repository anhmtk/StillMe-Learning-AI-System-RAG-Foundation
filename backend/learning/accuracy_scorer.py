"""
Accuracy Scoring System for StillMe
Measures and tracks learning accuracy and performance
"""

import json
import sqlite3
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class AccuracyScorer:
    """System for scoring and tracking learning accuracy"""
    
    def __init__(self, db_path: str = "data/accuracy_scores.db"):
        """Initialize accuracy scoring system
        
        Args:
            db_path: Path to SQLite database for accuracy tracking
        """
        self.db_path = db_path
        self._init_database()
        logger.info("Accuracy Scorer system initialized")
    
    def _init_database(self):
        """Initialize database tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Accuracy scores table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accuracy_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT NOT NULL,
                    expected_answer TEXT,
                    actual_answer TEXT NOT NULL,
                    accuracy_score REAL NOT NULL,
                    scoring_method TEXT NOT NULL,
                    context_used TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            
            # Performance trends table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_trends (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    measurement_date DATE NOT NULL,
                    context TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Learning objectives table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learning_objectives (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    objective_name TEXT NOT NULL,
                    target_accuracy REAL NOT NULL,
                    current_accuracy REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    achieved_at TIMESTAMP,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            
            conn.commit()
            conn.close()
            logger.info("Accuracy scoring database initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def score_response(self, 
                      question: str, 
                      actual_answer: str,
                      expected_answer: Optional[str] = None,
                      scoring_method: str = "semantic_similarity",
                      context_used: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> float:
        """Score a response for accuracy
        
        Args:
            question: Original question
            actual_answer: Answer provided by StillMe
            expected_answer: Expected answer (if available)
            scoring_method: Method used for scoring
            context_used: Context used in answering
            metadata: Additional metadata
            
        Returns:
            float: Accuracy score (0-1)
        """
        try:
            # Calculate accuracy based on method
            if scoring_method == "semantic_similarity" and expected_answer:
                accuracy = self._calculate_semantic_similarity(actual_answer, expected_answer)
            elif scoring_method == "keyword_match":
                accuracy = self._calculate_keyword_match(actual_answer, expected_answer or question)
            elif scoring_method == "length_appropriateness":
                accuracy = self._calculate_length_appropriateness(actual_answer, question)
            else:
                accuracy = 0.5  # Default neutral score
            
            # Store the score
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO accuracy_scores 
                (question, expected_answer, actual_answer, accuracy_score, 
                 scoring_method, context_used, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                question,
                expected_answer,
                actual_answer,
                accuracy,
                scoring_method,
                context_used,
                json.dumps(metadata or {})
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Scored response: {accuracy:.3f} using {scoring_method}")
            return accuracy
            
        except Exception as e:
            logger.error(f"Failed to score response: {e}")
            return 0.0
    
    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            float: Similarity score (0-1)
        """
        try:
            # Simple word overlap for now - can be enhanced with embeddings
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            
            if not words1 or not words2:
                return 0.0
            
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            return len(intersection) / len(union) if union else 0.0
            
        except Exception as e:
            logger.error(f"Failed to calculate semantic similarity: {e}")
            return 0.0
    
    def _calculate_keyword_match(self, answer: str, reference: str) -> float:
        """Calculate keyword matching score
        
        Args:
            answer: Answer text
            reference: Reference text
            
        Returns:
            float: Match score (0-1)
        """
        try:
            # Extract important keywords (longer words, not common words)
            common_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
            
            answer_words = set(word.lower() for word in answer.split() if len(word) > 3 and word.lower() not in common_words)
            reference_words = set(word.lower() for word in reference.split() if len(word) > 3 and word.lower() not in common_words)
            
            if not answer_words or not reference_words:
                return 0.0
            
            matches = answer_words.intersection(reference_words)
            return len(matches) / max(len(answer_words), len(reference_words))
            
        except Exception as e:
            logger.error(f"Failed to calculate keyword match: {e}")
            return 0.0
    
    def _calculate_length_appropriateness(self, answer: str, question: str) -> float:
        """Calculate if answer length is appropriate for question
        
        Args:
            answer: Answer text
            question: Question text
            
        Returns:
            float: Appropriateness score (0-1)
        """
        try:
            answer_length = len(answer.split())
            question_length = len(question.split())
            
            # Ideal answer length is 1.5-3x question length
            ideal_min = question_length * 1.5
            ideal_max = question_length * 3.0
            
            if answer_length < ideal_min:
                return answer_length / ideal_min * 0.8  # Partial credit for short answers
            elif answer_length <= ideal_max:
                return 1.0  # Full credit for appropriate length
            else:
                # Penalty for overly long answers
                excess = answer_length - ideal_max
                penalty = min(excess / ideal_max, 0.5)  # Max 50% penalty
                return max(0.5, 1.0 - penalty)
                
        except Exception as e:
            logger.error(f"Failed to calculate length appropriateness: {e}")
            return 0.5
    
    def get_accuracy_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get accuracy metrics for specified period
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dict with accuracy statistics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get recent scores
            cursor.execute("""
                SELECT accuracy_score, scoring_method, created_at
                FROM accuracy_scores 
                WHERE created_at >= datetime('now', '-{} days')
                ORDER BY created_at DESC
            """.format(days))
            
            recent_scores = cursor.fetchall()
            
            if not recent_scores:
                return {"error": "No recent scores found"}
            
            # Calculate metrics
            scores = [row[0] for row in recent_scores]
            methods = [row[1] for row in recent_scores]
            
            avg_accuracy = sum(scores) / len(scores)
            max_accuracy = max(scores)
            min_accuracy = min(scores)
            
            # Method breakdown
            method_scores = {}
            for method in set(methods):
                method_scores[method] = [
                    score for score, m in zip(scores, methods) if m == method
                ]
            
            # Trend analysis
            recent_avg = sum(scores[:len(scores)//2]) / (len(scores)//2) if len(scores) > 1 else avg_accuracy
            older_avg = sum(scores[len(scores)//2:]) / (len(scores) - len(scores)//2) if len(scores) > 1 else avg_accuracy
            
            trend = "improving" if recent_avg > older_avg else "declining" if recent_avg < older_avg else "stable"
            
            metrics = {
                "period_days": days,
                "total_responses": len(scores),
                "average_accuracy": round(avg_accuracy, 3),
                "max_accuracy": round(max_accuracy, 3),
                "min_accuracy": round(min_accuracy, 3),
                "method_breakdown": {
                    method: {
                        "count": len(scores_list),
                        "average": round(sum(scores_list) / len(scores_list), 3)
                    }
                    for method, scores_list in method_scores.items()
                },
                "trend": trend,
                "recent_vs_older": {
                    "recent_avg": round(recent_avg, 3),
                    "older_avg": round(older_avg, 3)
                }
            }
            
            conn.close()
            logger.info(f"Calculated accuracy metrics: {metrics}")
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get accuracy metrics: {e}")
            return {"error": str(e)}
    
    def set_learning_objective(self, 
                              objective_name: str, 
                              target_accuracy: float,
                              metadata: Optional[Dict[str, Any]] = None) -> int:
        """Set a learning objective
        
        Args:
            objective_name: Name of the objective
            target_accuracy: Target accuracy to achieve (0-1)
            metadata: Additional metadata
            
        Returns:
            int: Objective ID
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO learning_objectives 
                (objective_name, target_accuracy, metadata)
                VALUES (?, ?, ?)
            """, (objective_name, target_accuracy, json.dumps(metadata or {})))
            
            objective_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Set learning objective {objective_id}: {objective_name}")
            return objective_id
            
        except Exception as e:
            logger.error(f"Failed to set learning objective: {e}")
            return -1
    
    def update_objective_progress(self, objective_id: int, current_accuracy: float) -> bool:
        """Update progress on a learning objective
        
        Args:
            objective_id: ID of the objective
            current_accuracy: Current accuracy achieved
            
        Returns:
            bool: Success status
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Update current accuracy
            cursor.execute("""
                UPDATE learning_objectives 
                SET current_accuracy = ?
                WHERE id = ?
            """, (current_accuracy, objective_id))
            
            # Check if objective is achieved
            cursor.execute("""
                SELECT target_accuracy FROM learning_objectives WHERE id = ?
            """, (objective_id,))
            
            target = cursor.fetchone()
            if target and current_accuracy >= target[0]:
                cursor.execute("""
                    UPDATE learning_objectives 
                    SET status = 'achieved', achieved_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (objective_id,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Updated objective {objective_id} progress: {current_accuracy}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update objective progress: {e}")
            return False
