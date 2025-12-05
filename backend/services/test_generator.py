"""
Test Generator Service for StillMe Codebase Assistant

Phase 2.1: Generate unit tests for code files using LLM with code context.
Safety: Generate tests only, no code modifications.
"""

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import os

logger = logging.getLogger(__name__)


class TestGenerator:
    """
    Generates unit tests for code files using LLM with codebase context.
    
    Safety Rules:
    - Only generates test code, never modifies source code
    - Tests are returned as strings (user must review before using)
    - No automatic file writing or execution
    """
    
    def __init__(self, codebase_indexer=None, llm_provider="deepseek", llm_api_key=None):
        """
        Initialize TestGenerator.
        
        Args:
            codebase_indexer: CodebaseIndexer instance for retrieving code context
            llm_provider: LLM provider name ("deepseek", "openrouter", etc.)
            llm_api_key: API key for LLM provider
        """
        self.codebase_indexer = codebase_indexer
        self.llm_provider = llm_provider
        self.llm_api_key = llm_api_key or os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENROUTER_API_KEY")
        
        if not self.llm_api_key:
            logger.warning("No LLM API key provided - test generation will fail")
    
    async def generate_tests(
        self,
        file_path: Optional[str] = None,
        code_content: Optional[str] = None,
        test_framework: str = "pytest",
        include_edge_cases: bool = True,
        include_error_handling: bool = True
    ) -> Dict[str, Any]:
        """
        Generate unit tests for a code file.
        
        Args:
            file_path: Path to source file (relative to project root)
            code_content: Source code content (if file_path not provided)
            test_framework: Test framework to use ("pytest", "unittest")
            include_edge_cases: Whether to include edge case tests
            include_error_handling: Whether to include error handling tests
        
        Returns:
            Dictionary with:
            - test_code: Generated test code as string
            - test_file_path: Suggested test file path
            - coverage_estimate: Estimated coverage (percentage)
            - test_cases: List of test case descriptions
        """
        if not file_path and not code_content:
            raise ValueError("Either file_path or code_content must be provided")
        
        # Get code content if file_path provided
        if file_path and not code_content:
            project_root = Path.cwd()
            full_path = project_root / file_path
            if not full_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            code_content = full_path.read_text(encoding="utf-8")
        
        # Retrieve related code context from codebase
        related_code = []
        if self.codebase_indexer:
            try:
                # Query for related code (imports, dependencies, similar patterns)
                query = f"code related to {file_path or 'this code'}"
                results = self.codebase_indexer.query_codebase(query, n_results=5)
                related_code = results
            except Exception as e:
                logger.warning(f"Could not retrieve code context: {e}")
        
        # Build prompt for test generation
        prompt = self._build_test_generation_prompt(
            code_content=code_content,
            file_path=file_path,
            test_framework=test_framework,
            include_edge_cases=include_edge_cases,
            include_error_handling=include_error_handling,
            related_code=related_code
        )
        
        # Generate tests using LLM
        test_code = await self._generate_with_llm(prompt)
        
        # Parse and analyze generated tests
        test_cases = self._extract_test_cases(test_code, test_framework)
        coverage_estimate = self._estimate_coverage(code_content, test_code)
        
        # Suggest test file path
        test_file_path = self._suggest_test_file_path(file_path)
        
        return {
            "test_code": test_code,
            "test_file_path": test_file_path,
            "coverage_estimate": coverage_estimate,
            "test_cases": test_cases,
            "framework": test_framework
        }
    
    def _build_test_generation_prompt(
        self,
        code_content: str,
        file_path: Optional[str],
        test_framework: str,
        include_edge_cases: bool,
        include_error_handling: bool,
        related_code: List[Dict[str, Any]]
    ) -> str:
        """Build prompt for LLM to generate tests."""
        
        # Build related code context
        related_context = ""
        if related_code:
            related_context = "\n\n## Related Code Context:\n"
            for i, chunk in enumerate(related_code[:3], 1):  # Limit to 3 chunks
                metadata = chunk.get("metadata", {})
                related_context += f"\n### Related Code {i}:\n"
                related_context += f"File: {metadata.get('file_path', 'unknown')}\n"
                related_context += f"Lines: {metadata.get('line_start', '?')}-{metadata.get('line_end', '?')}\n"
                related_context += f"Code:\n{chunk.get('document', '')[:500]}\n"  # Limit length
        
        # Build requirements
        requirements = []
        requirements.append("1. Happy path tests (normal operation)")
        if include_edge_cases:
            requirements.append("2. Edge cases (boundary conditions, empty inputs, None values)")
        if include_error_handling:
            requirements.append("3. Error handling (invalid inputs, exceptions)")
        requirements.append("4. Use proper pytest fixtures if needed")
        requirements.append("5. Include docstrings for each test function")
        requirements.append("6. Follow pytest naming conventions (test_*.py, test_* functions)")
        
        prompt = f"""You are a test generation assistant for the StillMe codebase.

## Task
Generate comprehensive unit tests for the following code using {test_framework}.

## Source Code
File: {file_path or 'provided code'}
```python
{code_content}
```

{related_context}

## Requirements
{chr(10).join(f'- {req}' for req in requirements)}

## Safety Rules
- ONLY generate test code, do NOT modify the source code
- Do NOT suggest changes to the source code
- Generate tests that verify the code works as written
- Use proper imports and fixtures
- Make tests independent and isolated

## Output Format
Generate ONLY the test code, starting with imports and ending with test functions.
Do not include explanations or comments outside the code.
Use proper {test_framework} syntax.

## Test Code:
"""
        return prompt
    
    async def _generate_with_llm(self, prompt: str) -> str:
        """Generate test code using LLM."""
        try:
            from backend.api.utils.chat_helpers import generate_ai_response
            
            response = await generate_ai_response(
                prompt=prompt,
                detected_lang="en",
                llm_provider=self.llm_provider,
                llm_api_key=self.llm_api_key,
                use_server_keys=True,
                question="Generate unit tests",
                task_type="code_generation"
            )
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Failed to generate tests with LLM: {e}", exc_info=True)
            raise RuntimeError(f"Test generation failed: {str(e)}")
    
    def _extract_test_cases(self, test_code: str, framework: str) -> List[str]:
        """Extract test case descriptions from generated test code."""
        test_cases = []
        
        if framework == "pytest":
            # Look for test_* functions
            import re
            pattern = r'def\s+(test_\w+)\s*\([^)]*\)\s*:'
            matches = re.findall(pattern, test_code)
            test_cases = matches
        
        return test_cases
    
    def _estimate_coverage(self, source_code: str, test_code: str) -> int:
        """Estimate test coverage percentage (rough estimate)."""
        # Simple heuristic: count functions/classes in source vs tests
        import re
        
        # Count functions/classes in source
        source_functions = len(re.findall(r'def\s+\w+\s*\(', source_code))
        source_classes = len(re.findall(r'class\s+\w+', source_code))
        source_total = source_functions + source_classes
        
        # Count test functions
        test_functions = len(re.findall(r'def\s+test_\w+\s*\(', test_code))
        
        if source_total == 0:
            return 0
        
        # Rough estimate: assume each test covers one function/class
        coverage = min(100, int((test_functions / source_total) * 100))
        return coverage
    
    def _suggest_test_file_path(self, source_file_path: Optional[str]) -> str:
        """Suggest test file path based on source file path."""
        if not source_file_path:
            return "tests/test_generated.py"
        
        # Convert source path to test path
        # e.g., backend/services/validator.py -> tests/backend/services/test_validator.py
        path = Path(source_file_path)
        
        # Remove extension and add test_ prefix
        test_name = f"test_{path.stem}.py"
        
        # Keep directory structure, prepend tests/
        if path.parent != Path("."):
            test_path = Path("tests") / path.parent / test_name
        else:
            test_path = Path("tests") / test_name
        
        return str(test_path)


def get_test_generator(codebase_indexer=None):
    """
    Get or create TestGenerator singleton instance.
    
    Args:
        codebase_indexer: Optional CodebaseIndexer instance
    
    Returns:
        TestGenerator instance
    """
    global _test_generator_instance
    
    if _test_generator_instance is None:
        _test_generator_instance = TestGenerator(codebase_indexer=codebase_indexer)
    
    return _test_generator_instance


_test_generator_instance = None

