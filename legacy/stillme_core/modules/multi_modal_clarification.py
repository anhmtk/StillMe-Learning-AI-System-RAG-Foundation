"""
Multi-Modal Clarification Module - Phase 3

This module provides clarification capabilities for different input types:
- VisualClarifier: Image analysis and clarification
- CodeClarifier: Code analysis using AST and language detection
- TextClarifier: Enhanced text clarification (extends Phase 2)

Author: StillMe AI Platform
Version: 3.0.0
"""

import ast
import base64
import hashlib
import io
import logging
import re
from dataclasses import dataclass
from typing import Any

from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class MultiModalResult:
    """Result of multi-modal clarification analysis"""

    needs_clarification: bool
    input_type: str  # "text", "code", "image", "mixed"
    question: str | None
    options: list[str] | None
    confidence: float
    reasoning: str
    metadata: dict[str, Any]
    suggestions: list[str] | None = None
    domain: str | None = None
    round_number: int = 1
    max_rounds: int = 2
    trace_id: str | None = None


class VisualClarifier:
    """
    Handles image analysis and clarification for visual inputs.
    Currently uses stub implementation, ready for integration with real CV models.
    """

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.max_size_mb = config.get("max_image_size_mb", 10)
        self.supported_formats = config.get(
            "supported_image_formats", ["jpg", "jpeg", "png", "gif", "webp"]
        )
        self.analysis_mode = config.get("image_analysis", "stub")

    def _validate_image(self, image_data: bytes | str) -> dict[str, Any]:
        """Validate image data and extract metadata"""
        try:
            if isinstance(image_data, str):
                # Assume base64 encoded
                image_bytes = base64.b64decode(image_data)
            else:
                image_bytes = image_data

            # Check size
            size_mb = len(image_bytes) / (1024 * 1024)
            if size_mb > self.max_size_mb:
                return {
                    "valid": False,
                    "error": f"Image too large: {size_mb:.1f}MB > {self.max_size_mb}MB",
                }

            # Try to open with PIL
            image = Image.open(io.BytesIO(image_bytes))
            format_name = image.format.lower() if image.format else "unknown"

            if format_name not in self.supported_formats:
                return {"valid": False, "error": f"Unsupported format: {format_name}"}

            return {
                "valid": True,
                "format": format_name,
                "size": image.size,
                "mode": image.mode,
                "size_mb": size_mb,
                "hash": hashlib.sha256(image_bytes).hexdigest()[:16],
            }
        except Exception as e:
            return {"valid": False, "error": f"Invalid image data: {str(e)}"}

    def _stub_analysis(self, image_metadata: dict[str, Any]) -> dict[str, Any]:
        """Stub implementation for image analysis"""
        # Simulate different types of images based on size and format
        width, height = image_metadata["size"]
        aspect_ratio = width / height if height > 0 else 1

        if aspect_ratio > 2:
            # Wide image - likely diagram or chart
            return {
                "question": "I see a wide diagram or chart. What specific aspect would you like me to focus on?",
                "options": [
                    "Data analysis",
                    "Layout optimization",
                    "Content explanation",
                    "Design improvement",
                ],
                "confidence": 0.7,
                "detected_objects": ["diagram", "chart", "wide_layout"],
                "suggestions": [
                    "Analyze the data",
                    "Improve the layout",
                    "Explain the content",
                ],
            }
        elif aspect_ratio < 0.5:
            # Tall image - likely document or code
            return {
                "question": "I see a tall document or code snippet. What would you like me to help with?",
                "options": [
                    "Code review",
                    "Documentation",
                    "Bug fixing",
                    "Optimization",
                ],
                "confidence": 0.8,
                "detected_objects": ["document", "code", "text"],
                "suggestions": ["Review the code", "Improve documentation", "Fix bugs"],
            }
        else:
            # Square-ish image - likely UI or general content
            return {
                "question": "I see an image. What specific area would you like me to analyze?",
                "options": [
                    "UI/UX review",
                    "Content analysis",
                    "Design feedback",
                    "Accessibility check",
                ],
                "confidence": 0.6,
                "detected_objects": ["ui", "content", "design"],
                "suggestions": [
                    "Review UI/UX",
                    "Analyze content",
                    "Check accessibility",
                ],
            }

    def analyze(
        self, image_data: bytes | str, context: dict[str, Any] = None
    ) -> MultiModalResult:
        """
        Analyze image and generate clarification questions

        Args:
            image_data: Image bytes or base64 string
            context: Additional context for analysis

        Returns:
            MultiModalResult with clarification information
        """
        try:
            # Validate image
            validation = self._validate_image(image_data)
            if not validation["valid"]:
                return MultiModalResult(
                    needs_clarification=True,
                    input_type="image",
                    question=f"Image validation failed: {validation['error']}. Would you like to try a different image?",
                    options=[
                        "Try different image",
                        "Describe the image",
                        "Skip image analysis",
                    ],
                    confidence=0.9,
                    reasoning="Image validation failed",
                    metadata={"validation_error": validation["error"]},
                )

            # Perform analysis based on mode
            if self.analysis_mode == "stub":
                analysis_result = self._stub_analysis(validation)
            else:
                # Future: integrate with real CV models (OpenAI Vision, custom models)
                analysis_result = self._stub_analysis(validation)

            return MultiModalResult(
                needs_clarification=True,
                input_type="image",
                question=analysis_result["question"],
                options=analysis_result["options"],
                confidence=analysis_result["confidence"],
                reasoning=f"Image analysis detected: {', '.join(analysis_result['detected_objects'])}",
                metadata={
                    "image_metadata": validation,
                    "analysis_result": analysis_result,
                    "analysis_mode": self.analysis_mode,
                },
                suggestions=analysis_result.get("suggestions"),
                domain="visual",
            )

        except Exception as e:
            logger.error(f"VisualClarifier analysis failed: {e}")
            return MultiModalResult(
                needs_clarification=True,
                input_type="image",
                question="I encountered an error analyzing the image. Could you describe what you'd like me to help with?",
                options=[
                    "Describe the image",
                    "Try different image",
                    "Skip image analysis",
                ],
                confidence=0.5,
                reasoning=f"Analysis error: {str(e)}",
                metadata={"error": str(e)},
            )


