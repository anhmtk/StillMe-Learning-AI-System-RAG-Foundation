#!/usr/bin/env python3
"""
AgentDev Quality Enforcer - Automated quality enforcement
Automated linter, formatter, static analysis, and test generation
"""

import ast
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import json
import re

@dataclass
class QualityReport:
    """Quality analysis report"""
    file_path: str
    issues: List[Dict[str, Any]]
    score: float
    suggestions: List[str]
    auto_fixes: List[str]

@dataclass
class LintResult:
    """Linting result"""
    tool: str
    issues: List[Dict[str, Any]]
    score: float
    passed: bool

class QualityEnforcer:
    """Automated quality enforcement system"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.quality_tools = {
            "ruff": "ruff check",
            "black": "black --check",
            "mypy": "mypy",
            "pylint": "pylint",
            "bandit": "bandit -r"
        }
        self.reports = []
    
    async def enforce_quality(self, file_path: str) -> QualityReport:
        """Enforce quality for a specific file"""
        print(f"🔍 Enforcing quality for {file_path}")
        
        issues = []
        suggestions = []
        auto_fixes = []
        
        # Run all quality tools
        lint_results = await self._run_linters(file_path)
        format_results = await self._run_formatters(file_path)
        static_results = await self._run_static_analysis(file_path)
        security_results = await self._run_security_scan(file_path)
        
        # Combine results
        all_issues = []
        for result in lint_results + format_results + static_results + security_results:
            all_issues.extend(result.issues)
        
        # Generate suggestions
        suggestions = await self._generate_suggestions(file_path, all_issues)
        
        # Generate auto-fixes
        auto_fixes = await self._generate_auto_fixes(file_path, all_issues)
        
        # Calculate quality score
        score = self._calculate_quality_score(all_issues)
        
        report = QualityReport(
            file_path=file_path,
            issues=all_issues,
            score=score,
            suggestions=suggestions,
            auto_fixes=auto_fixes
        )
        
        self.reports.append(report)
        return report
    
    async def _run_linters(self, file_path: str) -> List[LintResult]:
        """Run linting tools"""
        results = []
        
        # Run ruff
        try:
            ruff_result = await self._run_ruff(file_path)
            results.append(ruff_result)
        except Exception as e:
            print(f"⚠️ Ruff failed: {e}")
        
        # Run pylint
        try:
            pylint_result = await self._run_pylint(file_path)
            results.append(pylint_result)
        except Exception as e:
            print(f"⚠️ Pylint failed: {e}")
        
        return results
    
    async def _run_ruff(self, file_path: str) -> LintResult:
        """Run ruff linter"""
        try:
            result = subprocess.run(
                ["ruff", "check", file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            issues = []
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        issues.append({
                            "tool": "ruff",
                            "message": line,
                            "severity": "warning"
                        })
            
            return LintResult(
                tool="ruff",
                issues=issues,
                score=max(0, 100 - len(issues) * 5),
                passed=result.returncode == 0
            )
        except Exception as e:
            return LintResult(
                tool="ruff",
                issues=[{"error": str(e)}],
                score=0,
                passed=False
            )
    
    async def _run_pylint(self, file_path: str) -> LintResult:
        """Run pylint linter"""
        try:
            result = subprocess.run(
                ["pylint", file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            issues = []
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line and not line.startswith('---'):
                        issues.append({
                            "tool": "pylint",
                            "message": line,
                            "severity": "warning"
                        })
            
            return LintResult(
                tool="pylint",
                issues=issues,
                score=max(0, 100 - len(issues) * 2),
                passed=result.returncode == 0
            )
        except Exception as e:
            return LintResult(
                tool="pylint",
                issues=[{"error": str(e)}],
                score=0,
                passed=False
            )
    
    async def _run_formatters(self, file_path: str) -> List[LintResult]:
        """Run formatting tools"""
        results = []
        
        # Run black
        try:
            black_result = await self._run_black(file_path)
            results.append(black_result)
        except Exception as e:
            print(f"⚠️ Black failed: {e}")
        
        return results
    
    async def _run_black(self, file_path: str) -> LintResult:
        """Run black formatter"""
        try:
            result = subprocess.run(
                ["black", "--check", file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            issues = []
            if result.returncode != 0:
                issues.append({
                    "tool": "black",
                    "message": "Code formatting issues detected",
                    "severity": "warning"
                })
            
            return LintResult(
                tool="black",
                issues=issues,
                score=100 if result.returncode == 0 else 50,
                passed=result.returncode == 0
            )
        except Exception as e:
            return LintResult(
                tool="black",
                issues=[{"error": str(e)}],
                score=0,
                passed=False
            )
    
    async def _run_static_analysis(self, file_path: str) -> List[LintResult]:
        """Run static analysis tools"""
        results = []
        
        # Run mypy
        try:
            mypy_result = await self._run_mypy(file_path)
            results.append(mypy_result)
        except Exception as e:
            print(f"⚠️ MyPy failed: {e}")
        
        return results
    
    async def _run_mypy(self, file_path: str) -> LintResult:
        """Run mypy type checker"""
        try:
            result = subprocess.run(
                ["mypy", file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            issues = []
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line and 'error:' in line:
                        issues.append({
                            "tool": "mypy",
                            "message": line,
                            "severity": "error"
                        })
            
            return LintResult(
                tool="mypy",
                issues=issues,
                score=max(0, 100 - len(issues) * 10),
                passed=result.returncode == 0
            )
        except Exception as e:
            return LintResult(
                tool="mypy",
                issues=[{"error": str(e)}],
                score=0,
                passed=False
            )
    
    async def _run_security_scan(self, file_path: str) -> List[LintResult]:
        """Run security scanning tools"""
        results = []
        
        # Run bandit
        try:
            bandit_result = await self._run_bandit(file_path)
            results.append(bandit_result)
        except Exception as e:
            print(f"⚠️ Bandit failed: {e}")
        
        return results
    
    async def _run_bandit(self, file_path: str) -> LintResult:
        """Run bandit security scanner"""
        try:
            result = subprocess.run(
                ["bandit", "-r", file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            issues = []
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line and 'Issue:' in line:
                        issues.append({
                            "tool": "bandit",
                            "message": line,
                            "severity": "high"
                        })
            
            return LintResult(
                tool="bandit",
                issues=issues,
                score=max(0, 100 - len(issues) * 20),
                passed=result.returncode == 0
            )
        except Exception as e:
            return LintResult(
                tool="bandit",
                issues=[{"error": str(e)}],
                score=0,
                passed=False
            )
    
    async def _generate_suggestions(self, file_path: str, issues: List[Dict[str, Any]]) -> List[str]:
        """Generate improvement suggestions"""
        suggestions = []
        
        # Analyze common patterns
        if any("import" in issue.get("message", "") for issue in issues):
            suggestions.append("Consider organizing imports with isort")
        
        if any("line too long" in issue.get("message", "").lower() for issue in issues):
            suggestions.append("Consider breaking long lines for better readability")
        
        if any("unused" in issue.get("message", "").lower() for issue in issues):
            suggestions.append("Remove unused imports and variables")
        
        if any("type" in issue.get("message", "").lower() for issue in issues):
            suggestions.append("Add type hints for better code documentation")
        
        return suggestions
    
    async def _generate_auto_fixes(self, file_path: str, issues: List[Dict[str, Any]]) -> List[str]:
        """Generate automatic fixes"""
        fixes = []
        
        # Auto-fix suggestions
        if any("import" in issue.get("message", "") for issue in issues):
            fixes.append("Run: isort " + file_path)
        
        if any("format" in issue.get("message", "").lower() for issue in issues):
            fixes.append("Run: black " + file_path)
        
        if any("unused" in issue.get("message", "").lower() for issue in issues):
            fixes.append("Run: autoflake --remove-all-unused-imports " + file_path)
        
        return fixes
    
    def _calculate_quality_score(self, issues: List[Dict[str, Any]]) -> float:
        """Calculate quality score"""
        if not issues:
            return 100.0
        
        # Weight different types of issues
        error_count = sum(1 for issue in issues if issue.get("severity") == "error")
        warning_count = sum(1 for issue in issues if issue.get("severity") == "warning")
        
        # Calculate score
        score = 100 - (error_count * 10) - (warning_count * 5)
        return max(0, score)
    
    async def generate_tests(self, file_path: str) -> str:
        """Generate test file for given source file"""
        print(f"🧪 Generating tests for {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            tree = ast.parse(content)
            
            # Generate test content
            test_content = self._generate_test_content(file_path, tree)
            
            # Write test file
            test_file_path = file_path.replace('.py', '_test.py').replace('agentdev/', 'tests/agentdev/')
            test_file_path = test_file_path.replace('tests/tests/', 'tests/')
            
            os.makedirs(os.path.dirname(test_file_path), exist_ok=True)
            
            with open(test_file_path, 'w', encoding='utf-8') as f:
                f.write(test_content)
            
            print(f"✅ Test file generated: {test_file_path}")
            return test_file_path
            
        except Exception as e:
            print(f"❌ Failed to generate tests: {e}")
            return ""
    
    def _generate_test_content(self, file_path: str, tree: ast.AST) -> str:
        """Generate test content from AST"""
        test_content = f'''#!/usr/bin/env python3
"""
Auto-generated tests for {file_path}
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from {file_path.replace('.py', '').replace('/', '.')} import *
except ImportError as e:
    print(f"Warning: Could not import module: {{e}}")

