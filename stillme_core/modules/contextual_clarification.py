#!/usr/bin/env python3
"""
Context-Aware Clarification Module - Phase 2
Generates intelligent clarification questions based on context
"""

import logging
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ClarificationQuestion:
    """Structured clarification question"""

    question: str
    options: list[str]
    confidence: float
    domain: str
    reasoning: str
    follow_up_hints: list[str] = None


class ContextAwareClarifier:
    """
    Generates context-aware clarification questions
    """

    def __init__(self, context_analyzer=None, semantic_search=None, learner=None):
        self.context_analyzer = context_analyzer
        self.semantic_search = semantic_search
        self.learner = learner
        self.domain_question_banks = self._initialize_question_banks()

    def _initialize_question_banks(self) -> dict[str, list[tuple[str, list[str]]]]:
        """Initialize domain-specific question banks"""
        return {
            "web": [
                (
                    "Which framework do you prefer? Flask or FastAPI?",
                    ["Flask", "FastAPI"],
                ),
                ("Backend or frontend focus?", ["Backend", "Frontend"]),
                (
                    "What type of web application? E-commerce, Blog, Dashboard, or API?",
                    ["E-commerce", "Blog", "Dashboard", "API"],
                ),
                (
                    "Which frontend framework? React, Vue, or Angular?",
                    ["React", "Vue", "Angular"],
                ),
                ("Database preference? SQL or NoSQL?", ["SQL", "NoSQL"]),
                ("Deployment target? Cloud, VPS, or Local?", ["Cloud", "VPS", "Local"]),
            ],
            "data": [
                (
                    "What data source? CSV, JSON, Database, or API?",
                    ["CSV", "JSON", "Database", "API"],
                ),
                (
                    "What type of analysis? Descriptive, Predictive, or Prescriptive?",
                    ["Descriptive", "Predictive", "Prescriptive"],
                ),
                (
                    "Which visualization library? Matplotlib, Seaborn, or Plotly?",
                    ["Matplotlib", "Seaborn", "Plotly"],
                ),
                (
                    "Data size? Small (<1MB), Medium (1-100MB), or Large (>100MB)?",
                    ["Small", "Medium", "Large"],
                ),
                (
                    "Analysis goal? Exploration, Reporting, or Modeling?",
                    ["Exploration", "Reporting", "Modeling"],
                ),
            ],
            "ml": [
                (
                    "Which model family? Linear, Tree-based, or Neural Network?",
                    ["Linear", "Tree-based", "Neural Network"],
                ),
                (
                    "Problem type? Classification, Regression, or Clustering?",
                    ["Classification", "Regression", "Clustering"],
                ),
                (
                    "Which ML framework? Scikit-learn, TensorFlow, or PyTorch?",
                    ["Scikit-learn", "TensorFlow", "PyTorch"],
                ),
                (
                    "Data size? Small (<1K samples), Medium (1K-100K), or Large (>100K)?",
                    ["Small", "Medium", "Large"],
                ),
                (
                    "Performance priority? Accuracy, Speed, or Interpretability?",
                    ["Accuracy", "Speed", "Interpretability"],
                ),
            ],
            "devops": [
                (
                    "Target environment? Docker, VM, or Serverless?",
                    ["Docker", "VM", "Serverless"],
                ),
                ("Cloud provider? AWS, Azure, or GCP?", ["AWS", "Azure", "GCP"]),
                (
                    "Deployment type? Blue-Green, Rolling, or Canary?",
                    ["Blue-Green", "Rolling", "Canary"],
                ),
                (
                    "Monitoring needs? Basic, Advanced, or Enterprise?",
                    ["Basic", "Advanced", "Enterprise"],
                ),
                (
                    "Security level? Standard, Enhanced, or High?",
                    ["Standard", "Enhanced", "High"],
                ),
            ],
            "mobile": [
                (
                    "Platform? iOS, Android, or Cross-platform?",
                    ["iOS", "Android", "Cross-platform"],
                ),
                ("App type? Native, Hybrid, or PWA?", ["Native", "Hybrid", "PWA"]),
                (
                    "Framework? React Native, Flutter, or Xamarin?",
                    ["React Native", "Flutter", "Xamarin"],
                ),
                (
                    "Target audience? Consumer, Enterprise, or Internal?",
                    ["Consumer", "Enterprise", "Internal"],
                ),
                (
                    "Monetization? Free, Freemium, or Paid?",
                    ["Free", "Freemium", "Paid"],
                ),
            ],
            "programming": [
                (
                    "Which programming language? Python, JavaScript, Java, or C++?",
                    ["Python", "JavaScript", "Java", "C++"],
                ),
                (
                    "What type of program? Script, Application, or Library?",
                    ["Script", "Application", "Library"],
                ),
                (
                    "Complexity level? Beginner, Intermediate, or Advanced?",
                    ["Beginner", "Intermediate", "Advanced"],
                ),
                (
                    "Performance requirement? Low, Medium, or High?",
                    ["Low", "Medium", "High"],
                ),
                (
                    "Code style? Functional, Object-oriented, or Procedural?",
                    ["Functional", "Object-oriented", "Procedural"],
                ),
            ],
            "generic": [
                (
                    "Could you specify the goal? Performance, Security, or Usability?",
                    ["Performance", "Security", "Usability"],
                ),
                (
                    "What's the priority? Speed, Quality, or Cost?",
                    ["Speed", "Quality", "Cost"],
                ),
                (
                    "Target audience? Beginner, Intermediate, or Expert?",
                    ["Beginner", "Intermediate", "Expert"],
                ),
                (
                    "Scope? Small, Medium, or Large project?",
                    ["Small", "Medium", "Large"],
                ),
                (
                    "Timeline? Urgent, Normal, or Flexible?",
                    ["Urgent", "Normal", "Flexible"],
                ),
            ],
        }

    def _detect_domain_from_history(
        self, conversation_history: list[dict[str, Any]]
    ) -> str:
        """Detect domain from conversation history"""
        if not conversation_history:
            return "generic"

        # Keywords for domain detection
        domain_keywords = {
            "web": [
                "web",
                "website",
                "app",
                "frontend",
                "backend",
                "api",
                "flask",
                "fastapi",
                "react",
                "vue",
            ],
            "data": [
                "data",
                "analysis",
                "csv",
                "json",
                "database",
                "pandas",
                "numpy",
                "matplotlib",
            ],
            "ml": [
                "machine learning",
                "ml",
                "model",
                "training",
                "prediction",
                "tensorflow",
                "pytorch",
            ],
            "devops": [
                "deploy",
                "docker",
                "kubernetes",
                "aws",
                "azure",
                "gcp",
                "ci/cd",
                "pipeline",
            ],
            "mobile": ["mobile", "ios", "android", "app", "react native", "flutter"],
            "programming": [
                "code",
                "program",
                "function",
                "class",
                "python",
                "javascript",
                "java",
            ],
        }

        # Analyze recent messages
        recent_messages = conversation_history[-5:]  # Last 5 messages
        domain_scores = dict.fromkeys(domain_keywords.keys(), 0)

        for message in recent_messages:
            content = message.get("content", "").lower()
            for domain, keywords in domain_keywords.items():
                for keyword in keywords:
                    if keyword in content:
                        domain_scores[domain] += 1

        # Return domain with highest score
        if domain_scores:
            best_domain = max(domain_scores, key=domain_scores.get)
            if domain_scores[best_domain] > 0:
                return best_domain

        return "generic"

    def _detect_domain_from_project_context(
        self, project_context: dict[str, Any]
    ) -> str:
        """Detect domain from project context"""
        if not project_context:
            return "generic"

        # Check for framework files
        files = project_context.get("files", [])
        file_extensions = project_context.get("extensions", [])

        # Web development indicators
        if any(
            f in files
            for f in ["package.json", "requirements.txt", "app.py", "main.py"]
        ):
            if any(ext in file_extensions for ext in [".js", ".jsx", ".ts", ".tsx"]):
                return "web"
            elif any(ext in file_extensions for ext in [".py"]):
                return (
                    "web"
                    if "flask" in str(files).lower() or "fastapi" in str(files).lower()
                    else "programming"
                )

        # Data science indicators
        if any(f in files for f in ["requirements.txt", "environment.yml"]) and any(
            ext in file_extensions for ext in [".ipynb", ".py"]
        ):
            if "pandas" in str(files).lower() or "numpy" in str(files).lower():
                return "data"

        # Mobile development indicators
        if any(f in files for f in ["pubspec.yaml", "package.json"]) and any(
            ext in file_extensions for ext in [".dart", ".swift", ".kt"]
        ):
            return "mobile"

        return "generic"

    def _extract_keywords_from_prompt(self, prompt: str) -> list[str]:
        """Extract relevant keywords from prompt"""
        # Simple keyword extraction
        words = re.findall(r"\b\w+\b", prompt.lower())

        # Filter out common words
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
        }
        keywords = [word for word in words if word not in stop_words and len(word) > 2]

        return keywords[:10]  # Top 10 keywords

    def _get_semantic_suggestions(
        self, prompt: str, context: dict[str, Any]
    ) -> list[str]:
        """Get semantic suggestions from knowledge base"""
        if not self.semantic_search:
            return []

        try:
            # Extract keywords for semantic search
            keywords = self._extract_keywords_from_prompt(prompt)

            # Search for related items
            related_items = self.semantic_search.find_related_items(" ".join(keywords))

            # Extract suggestions from related items
            suggestions = []
            for item in related_items[:5]:  # Top 5 related items
                if isinstance(item, dict):
                    suggestions.append(item.get("name", str(item)))
                else:
                    suggestions.append(str(item))

            return suggestions
        except Exception as e:
            logger.warning(f"Semantic search failed: {e}")
            return []

    def make_question(
        self,
        prompt: str,
        conversation_history: list[dict[str, Any]],
        project_context: dict[str, Any],
    ) -> ClarificationQuestion:
        """
        Generate context-aware clarification question

        Args:
            prompt: User prompt to clarify
            conversation_history: Recent conversation messages
            project_context: Project files and context

        Returns:
            ClarificationQuestion with question, options, and metadata
        """
        # Detect domain from multiple sources
        history_domain = self._detect_domain_from_history(conversation_history)
        project_domain = self._detect_domain_from_project_context(project_context)

        # Use project domain if available, otherwise history domain
        domain = project_domain if project_domain != "generic" else history_domain

        # Try to get learned patterns first
        learned_suggestion = None
        if self.learner:
            try:
                # Note: suggest_patterns is async, but we're in sync context
                # For now, skip learned patterns in sync context
                learned_suggestion = None
            except Exception as e:
                logger.warning(f"Learner suggestion failed: {e}")

        # Use learned pattern if available and confident
        if learned_suggestion and learned_suggestion.get("confidence", 0) > 0.5:
            question_text = learned_suggestion["template"]
            options = learned_suggestion.get("slots", {}).get("options", [])
            confidence = learned_suggestion["confidence"]
            reasoning = f"Learned pattern (success rate: {learned_suggestion.get('success_rate', 0):.2f})"
        else:
            # Use domain-specific question bank
            question_bank = self.domain_question_banks.get(
                domain, self.domain_question_banks["generic"]
            )

            # Select most appropriate question based on prompt content
            best_question = self._select_best_question(prompt, question_bank)
            question_text, options = best_question
            confidence = 0.65  # Default confidence for domain-based questions
            reasoning = f"Domain-based question for '{domain}'"

        # Add semantic suggestions as follow-up hints
        follow_up_hints = self._get_semantic_suggestions(prompt, project_context)

        return ClarificationQuestion(
            question=question_text,
            options=options,
            confidence=confidence,
            domain=domain,
            reasoning=reasoning,
            follow_up_hints=follow_up_hints,
        )

    def _select_best_question(
        self, prompt: str, question_bank: list[tuple[str, list[str]]]
    ) -> tuple[str, list[str]]:
        """Select the most appropriate question from the bank based on prompt content"""
        if not question_bank:
            return "Could you please provide more details?", []

        # Simple keyword matching to select best question
        prompt_lower = prompt.lower()

        # Score each question based on keyword overlap
        scored_questions = []
        for question, options in question_bank:
            question_lower = question.lower()
            options_lower = " ".join(options).lower()

            # Count keyword matches
            prompt_words = set(re.findall(r"\b\w+\b", prompt_lower))
            question_words = set(re.findall(r"\b\w+\b", question_lower))
            options_words = set(re.findall(r"\b\w+\b", options_lower))

            # Calculate overlap score
            question_overlap = len(prompt_words.intersection(question_words))
            options_overlap = len(prompt_words.intersection(options_words))
            total_score = question_overlap + options_overlap * 0.5

            scored_questions.append((total_score, question, options))

        # Return question with highest score, or first question if no matches
        if scored_questions:
            scored_questions.sort(key=lambda x: x[0], reverse=True)
            return scored_questions[0][1], scored_questions[0][2]

        return question_bank[0]

    def get_domain_stats(self) -> dict[str, int]:
        """Get statistics about domain usage"""
        return {
            domain: len(questions)
            for domain, questions in self.domain_question_banks.items()
        }


# Example usage and testing
if __name__ == "__main__":
    # Test the context-aware clarifier
    clarifier = ContextAwareClarifier()

    # Test with different contexts
    test_cases = [
        {
            "prompt": "Write code for this",
            "history": [{"content": "I'm working on a web application with Flask"}],
            "project": {"files": ["app.py", "requirements.txt"], "extensions": [".py"]},
        },
        {
            "prompt": "Build an app",
            "history": [{"content": "I need to analyze some data"}],
            "project": {
                "files": ["data.csv", "analysis.py"],
                "extensions": [".py", ".csv"],
            },
        },
        {"prompt": "Create something", "history": [], "project": {}},
    ]

    for i, test_case in enumerate(test_cases):
        print(f"\nTest Case {i+1}:")
        print(f"Prompt: {test_case['prompt']}")

        question = clarifier.make_question(
            test_case["prompt"], test_case["history"], test_case["project"]
        )

        print(f"Domain: {question.domain}")
        print(f"Question: {question.question}")
        print(f"Options: {question.options}")
        print(f"Confidence: {question.confidence:.2f}")
        print(f"Reasoning: {question.reasoning}")
