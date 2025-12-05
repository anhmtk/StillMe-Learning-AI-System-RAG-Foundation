"""
Code Review Assistant for StillMe Codebase Assistant

Phase 2.2: Analyze code for issues and generate review comments.
Safety: Review only, no auto-fix.
"""

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import os
import ast
import re

logger = logging.getLogger(__name__)


class CodeReviewer:
    """
    Analyzes code for issues and generates review comments.
    
    Safety Rules:
    - Only reviews code, never modifies it
    - Returns suggestions as comments (user must review before applying)
    - No automatic fixes or code changes
    """
    
    def __init__(self, codebase_indexer=None, llm_provider="deepseek", llm_api_key=None):
        """
        Initialize CodeReviewer.
        
        Args:
            codebase_indexer: CodebaseIndexer instance for retrieving code context
            llm_provider: LLM provider name ("deepseek", "openrouter", etc.)
            llm_api_key: API key for LLM provider
        """
        self.codebase_indexer = codebase_indexer
        self.llm_provider = llm_provider
        self.llm_api_key = llm_api_key or os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENROUTER_API_KEY")
        
        if not self.llm_api_key:
            logger.warning("No LLM API key provided - code review will fail")
    
    async def review_code(
        self,
        code_content: str,
        file_path: Optional[str] = None,
        check_style: bool = True,
        check_security: bool = True,
        check_performance: bool = True
    ) -> Dict[str, Any]:
        """
        Review code and generate review comments.
        
        Args:
            code_content: Source code content to review
            file_path: Optional file path for context
            check_style: Whether to check code style issues
            check_security: Whether to check security issues
            check_performance: Whether to check performance issues
        
        Returns:
            Dictionary with:
            - issues: List of issues found (with severity, line, message, suggestion)
            - summary: Summary statistics
            - score: Overall code quality score (0-100)
        """
        issues = []
        
        # Static analysis (AST-based)
        static_issues = self._static_analysis(code_content, file_path)
        issues.extend(static_issues)
        
        # LLM-based analysis (for complex issues)
        llm_issues = await self._llm_analysis(
            code_content=code_content,
            file_path=file_path,
            check_style=check_style,
            check_security=check_security,
            check_performance=check_performance
        )
        issues.extend(llm_issues)
        
        # Calculate score and summary
        score = self._calculate_score(issues)
        summary = self._generate_summary(issues)
        
        return {
            "issues": issues,
            "summary": summary,
            "score": score,
            "file_path": file_path
        }
    
    def _static_analysis(self, code_content: str, file_path: Optional[str]) -> List[Dict[str, Any]]:
        """Perform static analysis using AST."""
        issues = []
        
        try:
            tree = ast.parse(code_content)
            
            # Check for unused imports
            unused_imports = self._check_unused_imports(tree, code_content)
            issues.extend(unused_imports)
            
            # Check for unreachable code
            unreachable = self._check_unreachable_code(tree)
            issues.extend(unreachable)
            
            # Check for missing error handling
            missing_error_handling = self._check_error_handling(tree)
            issues.extend(missing_error_handling)
            
            # Check for naming inconsistencies
            naming_issues = self._check_naming(tree)
            issues.extend(naming_issues)
            
        except SyntaxError as e:
            issues.append({
                "severity": "error",
                "line": e.lineno or 0,
                "type": "syntax_error",
                "message": f"Syntax error: {e.msg}",
                "suggestion": "Fix syntax error before reviewing"
            })
        except Exception as e:
            logger.warning(f"Static analysis failed: {e}")
        
        return issues
    
    def _check_unused_imports(self, tree: ast.AST, code_content: str) -> List[Dict[str, Any]]:
        """Check for unused imports."""
        issues = []
        
        # Get all imports
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module.split('.')[0])
                for alias in node.names:
                    imports.append(alias.name)
        
        # Check if imports are used
        for imp in set(imports):
            # Simple heuristic: check if import name appears in code (not in import statements)
            pattern = r'\b' + re.escape(imp) + r'\b'
            matches = re.findall(pattern, code_content)
            # Count matches outside import lines
            import_lines = [i for i, line in enumerate(code_content.split('\n'), 1) if 'import' in line]
            usage_count = 0
            for i, line in enumerate(code_content.split('\n'), 1):
                if i not in import_lines and re.search(pattern, line):
                    usage_count += 1
            
            if usage_count == 0:
                issues.append({
                    "severity": "info",
                    "line": 0,  # Could be improved to find exact line
                    "type": "unused_import",
                    "message": f"Unused import: {imp}",
                    "suggestion": f"Remove unused import: {imp}"
                })
        
        return issues
    
    def _check_unreachable_code(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Check for unreachable code (e.g., after return statements)."""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check for code after return in function
                has_return = False
                for stmt in node.body:
                    if isinstance(stmt, ast.Return):
                        has_return = True
                    elif has_return and not isinstance(stmt, (ast.Pass, ast.Ellipsis)):
                        # Code after return (simplified check)
                        issues.append({
                            "severity": "warning",
                            "line": stmt.lineno if hasattr(stmt, 'lineno') else 0,
                            "type": "unreachable_code",
                            "message": "Code after return statement may be unreachable",
                            "suggestion": "Review logic - code after return may never execute"
                        })
        
        return issues
    
    def _check_error_handling(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Check for missing error handling."""
        issues = []
        
        for node in ast.walk(tree):
            # Check for file operations without try-except
            if isinstance(node, ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                
                # Common operations that should have error handling
                risky_operations = ['open', 'read', 'write', 'remove', 'mkdir', 'chmod']
                if func_name in risky_operations:
                    # Check if in try-except
                    parent = node
                    in_try = False
                    while parent:
                        if isinstance(parent, ast.Try):
                            in_try = True
                            break
                        parent = getattr(parent, 'parent', None)
                    
                    if not in_try:
                        issues.append({
                            "severity": "warning",
                            "line": node.lineno if hasattr(node, 'lineno') else 0,
                            "type": "missing_error_handling",
                            "message": f"Missing error handling for {func_name}()",
                            "suggestion": f"Wrap {func_name}() in try-except block"
                        })
        
        return issues
    
    def _check_naming(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Check for naming inconsistencies."""
        issues = []
        
        for node in ast.walk(tree):
            # Check function names (should be snake_case)
            if isinstance(node, ast.FunctionDef):
                name = node.name
                if not re.match(r'^[a-z_][a-z0-9_]*$', name) and not name.startswith('_'):
                    issues.append({
                        "severity": "info",
                        "line": node.lineno if hasattr(node, 'lineno') else 0,
                        "type": "naming_inconsistency",
                        "message": f"Function name '{name}' doesn't follow snake_case convention",
                        "suggestion": f"Consider renaming to snake_case: {re.sub(r'([A-Z])', r'_\1', name).lower()}"
                    })
            
            # Check class names (should be PascalCase)
            elif isinstance(node, ast.ClassDef):
                name = node.name
                if not re.match(r'^[A-Z][a-zA-Z0-9]*$', name):
                    issues.append({
                        "severity": "info",
                        "line": node.lineno if hasattr(node, 'lineno') else 0,
                        "type": "naming_inconsistency",
                        "message": f"Class name '{name}' doesn't follow PascalCase convention",
                        "suggestion": f"Consider renaming to PascalCase"
                    })
        
        return issues
    
    async def _llm_analysis(
        self,
        code_content: str,
        file_path: Optional[str],
        check_style: bool,
        check_security: bool,
        check_performance: bool
    ) -> List[Dict[str, Any]]:
        """Perform LLM-based analysis for complex issues."""
        try:
            from backend.api.utils.chat_helpers import generate_ai_response
            
            # Build prompt
            prompt = self._build_review_prompt(
                code_content=code_content,
                file_path=file_path,
                check_style=check_style,
                check_security=check_security,
                check_performance=check_performance
            )
            
            # Get LLM response
            response = await generate_ai_response(
                prompt=prompt,
                detected_lang="en",
                llm_provider=self.llm_provider,
                llm_api_key=self.llm_api_key,
                use_server_keys=True,
                question="Review code for issues",
                task_type="code_review"
            )
            
            # Parse LLM response into issues
            issues = self._parse_llm_response(response)
            return issues
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}", exc_info=True)
            return []
    
    def _build_review_prompt(
        self,
        code_content: str,
        file_path: Optional[str],
        check_style: bool,
        check_security: bool,
        check_performance: bool
    ) -> str:
        """Build prompt for LLM code review."""
        
        checks = []
        if check_style:
            checks.append("- Code style and conventions")
        if check_security:
            checks.append("- Security vulnerabilities")
        if check_performance:
            checks.append("- Performance issues")
        
        prompt = f"""You are a code review assistant for the StillMe codebase.

## Task
Review the following code and identify issues. Return ONLY a JSON array of issues.

## Code to Review
File: {file_path or 'provided code'}
```python
{code_content}
```

## Review Focus
{chr(10).join(f'- {check}' for check in checks)}

## Issue Format
Return a JSON array with this structure:
[
  {{
    "severity": "error|warning|info",
    "line": <line_number>,
    "type": "<issue_type>",
    "message": "<description>",
    "suggestion": "<how to fix>"
  }}
]

## Severity Levels
- error: Critical issues that must be fixed
- warning: Issues that should be addressed
- info: Suggestions for improvement

## Safety Rules
- ONLY review code, do NOT suggest modifications that change behavior
- Focus on code quality, not feature changes
- Be specific and actionable

## Output
Return ONLY the JSON array, no other text.
"""
        return prompt
    
    def _parse_llm_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response into structured issues."""
        import json
        
        issues = []
        
        try:
            # Try to extract JSON from response
            # Remove markdown code blocks if present
            response_clean = response.strip()
            if response_clean.startswith("```"):
                # Extract JSON from code block
                lines = response_clean.split('\n')
                json_lines = []
                in_json = False
                for line in lines:
                    if line.strip().startswith("```"):
                        in_json = not in_json
                        continue
                    if in_json:
                        json_lines.append(line)
                response_clean = '\n'.join(json_lines)
            
            # Parse JSON
            parsed = json.loads(response_clean)
            if isinstance(parsed, list):
                issues = parsed
            elif isinstance(parsed, dict) and "issues" in parsed:
                issues = parsed["issues"]
        
        except json.JSONDecodeError:
            logger.warning("Could not parse LLM response as JSON")
        except Exception as e:
            logger.warning(f"Error parsing LLM response: {e}")
        
        return issues
    
    def _calculate_score(self, issues: List[Dict[str, Any]]) -> int:
        """Calculate overall code quality score (0-100)."""
        if not issues:
            return 100
        
        # Weight by severity
        error_weight = 10
        warning_weight = 5
        info_weight = 1
        
        total_penalty = 0
        for issue in issues:
            severity = issue.get("severity", "info")
            if severity == "error":
                total_penalty += error_weight
            elif severity == "warning":
                total_penalty += warning_weight
            else:
                total_penalty += info_weight
        
        # Score = 100 - penalty (capped at 0)
        score = max(0, 100 - total_penalty)
        return score
    
    def _generate_summary(self, issues: List[Dict[str, Any]]) -> Dict[str, int]:
        """Generate summary statistics."""
        summary = {
            "total": len(issues),
            "errors": sum(1 for i in issues if i.get("severity") == "error"),
            "warnings": sum(1 for i in issues if i.get("severity") == "warning"),
            "info": sum(1 for i in issues if i.get("severity") == "info")
        }
        return summary


def get_code_reviewer(codebase_indexer=None):
    """
    Get or create CodeReviewer singleton instance.
    
    Args:
        codebase_indexer: Optional CodebaseIndexer instance
    
    Returns:
        CodeReviewer instance
    """
    global _code_reviewer_instance
    
    if _code_reviewer_instance is None:
        _code_reviewer_instance = CodeReviewer(codebase_indexer=codebase_indexer)
    
    return _code_reviewer_instance


_code_reviewer_instance = None

