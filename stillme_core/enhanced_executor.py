# stillme_core/enhanced_executor.py
"""
Enhanced Executor with multiple testing frameworks support
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional, Union, Tuple
import subprocess
import asyncio
import concurrent.futures
import time
import json
import os
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import logging

from .plan_types import PlanItem
from .executor import ExecResult, _run

logger = logging.getLogger(__name__)

class TestFramework(Enum):
    """Supported testing frameworks"""
    PYTEST = "pytest"
    UNITTEST = "unittest"
    DOCTEST = "doctest"
    NOSE = "nose"

@dataclass
class TestResult:
    """Enhanced test result with framework information"""
    framework: TestFramework
    passed: int
    failed: int
    skipped: int
    errors: int
    duration: float
    output: str
    error_output: str
    coverage_percent: Optional[float] = None
    test_files: Optional[List[str]] = None

@dataclass
class TestImpact:
    """Test impact analysis result"""
    affected_tests: List[str]
    total_tests: int
    impact_percent: float
    recommended_tests: List[str]

class EnhancedExecutor:
    """
    Enhanced executor with multiple testing frameworks support
    """
    
    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root)
        self.test_cache: Dict[str, TestResult] = {}
        self.impact_cache: Dict[str, TestImpact] = {}
        self.parallel_workers = min(4, os.cpu_count() or 1)
        
    def run_tests_parallel(self, test_files: List[str], framework: TestFramework = TestFramework.PYTEST) -> List[TestResult]:
        """Run tests in parallel for better performance"""
        if not test_files:
            return []
        
        # Group tests by framework
        grouped_tests = self._group_tests_by_framework(test_files)
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            futures = []
            
            for fw, files in grouped_tests.items():
                if files:
                    future = executor.submit(self._run_framework_tests, fw, files)
                    futures.append(future)
            
            # Collect results
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.error(f"Test execution failed: {e}")
        
        return results
    
    def _group_tests_by_framework(self, test_files: List[str]) -> Dict[TestFramework, List[str]]:
        """Group test files by their framework"""
        grouped = {fw: [] for fw in TestFramework}
        
        for test_file in test_files:
            framework = self._detect_test_framework(test_file)
            grouped[framework].append(test_file)
        
        return grouped
    
    def _detect_test_framework(self, test_file: str) -> TestFramework:
        """Detect test framework from file content"""
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for framework indicators
            if 'import pytest' in content or 'from pytest' in content:
                return TestFramework.PYTEST
            elif 'import unittest' in content or 'from unittest' in content:
                return TestFramework.UNITTEST
            elif 'import doctest' in content or 'from doctest' in content:
                return TestFramework.DOCTEST
            elif 'import nose' in content or 'from nose' in content:
                return TestFramework.NOSE
            else:
                # Default to pytest for .py files
                return TestFramework.PYTEST
                
        except Exception:
            return TestFramework.PYTEST
    
    def _run_framework_tests(self, framework: TestFramework, test_files: List[str]) -> Optional[TestResult]:
        """Run tests for a specific framework"""
        try:
            if framework == TestFramework.PYTEST:
                return self._run_pytest_tests(test_files)
            elif framework == TestFramework.UNITTEST:
                return self._run_unittest_tests(test_files)
            elif framework == TestFramework.DOCTEST:
                return self._run_doctest_tests(test_files)
            elif framework == TestFramework.NOSE:
                return self._run_nose_tests(test_files)
        except Exception as e:
            logger.error(f"Failed to run {framework.value} tests: {e}")
            return None
    
    def _run_pytest_tests(self, test_files: List[str]) -> TestResult:
        """Run pytest tests with coverage"""
        args = [
            "python", "-m", "pytest", 
            "-v", "--tb=short", "--maxfail=1",
            "--cov=.", "--cov-report=term-missing"
        ]
        args.extend(test_files)
        
        start_time = time.time()
        result = _run(args, cwd=str(self.repo_root))
        duration = time.time() - start_time
        
        # Parse pytest output
        passed, failed, skipped, errors = self._parse_pytest_output(result.stdout)
        coverage = self._extract_coverage_percent(result.stdout)
        
        return TestResult(
            framework=TestFramework.PYTEST,
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            duration=duration,
            output=result.stdout,
            error_output=result.stderr,
            coverage_percent=coverage,
            test_files=test_files
        )
    
    def _run_unittest_tests(self, test_files: List[str]) -> TestResult:
        """Run unittest tests"""
        args = ["python", "-m", "unittest", "-v"]
        args.extend(test_files)
        
        start_time = time.time()
        result = _run(args, cwd=str(self.repo_root))
        duration = time.time() - start_time
        
        # Parse unittest output
        passed, failed, skipped, errors = self._parse_unittest_output(result.stdout)
        
        return TestResult(
            framework=TestFramework.UNITTEST,
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            duration=duration,
            output=result.stdout,
            error_output=result.stderr,
            test_files=test_files
        )
    
    def _run_doctest_tests(self, test_files: List[str]) -> TestResult:
        """Run doctest tests"""
        args = ["python", "-m", "doctest", "-v"]
        args.extend(test_files)
        
        start_time = time.time()
        result = _run(args, cwd=str(self.repo_root))
        duration = time.time() - start_time
        
        # Parse doctest output
        passed, failed, skipped, errors = self._parse_doctest_output(result.stdout)
        
        return TestResult(
            framework=TestFramework.DOCTEST,
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            duration=duration,
            output=result.stdout,
            error_output=result.stderr,
            test_files=test_files
        )
    
    def _run_nose_tests(self, test_files: List[str]) -> TestResult:
        """Run nose tests"""
        args = ["python", "-m", "nose", "-v"]
        args.extend(test_files)
        
        start_time = time.time()
        result = _run(args, cwd=str(self.repo_root))
        duration = time.time() - start_time
        
        # Parse nose output
        passed, failed, skipped, errors = self._parse_nose_output(result.stdout)
        
        return TestResult(
            framework=TestFramework.NOSE,
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            duration=duration,
            output=result.stdout,
            error_output=result.stderr,
            test_files=test_files
        )
    
    def _parse_pytest_output(self, output: str) -> Tuple[int, int, int, int]:
        """Parse pytest output to extract test counts"""
        import re
        
        # Look for summary line
        summary_pattern = r"(\d+) passed(?:, (\d+) failed)?(?:, (\d+) skipped)?(?:, (\d+) error)?"
        match = re.search(summary_pattern, output)
        
        if match:
            passed = int(match.group(1))
            failed = int(match.group(2) or 0)
            skipped = int(match.group(3) or 0)
            errors = int(match.group(4) or 0)
        else:
            # Fallback parsing
            passed = output.count("PASSED")
            failed = output.count("FAILED")
            skipped = output.count("SKIPPED")
            errors = output.count("ERROR")
        
        return passed, failed, skipped, errors
    
    def _parse_unittest_output(self, output: str) -> Tuple[int, int, int, int]:
        """Parse unittest output to extract test counts"""
        import re
        
        # Look for summary line
        summary_pattern = r"Ran (\d+) tests? in [\d.]+s"
        match = re.search(summary_pattern, output)
        
        if match:
            total = int(match.group(1))
            failed = output.count("FAILED")
            errors = output.count("ERROR")
            skipped = output.count("SKIPPED")
            passed = total - failed - errors - skipped
        else:
            passed = output.count("ok")
            failed = output.count("FAILED")
            skipped = output.count("SKIPPED")
            errors = output.count("ERROR")
        
        return passed, failed, skipped, errors
    
    def _parse_doctest_output(self, output: str) -> Tuple[int, int, int, int]:
        """Parse doctest output to extract test counts"""
        import re
        
        # Look for summary line
        summary_pattern = r"(\d+) tests? in (\d+) items?"
        match = re.search(summary_pattern, output)
        
        if match:
            total = int(match.group(1))
            failed = output.count("Failed example:")
            errors = output.count("Exception raised:")
            skipped = 0
            passed = total - failed - errors
        else:
            passed = output.count("ok")
            failed = output.count("Failed example:")
            skipped = 0
            errors = output.count("Exception raised:")
        
        return passed, failed, skipped, errors
    
    def _parse_nose_output(self, output: str) -> Tuple[int, int, int, int]:
        """Parse nose output to extract test counts"""
        import re
        
        # Look for summary line
        summary_pattern = r"Ran (\d+) tests? in [\d.]+s"
        match = re.search(summary_pattern, output)
        
        if match:
            total = int(match.group(1))
            failed = output.count("FAILED")
            errors = output.count("ERROR")
            skipped = output.count("SKIPPED")
            passed = total - failed - errors - skipped
        else:
            passed = output.count("ok")
            failed = output.count("FAILED")
            skipped = output.count("SKIPPED")
            errors = output.count("ERROR")
        
        return passed, failed, skipped, errors
    
    def _extract_coverage_percent(self, output: str) -> Optional[float]:
        """Extract coverage percentage from pytest output"""
        import re
        
        # Look for coverage percentage
        coverage_pattern = r"TOTAL\s+(\d+)\s+(\d+)\s+(\d+)%"
        match = re.search(coverage_pattern, output)
        
        if match:
            return float(match.group(3))
        
        return None
    
    def analyze_test_impact(self, changed_files: List[str]) -> TestImpact:
        """Analyze which tests are affected by code changes"""
        cache_key = "|".join(sorted(changed_files))
        
        if cache_key in self.impact_cache:
            return self.impact_cache[cache_key]
        
        affected_tests = []
        total_tests = 0
        
        # Find all test files
        test_files = self._find_all_test_files()
        total_tests = len(test_files)
        
        # Analyze dependencies
        for test_file in test_files:
            if self._is_test_affected(test_file, changed_files):
                affected_tests.append(test_file)
        
        impact_percent = (len(affected_tests) / total_tests * 100) if total_tests > 0 else 0
        
        # Recommend tests to run
        recommended_tests = self._recommend_tests(changed_files, affected_tests)
        
        result = TestImpact(
            affected_tests=affected_tests,
            total_tests=total_tests,
            impact_percent=impact_percent,
            recommended_tests=recommended_tests
        )
        
        self.impact_cache[cache_key] = result
        return result
    
    def _find_all_test_files(self) -> List[str]:
        """Find all test files in the repository"""
        test_files = []
        
        # Common test file patterns
        patterns = [
            "test_*.py",
            "*_test.py",
            "tests/**/*.py",
            "**/test_*.py",
            "**/*_test.py"
        ]
        
        for pattern in patterns:
            for file_path in self.repo_root.glob(pattern):
                if file_path.is_file() and file_path.suffix == '.py':
                    test_files.append(str(file_path))
        
        return list(set(test_files))  # Remove duplicates
    
    def _is_test_affected(self, test_file: str, changed_files: List[str]) -> bool:
        """Check if a test file is affected by changes"""
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple dependency analysis
            for changed_file in changed_files:
                # Check if test imports the changed file
                module_name = Path(changed_file).stem
                if f"import {module_name}" in content or f"from {module_name}" in content:
                    return True
                
                # Check if test file path suggests it tests the changed file
                if self._is_test_for_file(test_file, changed_file):
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _is_test_for_file(self, test_file: str, source_file: str) -> bool:
        """Check if test file is specifically for a source file"""
        test_name = Path(test_file).stem
        source_name = Path(source_file).stem
        
        # Common naming patterns
        patterns = [
            f"test_{source_name}",
            f"{source_name}_test",
            f"test_{source_name.replace('_', '')}",
            f"{source_name.replace('_', '')}_test"
        ]
        
        return test_name in patterns
    
    def _recommend_tests(self, changed_files: List[str], affected_tests: List[str]) -> List[str]:
        """Recommend which tests to run based on changes"""
        recommended = []
        
        # High priority: direct test files
        for changed_file in changed_files:
            if changed_file.startswith("test_") or changed_file.endswith("_test.py"):
                recommended.append(changed_file)
        
        # Medium priority: affected tests
        recommended.extend(affected_tests[:10])  # Limit to top 10
        
        # Low priority: integration tests
        integration_tests = [t for t in affected_tests if "integration" in t.lower()]
        recommended.extend(integration_tests[:5])
        
        return list(set(recommended))  # Remove duplicates
    
    def generate_coverage_report(self, test_results: List[TestResult]) -> Dict[str, Any]:
        """Generate comprehensive coverage report"""
        total_passed = sum(r.passed for r in test_results)
        total_failed = sum(r.failed for r in test_results)
        total_skipped = sum(r.skipped for r in test_results)
        total_errors = sum(r.errors for r in test_results)
        total_duration = sum(r.duration for r in test_results)
        
        # Calculate overall coverage
        coverage_values = [r.coverage_percent for r in test_results if r.coverage_percent is not None]
        overall_coverage = sum(coverage_values) / len(coverage_values) if coverage_values else 0
        
        return {
            "summary": {
                "total_passed": total_passed,
                "total_failed": total_failed,
                "total_skipped": total_skipped,
                "total_errors": total_errors,
                "total_duration": total_duration,
                "overall_coverage": overall_coverage
            },
            "frameworks": {
                r.framework.value: {
                    "passed": r.passed,
                    "failed": r.failed,
                    "skipped": r.skipped,
                    "errors": r.errors,
                    "duration": r.duration,
                    "coverage": r.coverage_percent
                }
                for r in test_results
            },
            "recommendations": self._generate_coverage_recommendations(overall_coverage, total_failed)
        }
    
    def _generate_coverage_recommendations(self, coverage: float, failed_tests: int) -> List[str]:
        """Generate recommendations based on coverage and test results"""
        recommendations = []
        
        if coverage < 70:
            recommendations.append("Coverage is below 70%. Consider adding more tests.")
        elif coverage < 80:
            recommendations.append("Coverage is below 80%. Consider improving test coverage.")
        
        if failed_tests > 0:
            recommendations.append(f"{failed_tests} tests failed. Review and fix failing tests.")
        
        if coverage > 90 and failed_tests == 0:
            recommendations.append("Excellent test coverage and all tests passing!")
        
        return recommendations