class CodeClarifier:
    """
    Handles code analysis and clarification using AST parsing and language detection.
    """

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.analysis_mode = config.get("code_analysis", "ast")
        self.supported_languages = config.get(
            "code_languages",
            ["python", "javascript", "typescript", "java", "cpp", "go", "rust"],
        )

    def _detect_language(self, code: str) -> str:
        """Detect programming language from code snippet"""
        code_lower = code.lower().strip()

        # Python indicators
        if any(
            keyword in code_lower
            for keyword in ["def ", "import ", "from ", "class ", "if __name__"]
        ):
            return "python"

        # JavaScript/TypeScript indicators
        if any(
            keyword in code_lower
            for keyword in [
                "function",
                "const ",
                "let ",
                "var ",
                "=>",
                "interface",
                "type ",
            ]
        ):
            if "interface " in code_lower or "type " in code_lower:
                return "typescript"
            return "javascript"

        # Java indicators
        if any(
            keyword in code_lower
            for keyword in ["public class", "private ", "public ", "import java"]
        ):
            return "java"

        # C++ indicators
        if (
            any(
                keyword in code_lower
                for keyword in ["#include", "std::", "namespace ", "class "]
            )
            and "def " not in code_lower
        ):
            return "cpp"

        # Go indicators
        if (
            any(
                keyword in code_lower
                for keyword in ["package ", "func ", "import (", "var "]
            )
            and "def " not in code_lower
        ):
            return "go"

        # Rust indicators
        if (
            any(
                keyword in code_lower
                for keyword in ["fn ", "let ", "use ", "mod ", "struct "]
            )
            and "def " not in code_lower
        ):
            return "rust"

        return "unknown"

    def _analyze_python_ast(self, code: str) -> dict[str, Any]:
        """Analyze Python code using AST"""
        try:
            tree = ast.parse(code)

            # Extract different node types
            functions = []
            classes = []
            imports = []
            variables = []

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append(
                        {
                            "name": node.name,
                            "args": [arg.arg for arg in node.args.args],
                            "line": node.lineno,
                        }
                    )
                elif isinstance(node, ast.ClassDef):
                    classes.append({"name": node.name, "line": node.lineno})
                elif isinstance(node, ast.Import):
                    imports.extend([alias.name for alias in node.names])
                elif isinstance(node, ast.ImportFrom):
                    imports.extend(
                        [
                            f"{node.module}.{alias.name}" if node.module else alias.name
                            for alias in node.names
                        ]
                    )
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            variables.append(target.id)

            return {
                "functions": functions,
                "classes": classes,
                "imports": imports,
                "variables": variables,
                "valid": True,
            }
        except SyntaxError as e:
            return {
                "valid": False,
                "error": f"Syntax error: {str(e)}",
                "line": getattr(e, "lineno", None),
            }
        except Exception as e:
            return {"valid": False, "error": f"Analysis error: {str(e)}"}

    def _generate_code_question(
        self, analysis: dict[str, Any], language: str
    ) -> dict[str, Any]:
        """Generate clarification question based on code analysis"""
        if not analysis.get("valid", False):
            return {
                "question": f"Your {language} code has a syntax error. Would you like me to help fix it first?",
                "options": [
                    "Fix syntax error",
                    "Explain the error",
                    "Rewrite the code",
                    "Skip this code",
                ],
                "confidence": 0.9,
                "suggestions": [
                    "Fix the syntax",
                    "Explain the error",
                    "Provide alternative",
                ],
            }

        functions = analysis.get("functions", [])
        classes = analysis.get("classes", [])
        analysis.get("imports", [])

        if functions and classes:
            return {
                "question": f"I see {len(functions)} functions and {len(classes)} classes. What would you like me to focus on?",
                "options": [f"Function: {f['name']}" for f in functions[:3]]
                + [f"Class: {c['name']}" for c in classes[:2]],
                "confidence": 0.8,
                "suggestions": [
                    "Review functions",
                    "Analyze classes",
                    "Check imports",
                    "Optimize code",
                ],
            }
        elif functions:
            if len(functions) == 1:
                func = functions[0]
                return {
                    "question": f"I see the function '{func['name']}'. What would you like me to help with?",
                    "options": [
                        "Review the function",
                        "Optimize performance",
                        "Add error handling",
                        "Write tests",
                    ],
                    "confidence": 0.8,
                    "suggestions": [
                        "Code review",
                        "Performance optimization",
                        "Add tests",
                    ],
                }
            else:
                return {
                    "question": f"I see {len(functions)} functions. Which one would you like me to focus on?",
                    "options": [f["name"] for f in functions[:4]],
                    "confidence": 0.7,
                    "suggestions": [
                        "Review all functions",
                        "Focus on specific function",
                        "Check function interactions",
                    ],
                }
        elif classes:
            return {
                "question": f"I see {len(classes)} classes. What would you like me to help with?",
                "options": [f"Class: {c['name']}" for c in classes[:3]]
                + ["Class relationships", "Design patterns"],
                "confidence": 0.7,
                "suggestions": [
                    "Review class design",
                    "Check inheritance",
                    "Optimize structure",
                ],
            }
        else:
            return {
                "question": "I see some code but couldn't identify specific functions or classes. What would you like me to help with?",
                "options": [
                    "Code review",
                    "Add functionality",
                    "Fix bugs",
                    "Optimize performance",
                ],
                "confidence": 0.6,
                "suggestions": [
                    "General code review",
                    "Add features",
                    "Performance optimization",
                ],
            }

    def analyze(self, code: str, context: dict[str, Any] = None) -> MultiModalResult:
        """
        Analyze code and generate clarification questions

        Args:
            code: Code string to analyze
            context: Additional context for analysis

        Returns:
            MultiModalResult with clarification information
        """
        try:
            # Detect language
            language = self._detect_language(code)

            # Perform analysis based on language and mode
            if language == "python" and self.analysis_mode == "ast":
                analysis = self._analyze_python_ast(code)
            else:
                # For other languages or LLM mode, use basic analysis
                analysis = {
                    "valid": True,
                    "language": language,
                    "lines": len(code.split("\n")),
                    "characters": len(code),
                }

            # Generate question
            question_data = self._generate_code_question(analysis, language)

            return MultiModalResult(
                needs_clarification=True,
                input_type="code",
                question=question_data["question"],
                options=question_data["options"],
                confidence=question_data["confidence"],
                reasoning=f"Code analysis: {language} code with {analysis.get('functions', [])} functions, {analysis.get('classes', [])} classes",
                metadata={
                    "language": language,
                    "analysis": analysis,
                    "analysis_mode": self.analysis_mode,
                },
                suggestions=question_data.get("suggestions"),
                domain="code",
            )

        except Exception as e:
            logger.error(f"CodeClarifier analysis failed: {e}")
            return MultiModalResult(
                needs_clarification=True,
                input_type="code",
                question="I encountered an error analyzing the code. Could you tell me what you'd like me to help with?",
                options=[
                    "Code review",
                    "Bug fixing",
                    "Add features",
                    "Optimize performance",
                ],
                confidence=0.5,
                reasoning=f"Analysis error: {str(e)}",
                metadata={"error": str(e)},
            )