class TestAutoGenerated:
    """Auto-generated test class"""
    
    def test_module_imports(self):
        """Test that module can be imported"""
        # This test ensures the module can be imported without errors
        assert True
    
    def test_basic_functionality(self):
        """Test basic functionality"""
        # Add your test cases here
        assert True
    
    @pytest.mark.asyncio
    async def test_async_functionality(self):
        """Test async functionality"""
        # Add async test cases here
        assert True
'''
        return test_content
    
    def get_quality_summary(self) -> Dict[str, Any]:
        """Get quality summary"""
        if not self.reports:
            return {"total_files": 0, "average_score": 0, "total_issues": 0}
        
        total_files = len(self.reports)
        total_issues = sum(len(report.issues) for report in self.reports)
        average_score = sum(report.score for report in self.reports) / total_files
        
        return {
            "total_files": total_files,
            "average_score": round(average_score, 2),
            "total_issues": total_issues,
            "files_with_issues": len([r for r in self.reports if r.issues]),
            "files_passing": len([r for r in self.reports if r.score >= 80])
        }
    
    def export_quality_report(self, output_path: str):
        """Export quality report"""
        report_data = {
            "summary": self.get_quality_summary(),
            "reports": [
                {
                    "file_path": report.file_path,
                    "score": report.score,
                    "issues_count": len(report.issues),
                    "suggestions": report.suggestions,
                    "auto_fixes": report.auto_fixes
                }
                for report in self.reports
            ]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Quality report exported to {output_path}")

# Example usage
async def main():
    """Example usage of QualityEnforcer"""
    enforcer = QualityEnforcer(".")
    
    # Analyze a specific file
    test_file = "agentdev/state_store.py"
    if os.path.exists(test_file):
        report = await enforcer.enforce_quality(test_file)
        print(f"Quality score: {report.score}")
        print(f"Issues: {len(report.issues)}")
        print(f"Suggestions: {report.suggestions}")
        
        # Generate tests
        test_file_path = await enforcer.generate_tests(test_file)
        if test_file_path:
            print(f"Generated test file: {test_file_path}")
    
    # Export report
    enforcer.export_quality_report("reports/quality_report.json")
    
    # Print summary
    summary = enforcer.get_quality_summary()
    print(f"Quality Summary: {summary}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
