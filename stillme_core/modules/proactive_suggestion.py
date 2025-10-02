"""
Proactive Suggestion Module - Phase 3

This module provides proactive suggestions to enhance user experience
by anticipating user needs and offering relevant options before they ask.

Author: StillMe AI Platform
Version: 3.0.0
"""

import logging
import re
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

@dataclass
class SuggestionResult:
    """Result of proactive suggestion analysis"""
    suggestions: list[str]
    confidence: float
    reasoning: str
    category: str
    metadata: dict[str, Any]
    learning_enabled: bool = True

class ProactiveSuggestion:
    """
    Generates proactive suggestions based on user input patterns,
    context analysis, and learned preferences.
    """

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.enabled = config.get("enabled", True)
        self.max_suggestions = config.get("max_suggestions", 3)
        self.categories = config.get("categories", ["performance", "security", "ux", "scalability", "maintainability"])
        self.confidence_threshold = config.get("confidence_threshold", 0.6)
        self.learning_enabled = config.get("learning_enabled", True)

        # Learning storage
        self.user_preferences = defaultdict(Counter)  # user_id -> category -> count
        self.suggestion_history = []  # Track suggestion usage
        self.pattern_learning = defaultdict(int)  # pattern -> success_count

        # Suggestion templates by category
        self.suggestion_templates = {
            "performance": {
                "optimization": [
                    "Optimize database queries",
                    "Implement caching strategy",
                    "Add performance monitoring",
                    "Optimize image loading",
                    "Minify CSS/JS files"
                ],
                "scalability": [
                    "Implement horizontal scaling",
                    "Add load balancing",
                    "Optimize memory usage",
                    "Implement connection pooling",
                    "Add auto-scaling"
                ]
            },
            "security": {
                "authentication": [
                    "Implement two-factor authentication",
                    "Add session management",
                    "Implement OAuth2",
                    "Add password policies",
                    "Implement JWT tokens"
                ],
                "data_protection": [
                    "Encrypt sensitive data",
                    "Implement HTTPS",
                    "Add input validation",
                    "Implement rate limiting",
                    "Add security headers"
                ]
            },
            "ux": {
                "usability": [
                    "Improve navigation",
                    "Add loading indicators",
                    "Implement responsive design",
                    "Add accessibility features",
                    "Optimize user flow"
                ],
                "interaction": [
                    "Add keyboard shortcuts",
                    "Implement drag and drop",
                    "Add tooltips",
                    "Implement auto-save",
                    "Add undo/redo functionality"
                ]
            },
            "scalability": {
                "architecture": [
                    "Implement microservices",
                    "Add message queues",
                    "Implement event-driven architecture",
                    "Add distributed caching",
                    "Implement API gateway"
                ],
                "infrastructure": [
                    "Implement containerization",
                    "Add monitoring and logging",
                    "Implement CI/CD pipeline",
                    "Add backup strategies",
                    "Implement disaster recovery"
                ]
            },
            "maintainability": {
                "code_quality": [
                    "Add unit tests",
                    "Implement code review process",
                    "Add documentation",
                    "Implement linting",
                    "Add code coverage"
                ],
                "architecture": [
                    "Implement design patterns",
                    "Add dependency injection",
                    "Implement SOLID principles",
                    "Add error handling",
                    "Implement logging"
                ]
            }
        }

        # Pattern matching for suggestion triggers
        self.trigger_patterns = {
            "performance": [
                r"\b(slow|fast|speed|performance|optimize|efficient)\b",
                r"\b(load|time|response|latency|throughput)\b",
                r"\b(cache|memory|cpu|resource)\b"
            ],
            "security": [
                r"\b(secure|security|auth|login|password|encrypt)\b",
                r"\b(vulnerability|attack|hack|breach|protect)\b",
                r"\b(ssl|https|certificate|token|session)\b"
            ],
            "ux": [
                r"\b(ui|ux|interface|user|experience|design)\b",
                r"\b(button|form|navigation|menu|layout)\b",
                r"\b(accessibility|responsive|mobile|desktop)\b"
            ],
            "scalability": [
                r"\b(scale|scalable|grow|expand|handle|traffic)\b",
                r"\b(microservice|distributed|cluster|load)\b",
                r"\b(concurrent|parallel|async|queue)\b"
            ],
            "maintainability": [
                r"\b(maintain|clean|refactor|test|document)\b",
                r"\b(code|quality|review|standards|best)\b",
                r"\b(debug|fix|error|exception|log)\b"
            ]
        }

    def _analyze_input_patterns(self, text: str) -> dict[str, float]:
        """Analyze input text to detect suggestion categories"""
        text_lower = text.lower()
        category_scores = {}

        for category, patterns in self.trigger_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text_lower))
                score += matches * 0.1  # Weight each match

            # Normalize score
            category_scores[category] = min(score, 1.0)

        return category_scores

    def _get_context_suggestions(self, context: dict[str, Any]) -> list[str]:
        """Generate suggestions based on context information"""
        suggestions = []

        # Project context analysis
        project_context = context.get("project_context", {})
        project_context.get("files", [])
        extensions = project_context.get("extensions", [])

        # File-based suggestions
        if any(ext in [".js", ".ts", ".jsx", ".tsx"] for ext in extensions):
            suggestions.extend([
                "Add TypeScript types",
                "Implement error boundaries",
                "Add performance monitoring"
            ])

        if any(ext in [".py"] for ext in extensions):
            suggestions.extend([
                "Add type hints",
                "Implement logging",
                "Add unit tests"
            ])

        if any(ext in [".sql"] for ext in extensions):
            suggestions.extend([
                "Add database indexes",
                "Implement query optimization",
                "Add data validation"
            ])

        # Conversation history analysis
        conversation_history = context.get("conversation_history", [])
        if conversation_history:
            recent_topics = []
            for msg in conversation_history[-3:]:  # Last 3 messages
                content = msg.get("content", "").lower()
                if "error" in content or "bug" in content:
                    recent_topics.append("debugging")
                elif "optimize" in content or "improve" in content:
                    recent_topics.append("optimization")
                elif "test" in content:
                    recent_topics.append("testing")

            if "debugging" in recent_topics:
                suggestions.extend([
                    "Add comprehensive error handling",
                    "Implement logging strategy",
                    "Add debugging tools"
                ])

            if "optimization" in recent_topics:
                suggestions.extend([
                    "Profile performance bottlenecks",
                    "Implement caching layer",
                    "Optimize database queries"
                ])

        return suggestions[:3]  # Limit to 3 context suggestions

    def _get_learned_suggestions(self, user_id: str, category: str) -> list[str]:
        """Get suggestions based on user's historical preferences"""
        if not self.learning_enabled or not user_id:
            return []

        user_prefs = self.user_preferences.get(user_id, Counter())
        if not user_prefs:
            return []

        # Get user's preferred categories
        top_categories = user_prefs.most_common(3)
        suggestions = []

        for cat, _count in top_categories:
            if cat in self.suggestion_templates:
                # Get random suggestions from preferred category
                templates = self.suggestion_templates[cat]
                for _subcategory, template_list in templates.items():
                    if template_list:
                        suggestions.extend(template_list[:1])  # Take 1 from each subcategory

        return suggestions[:2]  # Limit learned suggestions

    def _generate_suggestions(self, text: str, context: dict[str, Any] = None) -> SuggestionResult:
        """Generate proactive suggestions based on input analysis"""
        if not self.enabled:
            return SuggestionResult(
                suggestions=[],
                confidence=0.0,
                reasoning="Proactive suggestions disabled",
                category="none",
                metadata={"disabled": True}
            )

        try:
            # Analyze input patterns
            category_scores = self._analyze_input_patterns(text)

            # Find top category
            if not category_scores or max(category_scores.values()) < self.confidence_threshold:
                return SuggestionResult(
                    suggestions=[],
                    confidence=0.0,
                    reasoning="No clear category detected",
                    category="none",
                    metadata={"category_scores": category_scores}
                )

            top_category = max(category_scores, key=category_scores.get)
            confidence = category_scores[top_category]

            # Generate suggestions
            suggestions = []

            # 1. Category-based suggestions
            if top_category in self.suggestion_templates:
                templates = self.suggestion_templates[top_category]
                for _subcategory, template_list in templates.items():
                    if template_list:
                        suggestions.extend(template_list[:1])  # Take 1 from each subcategory

            # 2. Context-based suggestions
            if context:
                context_suggestions = self._get_context_suggestions(context)
                suggestions.extend(context_suggestions)

            # 3. Learned suggestions
            user_id = context.get("user_id") if context else None
            if user_id:
                learned_suggestions = self._get_learned_suggestions(user_id, top_category)
                suggestions.extend(learned_suggestions)

            # Remove duplicates and limit
            unique_suggestions = list(dict.fromkeys(suggestions))  # Preserve order, remove duplicates
            final_suggestions = unique_suggestions[:self.max_suggestions]

            return SuggestionResult(
                suggestions=final_suggestions,
                confidence=confidence,
                reasoning=f"Detected {top_category} category with {confidence:.2f} confidence",
                category=top_category,
                metadata={
                    "category_scores": category_scores,
                    "context_used": context is not None,
                    "learning_used": user_id is not None and self.learning_enabled
                },
                learning_enabled=self.learning_enabled
            )

        except Exception as e:
            logger.error(f"ProactiveSuggestion generation failed: {e}")
            return SuggestionResult(
                suggestions=[],
                confidence=0.0,
                reasoning=f"Generation error: {str(e)}",
                category="error",
                metadata={"error": str(e)}
            )

    def record_suggestion_usage(self, user_id: str, suggestion: str, category: str, success: bool = True):
        """Record suggestion usage for learning"""
        if not self.learning_enabled or not user_id:
            return

        try:
            # Record in user preferences
            if success:
                self.user_preferences[user_id][category] += 1

            # Record in suggestion history
            self.suggestion_history.append({
                "timestamp": time.time(),
                "user_id": user_id,
                "suggestion": suggestion,
                "category": category,
                "success": success
            })

            # Keep only recent history (last 1000 entries)
            if len(self.suggestion_history) > 1000:
                self.suggestion_history = self.suggestion_history[-1000:]

            logger.debug(f"Recorded suggestion usage: {suggestion} for user {user_id}, success={success}")

        except Exception as e:
            logger.error(f"Failed to record suggestion usage: {e}")

    def get_suggestion_stats(self) -> dict[str, Any]:
        """Get statistics about suggestion usage"""
        try:
            total_suggestions = len(self.suggestion_history)
            successful_suggestions = sum(1 for s in self.suggestion_history if s.get("success", False))

            # Category distribution
            category_counts = Counter()
            for suggestion in self.suggestion_history:
                category_counts[suggestion.get("category", "unknown")] += 1

            # User activity
            user_counts = Counter()
            for suggestion in self.suggestion_history:
                user_counts[suggestion.get("user_id", "unknown")] += 1

            return {
                "total_suggestions": total_suggestions,
                "successful_suggestions": successful_suggestions,
                "success_rate": successful_suggestions / total_suggestions if total_suggestions > 0 else 0.0,
                "category_distribution": dict(category_counts),
                "active_users": len(user_counts),
                "learning_enabled": self.learning_enabled,
                "categories_available": len(self.categories)
            }

        except Exception as e:
            logger.error(f"Failed to get suggestion stats: {e}")
            return {"error": str(e)}

    def clear_learning_data(self):
        """Clear all learning data"""
        try:
            self.user_preferences.clear()
            self.suggestion_history.clear()
            self.pattern_learning.clear()
            logger.info("Proactive suggestion learning data cleared")
        except Exception as e:
            logger.error(f"Failed to clear learning data: {e}")

    def suggest(self, text: str, context: dict[str, Any] = None) -> SuggestionResult:
        """
        Main method to generate proactive suggestions

        Args:
            text: Input text to analyze
            context: Additional context for suggestion generation

        Returns:
            SuggestionResult with suggestions and metadata
        """
        return self._generate_suggestions(text, context)