class TextClarifier:
    """
    Enhanced text clarification that extends Phase 2 capabilities.
    Integrates with existing contextual clarification.
    """

    def __init__(self, config: dict[str, Any], context_aware_clarifier=None):
        self.config = config
        self.analysis_mode = config.get("text_analysis", "enhanced")
        self.context_aware_clarifier = context_aware_clarifier

    def _enhanced_text_analysis(
        self, text: str, context: dict[str, Any] = None
    ) -> dict[str, Any]:
        """Enhanced text analysis with domain detection and intent classification"""
        text_lower = text.lower()

        # Domain detection
        domain_indicators = {
            "web": [
                "website",
                "app",
                "frontend",
                "backend",
                "api",
                "react",
                "vue",
                "angular",
            ],
            "data": [
                "data",
                "csv",
                "json",
                "database",
                "sql",
                "analysis",
                "visualization",
            ],
            "ml": [
                "model",
                "ai",
                "machine learning",
                "neural",
                "training",
                "prediction",
            ],
            "devops": [
                "deploy",
                "docker",
                "kubernetes",
                "ci/cd",
                "infrastructure",
                "cloud",
            ],
            "security": [
                "security",
                "auth",
                "encryption",
                "vulnerability",
                "penetration",
            ],
            "performance": [
                "optimize",
                "performance",
                "speed",
                "efficiency",
                "scalability",
            ],
        }

        detected_domains = []
        for domain, indicators in domain_indicators.items():
            if any(indicator in text_lower for indicator in indicators):
                detected_domains.append(domain)

        # Intent classification
        intent_indicators = {
            "create": ["create", "build", "make", "develop", "generate"],
            "fix": ["fix", "debug", "error", "bug", "issue", "problem"],
            "optimize": ["optimize", "improve", "enhance", "better", "faster"],
            "explain": ["explain", "how", "what", "why", "understand"],
            "review": ["review", "check", "analyze", "evaluate", "assess"],
        }

        detected_intents = []
        for intent, indicators in intent_indicators.items():
            if any(indicator in text_lower for indicator in indicators):
                detected_intents.append(intent)

        return {
            "domains": detected_domains,
            "intents": detected_intents,
            "length": len(text),
            "word_count": len(text.split()),
            "has_technical_terms": any(
                term in text_lower
                for term in ["api", "database", "algorithm", "framework", "library"]
            ),
        }

    def analyze(self, text: str, context: dict[str, Any] = None) -> MultiModalResult:
        """
        Analyze text and generate clarification questions

        Args:
            text: Text to analyze
            context: Additional context for analysis

        Returns:
            MultiModalResult with clarification information
        """
        try:
            # Enhanced analysis
            analysis = self._enhanced_text_analysis(text, context)

            # Use context-aware clarifier if available
            if self.context_aware_clarifier and context:
                try:
                    conversation_history = context.get("conversation_history", [])
                    project_context = context.get("project_context", {})

                    result = self.context_aware_clarifier.make_question(
                        text, conversation_history, project_context
                    )

                    return MultiModalResult(
                        needs_clarification=result.get("confidence", 0.5) < 0.8,
                        input_type="text",
                        question=result.get("question"),
                        options=result.get("options", []),
                        confidence=result.get("confidence", 0.5),
                        reasoning=result.get("reasoning", "Enhanced text analysis"),
                        metadata={
                            "analysis": analysis,
                            "context_aware": True,
                            "source": result.get("source", "enhanced"),
                        },
                        domain=result.get("domain"),
                    )
                except Exception as e:
                    logger.warning(f"Context-aware clarification failed: {e}")

            # Fallback to basic analysis
            domains = analysis.get("domains", [])
            intents = analysis.get("intents", [])

            if domains and intents:
                primary_domain = domains[0]
                primary_intent = intents[0]

                question = f"I understand you want to {primary_intent} something related to {primary_domain}. Could you be more specific?"
                options = [
                    f"{primary_intent.title()} {primary_domain} component",
                    f"{primary_intent.title()} {primary_domain} architecture",
                    f"{primary_intent.title()} {primary_domain} performance",
                ]
                confidence = 0.7
            else:
                question = "Could you provide more details about what you'd like me to help with?"
                options = [
                    "Provide more context",
                    "Give specific examples",
                    "Clarify the goal",
                ]
                confidence = 0.5

            return MultiModalResult(
                needs_clarification=True,
                input_type="text",
                question=question,
                options=options,
                confidence=confidence,
                reasoning=f"Enhanced text analysis: domains={domains}, intents={intents}",
                metadata={"analysis": analysis, "context_aware": False},
                domain=domains[0] if domains else "generic",
            )

        except Exception as e:
            logger.error(f"TextClarifier analysis failed: {e}")
            return MultiModalResult(
                needs_clarification=True,
                input_type="text",
                question="I need more information to help you effectively. Could you provide more details?",
                options=[
                    "Provide more context",
                    "Give specific examples",
                    "Clarify the goal",
                ],
                confidence=0.5,
                reasoning=f"Analysis error: {str(e)}",
                metadata={"error": str(e)},
            )


