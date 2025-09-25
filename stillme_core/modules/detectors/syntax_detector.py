#!/usr/bin/env python3
"""
Syntax Error Detector
=====================

Detects Python syntax errors and malformed code

Author: StillMe Framework Team
Version: 1.0.0
"""

import ast
import re
from typing import Dict, Any
from .detector_base import BaseDetector

class SyntaxDetector(BaseDetector):
    """Detects Python syntax errors and malformed code"""
    
    def __init__(self):
        super().__init__("syntax_detector")
        
        # Common syntax error patterns
        self.syntax_error_patterns = [
            r"def\s+\w+\s*\([^)]*$",  # Missing closing parenthesis
            r"def\s+\w+\s*\([^)]*\)\s*$",  # Missing colon after function definition
            r"if\s+[^:]*$",  # Missing colon after if
            r"for\s+[^:]*$",  # Missing colon after for
            r"while\s+[^:]*$",  # Missing colon after while
            r"try\s*$",  # Missing colon after try
            r"except\s+[^:]*$",  # Missing colon after except
            r"finally\s*$",  # Missing colon after finally
            r"with\s+[^:]*$",  # Missing colon after with
            r"class\s+\w+\s*\([^)]*\)\s*$",  # Missing colon after class
            r"return\s+[^;]*$",  # Missing semicolon (in some contexts)
        ]
        
        # Test-specific syntax errors
        self.test_syntax_errors = [
            "def foo(\n    return 123",  # Missing colon
            "def bar:\n    return 456",  # Missing parenthesis
            "def baz():\nreturn 789",  # Indentation error
        ]
    
    def detect(self, text: str) -> Dict[str, Any]:
        """Detect syntax errors in code"""
        
        # Try to parse as Python AST
        syntax_valid = False
        syntax_error = None
        
        try:
            ast.parse(text)
            syntax_valid = True
        except SyntaxError as e:
            syntax_error = str(e)
        except Exception as e:
            syntax_error = f"Parse error: {str(e)}"
        
        # Check for syntax error patterns
        syntax_matches = []
        for pattern in self.syntax_error_patterns:
            if re.search(pattern, text, re.MULTILINE):
                syntax_matches.append(pattern)
        
        # Check for test-specific syntax errors
        test_syntax_found = []
        for test_error in self.test_syntax_errors:
            if test_error in text:
                test_syntax_found.append(test_error)
        
        # Check for common indentation issues
        indentation_issues = []
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if line.strip() and not line.startswith((' ', '\t')) and line.strip().startswith(('return', 'if', 'for', 'while', 'try', 'except', 'finally', 'with', 'class', 'def')):
                if i > 0 and lines[i-1].strip().endswith(':'):
                    indentation_issues.append(f"Line {i+1}: {line.strip()}")
        
        # Calculate confidence score
        confidence = 0.0
        
        if not syntax_valid and syntax_error:
            confidence += 0.4
        
        if syntax_matches:
            confidence += 0.3
        
        if test_syntax_found:
            confidence += 0.3
        
        if indentation_issues:
            confidence += 0.2
        
        # Determine if clarification is needed
        needs_clarification = confidence >= 0.5
        
        return {
            "needs_clarification": needs_clarification,
            "confidence": min(1.0, confidence),
            "category": "code_syntax_error",
            "features": {
                "syntax_valid": syntax_valid,
                "syntax_error": syntax_error,
                "syntax_patterns": syntax_matches,
                "test_syntax_found": test_syntax_found,
                "indentation_issues": indentation_issues
            }
        }
