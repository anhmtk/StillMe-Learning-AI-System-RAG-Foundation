#!/usr/bin/env python3
"""
Clarification Core - StillMe
Phase 1: Basic Clarification Handler

This module provides the core functionality for detecting ambiguous prompts
and generating clarification questions to improve user interaction quality.
"""

import re
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ClarificationResult:
    """Result of clarification analysis"""
    needs_clarification: bool
    confidence: float
    question: Optional[str]
    category: Optional[str]
    reasoning: str

class ClarificationHandler:
    """
    Core clarification handler for StillMe

    Detects ambiguous prompts and generates clarification questions
    to improve user interaction quality and reduce token waste.
    """

    def __init__(self):
        self.ambiguity_patterns = self._load_ambiguity_patterns()
        self.clarification_templates = self._load_clarification_templates()
        self.confidence_threshold = 0.7

    def _load_ambiguity_patterns(self) -> dict[str, list[str]]:
        """Load ambiguity detection patterns"""
        return {
            "vague_instruction": [
                r"\b(write|make|create|build|do|fix|help)\s+(code|app|something|it|this|that)\b",
                r"\b(improve|optimize|enhance|upgrade|better)\s+(it|this|that)\b",
                r"\b(set|configure|adjust|tune|refactor)\s+(it|this|that)\b",
                r"\b(change|modify|update|restructure)\s+(it|this|that)\b"
            ],
            "missing_context": [
                r"\b(build|create|make|develop|design)\s+(an?\s+)?(app|website|program|system|tool|database|report|script|api|dashboard|form|chatbot|game|plugin|widget|component|module|service|library|framework|platform|toolchain)\b",
                r"\b(write|create|make)\s+(documentation|code|program|script|function|class|method|query|filter|view|trigger|constraint|index|relationship|join|union|subquery|procedure|transaction|backup|restore|migration|rollback|deployment|release|build)\b"
            ],
            "ambiguous_reference": [
                r"\b(do|fix|change|update|delete|move|copy|paste|save|load|run|stop|start|restart|close|open|hide|show|enable|disable|activate|deactivate|turn\s+on|turn\s+off|switch)\s+(it|this|that)\b"
            ],
            "fuzzy_goal": [
                r"\b(make|do)\s+(it|this|that)\s+(faster|slower|smaller|bigger|cleaner|simpler|more\s+complex|better|worse|easier|harder|cheaper|more\s+expensive|more\s+secure|more\s+reliable|more\s+scalable|more\s+maintainable|more\s+testable|more\s+readable|more\s+efficient|more\s+flexible|more\s+robust|more\s+portable|more\s+compatible|more\s+accessible|more\s+user-friendly)\b"
            ],
            "missing_parameter": [
                r"\b(write|create|make|build|design)\s+(a\s+)?(function|class|variable|method|schema|table|query|filter|view|trigger|constraint|index|relationship|join|union|subquery|procedure|transaction|backup|restore|migration|rollback|deployment|release|build)\b"
            ],
            "slang_informal": [
                r"\b(gimme|hook\s+me\s+up|sort\s+this\s+out|fix\s+this\s+mess|make\s+it\s+pop|jazz\s+it\s+up|spice\s+it\s+up|beef\s+it\s+up|tweak\s+it|fiddle\s+with\s+it|mess\s+around\s+with\s+it|play\s+with\s+it|toy\s+with\s+it|fool\s+around\s+with\s+it|mess\s+with\s+it|tinker\s+with\s+it|futz\s+with\s+it|screw\s+with\s+it|mess\s+it\s+up|break\s+it|fix\s+it\s+up|patch\s+it\s+up|clean\s+it\s+up|tidy\s+it\s+up|straighten\s+it\s+out)\b"
            ],
            "contextual_dependency": [
                r"\b(do\s+the\s+same\s+thing|like\s+before|as\s+usual|the\s+usual\s+way|like\s+last\s+time|same\s+as\s+before|like\s+the\s+other\s+one|similar\s+to\s+that|like\s+that\s+thing|same\s+as\s+that|like\s+the\s+previous|as\s+we\s+did|like\s+we\s+discussed|as\s+planned|according\s+to\s+plan|per\s+the\s+spec|as\s+specified|per\s+requirements|as\s+required|per\s+standard|as\s+standard|per\s+protocol|as\s+protocol|per\s+procedure|as\s+procedure)\b"
            ],
            "cross_domain": [
                r"\b(analyze|process|handle|manage|control|monitor|track|measure|calculate|compute|solve|resolve|address|tackle|approach|deal\s+with|work\s+on|focus\s+on|concentrate\s+on|emphasize|highlight|spotlight|feature|showcase|present)\s+(this|it|that)\b"
            ]
        }

    def _load_clarification_templates(self) -> dict[str, list[str]]:
        """Load clarification question templates"""
        return {
            "vague_instruction": [
                "What exactly would you like me to {action}?",
                "Could you be more specific about what needs to be {action}?",
                "What should I {action} for you?",
                "I'd be happy to help! What specifically do you need me to {action}?"
            ],
            "missing_context": [
                "What type of {item} would you like me to create?",
                "Could you tell me more about the {item} you need?",
                "What should this {item} do or contain?",
                "What are the requirements for this {item}?"
            ],
            "ambiguous_reference": [
                "What does '{reference}' refer to?",
                "Could you clarify what you mean by '{reference}'?",
                "What should I {action}?",
                "I'm not sure what you're referring to. Could you be more specific?"
            ],
            "fuzzy_goal": [
                "What aspect should be {goal}?",
                "How would you like me to make it {goal}?",
                "What specifically needs to be {goal}?",
                "Could you clarify what should be {goal}?"
            ],
            "missing_parameter": [
                "What should this {item} do?",
                "What functionality do you need for this {item}?",
                "What are the requirements for this {item}?",
                "Could you specify what this {item} should accomplish?"
            ],
            "slang_informal": [
                "I'd be happy to help! Could you clarify what you need?",
                "What would you like me to do for you?",
                "Could you be more specific about what you need help with?",
                "I'm here to help! What can I do for you?"
            ],
            "contextual_dependency": [
                "I don't have the previous context. Could you provide more details?",
                "What was done before that I should reference?",
                "Could you clarify what you're referring to?",
                "What should I base this on?"
            ],
            "cross_domain": [
                "What type of {action} do you need?",
                "Could you specify what kind of {action} you're looking for?",
                "What should I {action} for you?",
                "What are you trying to {action}?"
            ]
        }

    def detect_ambiguity(self, prompt: str, context: dict[str, Any] = None) -> ClarificationResult:
        """
        Detect if a prompt is ambiguous and needs clarification

        Args:
            prompt: User input prompt
            context: Conversation context (optional)

        Returns:
            ClarificationResult with detection results
        """
        if not prompt or not prompt.strip():
            return ClarificationResult(
                needs_clarification=True,
                confidence=1.0,
                question="Could you please provide your request?",
                category="empty_prompt",
                reasoning="Empty or whitespace-only prompt"
            )

        prompt_lower = prompt.lower().strip()
        max_confidence = 0.0
        best_category = None
        best_reasoning = ""

        # Check each category of ambiguity
        for category, patterns in self.ambiguity_patterns.items():
            for pattern in patterns:
                if re.search(pattern, prompt_lower, re.IGNORECASE):
                    confidence = self._calculate_confidence(prompt, pattern, category)
                    if confidence > max_confidence:
                        max_confidence = confidence
                        best_category = category
                        best_reasoning = f"Matched pattern '{pattern}' for category '{category}'"

        # Determine if clarification is needed
        needs_clarification = max_confidence >= self.confidence_threshold

        if needs_clarification:
            question = self._generate_clarification_question(prompt, best_category, context)
        else:
            question = None

        return ClarificationResult(
            needs_clarification=needs_clarification,
            confidence=max_confidence,
            question=question,
            category=best_category,
            reasoning=best_reasoning
        )

    def _calculate_confidence(self, prompt: str, pattern: str, category: str) -> float:
        """Calculate confidence score for ambiguity detection"""
        base_confidence = 0.5

        # Adjust based on prompt length (shorter = more ambiguous)
        length_factor = max(0.1, 1.0 - (len(prompt) / 100))

        # Adjust based on category
        category_weights = {
            "vague_instruction": 0.9,
            "missing_context": 0.8,
            "ambiguous_reference": 0.95,
            "fuzzy_goal": 0.85,
            "missing_parameter": 0.8,
            "slang_informal": 0.7,
            "contextual_dependency": 0.9,
            "cross_domain": 0.75
        }

        category_weight = category_weights.get(category, 0.5)

        return min(1.0, base_confidence * length_factor * category_weight)

    def _generate_clarification_question(self, prompt: str, category: str, context: dict[str, Any] = None) -> str:
        """Generate appropriate clarification question"""
        if not category or category not in self.clarification_templates:
            return "Could you please clarify what you need help with?"

        templates = self.clarification_templates[category]

        # Select appropriate template based on category
        if category == "vague_instruction":
            # Extract action from prompt
            action_match = re.search(r"\b(write|make|create|build|do|fix|help|improve|optimize|enhance|upgrade|set|configure|adjust|tune|refactor|change|modify|update|restructure)\b", prompt.lower())
            action = action_match.group(1) if action_match else "do"
            template = templates[0].format(action=action)

        elif category == "missing_context":
            # Extract item from prompt
            item_match = re.search(r"\b(app|website|program|system|tool|database|report|script|api|dashboard|form|chatbot|game|plugin|widget|component|module|service|library|framework|platform|toolchain|function|class|method|query|filter|view|trigger|constraint|index|relationship|join|union|subquery|procedure|transaction|backup|restore|migration|rollback|deployment|release|build)\b", prompt.lower())
            item = item_match.group(1) if item_match else "item"
            template = templates[0].format(item=item)

        elif category == "ambiguous_reference":
            # Extract reference from prompt
            reference_match = re.search(r"\b(it|this|that)\b", prompt.lower())
            reference = reference_match.group(1) if reference_match else "this"
            action_match = re.search(r"\b(do|fix|change|update|delete|move|copy|paste|save|load|run|stop|start|restart|close|open|hide|show|enable|disable|activate|deactivate|turn\s+on|turn\s+off|switch)\b", prompt.lower())
            action = action_match.group(1) if action_match else "do"
            template = templates[0].format(reference=reference, action=action)

        elif category == "fuzzy_goal":
            # Extract goal from prompt
            goal_match = re.search(r"\b(faster|slower|smaller|bigger|cleaner|simpler|more\s+complex|better|worse|easier|harder|cheaper|more\s+expensive|more\s+secure|more\s+reliable|more\s+scalable|more\s+maintainable|more\s+testable|more\s+readable|more\s+efficient|more\s+flexible|more\s+robust|more\s+portable|more\s+compatible|more\s+accessible|more\s+user-friendly)\b", prompt.lower())
            goal = goal_match.group(1) if goal_match else "better"
            template = templates[0].format(goal=goal)

        elif category == "missing_parameter":
            # Extract item from prompt
            item_match = re.search(r"\b(function|class|variable|method|schema|table|query|filter|view|trigger|constraint|index|relationship|join|union|subquery|procedure|transaction|backup|restore|migration|rollback|deployment|release|build)\b", prompt.lower())
            item = item_match.group(1) if item_match else "item"
            template = templates[0].format(item=item)

        elif category == "cross_domain":
            # Extract action from prompt
            action_match = re.search(r"\b(analyze|process|handle|manage|control|monitor|track|measure|calculate|compute|solve|resolve|address|tackle|approach|deal\s+with|work\s+on|focus\s+on|concentrate\s+on|emphasize|highlight|spotlight|feature|showcase|present)\b", prompt.lower())
            action = action_match.group(1) if action_match else "help with"
            template = templates[0].format(action=action)

        else:
            template = templates[0]

        return template

    def generate_clarification(self, prompt: str, context: dict[str, Any] = None) -> Optional[str]:
        """
        Generate clarification question for ambiguous prompt

        Args:
            prompt: User input prompt
            context: Conversation context (optional)

        Returns:
            Clarification question or None if not needed
        """
        result = self.detect_ambiguity(prompt, context)
        return result.question if result.needs_clarification else None

    def get_clarification_stats(self) -> dict[str, Any]:
        """Get clarification handler statistics"""
        return {
            "patterns_loaded": sum(len(patterns) for patterns in self.ambiguity_patterns.values()),
            "categories": list(self.ambiguity_patterns.keys()),
            "templates_loaded": sum(len(templates) for templates in self.clarification_templates.values()),
            "confidence_threshold": self.confidence_threshold
        }

# Example usage and testing
if __name__ == "__main__":
    handler = ClarificationHandler()

    # Test cases
    test_prompts = [
        "Write code for this",
        "Build an app",
        "Do it now",
        "Make it better",
        "Create a function",
        "gimme some code",
        "do the same thing",
        "analyze this"
    ]

    print("Clarification Handler Test Results:")
    print("=" * 50)

    for prompt in test_prompts:
        result = handler.detect_ambiguity(prompt)
        print(f"Prompt: '{prompt}'")
        print(f"Needs clarification: {result.needs_clarification}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Category: {result.category}")
        print(f"Question: {result.question}")
        print("-" * 30)