class MultiModalClarifier:
    """
    Main orchestrator for multi-modal clarification.
    Routes inputs to appropriate clarifiers based on content type.
    """

    def __init__(self, config: dict[str, Any], context_aware_clarifier=None):
        self.config = config
        self.enabled = config.get("enabled", True)

        # Initialize clarifiers
        self.visual_clarifier = VisualClarifier(config)
        self.code_clarifier = CodeClarifier(config)
        self.text_clarifier = TextClarifier(config, context_aware_clarifier)

        # Input detection patterns
        self.code_patterns = [
            r"```[\w]*\n.*?\n```",  # Code blocks
            r"def\s+\w+\s*\(",  # Python functions
            r"function\s+\w+\s*\(",  # JavaScript functions
            r"class\s+\w+",  # Classes
            r"import\s+\w+",  # Imports
        ]

        self.image_patterns = [
            r"data:image/[^;]+;base64,",  # Base64 images
            r"\.(jpg|jpeg|png|gif|webp)",  # Image file extensions
        ]

    def _detect_input_type(self, content: str) -> str:
        """Detect the primary type of input content"""
        # Check for code patterns
        for pattern in self.code_patterns:
            if re.search(pattern, content, re.DOTALL | re.IGNORECASE):
                return "code"

        # Check for image patterns
        for pattern in self.image_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return "image"

        # Check for mixed content
        has_code = any(
            re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            for pattern in self.code_patterns
        )
        has_image = any(
            re.search(pattern, content, re.IGNORECASE)
            for pattern in self.image_patterns
        )

        if has_code and has_image:
            return "mixed"
        elif has_code:
            return "code"
        elif has_image:
            return "image"
        else:
            return "text"

    def _extract_code_blocks(self, content: str) -> list[str]:
        """Extract code blocks from mixed content"""
        code_blocks = []
        # Extract ```code``` blocks
        pattern = r"```[\w]*\n(.*?)\n```"
        matches = re.findall(pattern, content, re.DOTALL)
        code_blocks.extend(matches)

        # Extract inline code patterns
        for pattern in self.code_patterns[1:]:  # Skip the ``` pattern
            matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
            code_blocks.extend(matches)

        return code_blocks

    def _extract_image_data(self, content: str) -> list[str]:
        """Extract image data from mixed content"""
        images = []
        # Extract base64 images
        pattern = r"data:image/[^;]+;base64,([A-Za-z0-9+/=]+)"
        matches = re.findall(pattern, content)
        images.extend(matches)

        # Extract image file references
        pattern = r"[^\s]+\.(jpg|jpeg|png|gif|webp)"
        matches = re.findall(pattern, content, re.IGNORECASE)
        images.extend(matches)

        return images

    def analyze(self, content: str, context: dict[str, Any] = None) -> MultiModalResult:
        """
        Analyze multi-modal content and generate appropriate clarification

        Args:
            content: Input content (text, code, image, or mixed)
            context: Additional context for analysis

        Returns:
            MultiModalResult with clarification information
        """
        if not self.enabled:
            return MultiModalResult(
                needs_clarification=False,
                input_type="text",
                question=None,
                options=None,
                confidence=1.0,
                reasoning="Multi-modal clarification disabled",
                metadata={"disabled": True},
            )

        try:
            # Detect input type
            input_type = self._detect_input_type(content)

            if input_type == "text":
                return self.text_clarifier.analyze(content, context)

            elif input_type == "code":
                # Extract and analyze code
                code_blocks = self._extract_code_blocks(content)
                if code_blocks:
                    # Use the largest code block
                    main_code = max(code_blocks, key=len)
                    return self.code_clarifier.analyze(main_code, context)
                else:
                    return self.text_clarifier.analyze(content, context)

            elif input_type == "image":
                # Extract and analyze image
                image_data = self._extract_image_data(content)
                if image_data:
                    # Use the first image
                    return self.visual_clarifier.analyze(image_data[0], context)
                else:
                    return self.text_clarifier.analyze(content, context)

            elif input_type == "mixed":
                # Handle mixed content
                code_blocks = self._extract_code_blocks(content)
                image_data = self._extract_image_data(content)

                if code_blocks and image_data:
                    return MultiModalResult(
                        needs_clarification=True,
                        input_type="mixed",
                        question="I see both code and images. What would you like me to focus on?",
                        options=[
                            "Analyze the code",
                            "Analyze the images",
                            "Analyze both together",
                            "Focus on specific part",
                        ],
                        confidence=0.8,
                        reasoning="Mixed content detected: code and images",
                        metadata={
                            "code_blocks": len(code_blocks),
                            "images": len(image_data),
                            "mixed_content": True,
                        },
                        suggestions=[
                            "Code analysis",
                            "Image analysis",
                            "Combined analysis",
                        ],
                    )
                elif code_blocks:
                    return self.code_clarifier.analyze(code_blocks[0], context)
                elif image_data:
                    return self.visual_clarifier.analyze(image_data[0], context)
                else:
                    return self.text_clarifier.analyze(content, context)

            else:
                # Fallback to text analysis
                return self.text_clarifier.analyze(content, context)

        except Exception as e:
            logger.error(f"MultiModalClarifier analysis failed: {e}")
            return MultiModalResult(
                needs_clarification=True,
                input_type="unknown",
                question="I encountered an error analyzing your input. Could you provide more details?",
                options=[
                    "Provide more context",
                    "Try different format",
                    "Describe what you need",
                ],
                confidence=0.5,
                reasoning=f"Analysis error: {str(e)}",
                metadata={"error": str(e)},
            )
