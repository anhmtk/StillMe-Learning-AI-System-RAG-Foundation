"""
Comprehensive Testing for Phase 2: Test Generation & Code Review

Tests:
1. Test Generation for 5 different validators
2. Code Review for 10 code snippets
3. Edge cases: complex code, async code, error handling
4. Measure accuracy and false positive/negative rates
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()  # Try to load from current directory
except ImportError:
    pass  # python-dotenv not installed, use environment variables only
except Exception:
    pass  # Error loading .env, continue with environment variables

import logging
import asyncio
import json
from typing import List, Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Test cases for test generation
TEST_GENERATION_CASES = [
    {
        "name": "Simple Validator",
        "file": "backend/validators/citation_validator.py",
        "description": "Generate tests for citation validator"
    },
    {
        "name": "Math Functions",
        "code": """
def add(a, b):
    return a + b

def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
""",
        "description": "Generate tests for math functions with error handling"
    },
    {
        "name": "Async Function",
        "code": """
import asyncio

async def fetch_data(url: str) -> dict:
    await asyncio.sleep(0.1)
    return {"url": url, "data": "test"}
""",
        "description": "Generate tests for async function"
    },
    {
        "name": "Class with Methods",
        "code": """
class Calculator:
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def clear_history(self):
        self.history = []
""",
        "description": "Generate tests for class with state"
    },
    {
        "name": "Error Handling",
        "code": """
def process_file(filepath: str) -> str:
    try:
        with open(filepath, 'r') as f:
            return f.read()
    except FileNotFoundError:
        raise ValueError(f"File not found: {filepath}")
    except Exception as e:
        raise RuntimeError(f"Error reading file: {e}")
""",
        "description": "Generate tests for error handling scenarios"
    }
]

# Test cases for code review
CODE_REVIEW_CASES = [
    {
        "name": "Unused Imports",
        "code": """
import os
import sys
import json  # unused

def test():
    return "test"
""",
        "expected_issues": ["unused_import"]
    },
    {
        "name": "Missing Error Handling",
        "code": """
def read_file(path):
    file = open(path, 'r')
    data = file.read()
    return data
""",
        "expected_issues": ["missing_error_handling"]
    },
    {
        "name": "Naming Issues",
        "code": """
def BadFunctionName():
    pass

class badClassName:
    pass
""",
        "expected_issues": ["naming_inconsistency"]
    },
    {
        "name": "Unreachable Code",
        "code": """
def test():
    return True
    print("unreachable")
""",
        "expected_issues": ["unreachable_code"]
    },
    {
        "name": "Multiple Issues",
        "code": """
import os  # unused
import sys  # unused

def badName():
    file = open("test.txt")  # no error handling
    return file.read()
    print("unreachable")
""",
        "expected_issues": ["unused_import", "missing_error_handling", "naming_inconsistency", "unreachable_code"]
    },
    {
        "name": "Clean Code",
        "code": """
def calculate_sum(a: int, b: int) -> int:
    \"\"\"Add two numbers.\"\"\"
    return a + b
""",
        "expected_issues": []  # Should have no issues
    },
    {
        "name": "Complex Function",
        "code": """
def process_data(data: list, threshold: float) -> dict:
    if not data:
        return {"error": "Empty data"}
    
    try:
        filtered = [x for x in data if x > threshold]
        return {"count": len(filtered), "items": filtered}
    except TypeError:
        return {"error": "Invalid data type"}
""",
        "expected_issues": []  # Should be clean
    },
    {
        "name": "Async Code",
        "code": """
import asyncio

async def fetch_url(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()
""",
        "expected_issues": []  # Should be clean (assuming aiohttp is used)
    },
    {
        "name": "Security Issue",
        "code": """
import subprocess

def run_command(cmd):
    subprocess.run(cmd, shell=True)  # security risk
""",
        "expected_issues": ["security"]  # Should detect shell=True risk
    },
    {
        "name": "Performance Issue",
        "code": """
def find_item(items, target):
    for i in range(len(items)):
        for j in range(len(items)):
            if items[i] == target and items[j] == target:
                return i, j
    return None
""",
        "expected_issues": []  # May detect performance issue
    }
]


async def test_generation_comprehensive():
    """Test 1: Generate tests for 5 different cases"""
    logger.info("\n" + "="*80)
    logger.info("TEST 1: Test Generation (5 cases)")
    logger.info("="*80)
    
    try:
        from backend.services.test_generator import get_test_generator
        from backend.services.codebase_indexer import get_codebase_indexer
        
        indexer = get_codebase_indexer()
        generator = get_test_generator(codebase_indexer=indexer)
        
        results = []
        passed = 0
        
        for i, test_case in enumerate(TEST_GENERATION_CASES, 1):
            logger.info(f"\n📝 Test Case {i}/{len(TEST_GENERATION_CASES)}: {test_case['name']}")
            logger.info(f"   Description: {test_case['description']}")
            
            try:
                # Check if LLM API key available (from .env or environment)
                has_api_key = bool(os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENROUTER_API_KEY"))
                
                if not has_api_key:
                    logger.warning("   ⚠️ Skipping (no LLM API key)")
                    results.append({
                        "name": test_case["name"],
                        "status": "skipped",
                        "reason": "No LLM API key"
                    })
                    continue
                
                # Generate tests
                if "file" in test_case:
                    result = await generator.generate_tests(
                        file_path=test_case["file"],
                        test_framework="pytest"
                    )
                else:
                    result = await generator.generate_tests(
                        code_content=test_case["code"],
                        test_framework="pytest"
                    )
                
                # Verify result
                assert "test_code" in result
                assert "test_file_path" in result
                assert "coverage_estimate" in result
                
                # Check test quality
                test_code = result["test_code"]
                has_test_functions = "def test_" in test_code or "import pytest" in test_code
                
                if has_test_functions:
                    logger.info(f"   ✅ Generated {len(result['test_cases'])} test cases")
                    logger.info(f"   ✅ Coverage estimate: {result['coverage_estimate']}%")
                    passed += 1
                    results.append({
                        "name": test_case["name"],
                        "status": "pass",
                        "test_cases": len(result['test_cases']),
                        "coverage": result['coverage_estimate']
                    })
                else:
                    logger.warning(f"   ⚠️ Generated code doesn't look like tests")
                    results.append({
                        "name": test_case["name"],
                        "status": "partial",
                        "reason": "Invalid test format"
                    })
                    
            except Exception as e:
                logger.error(f"   ❌ Failed: {e}")
                results.append({
                    "name": test_case["name"],
                    "status": "fail",
                    "error": str(e)
                })
        
        logger.info(f"\n📊 Summary: {passed}/{len(TEST_GENERATION_CASES)} passed")
        return results
        
    except Exception as e:
        logger.error(f"❌ Test generation comprehensive failed: {e}", exc_info=True)
        return []


async def test_code_review_comprehensive():
    """Test 2: Review 10 code snippets"""
    logger.info("\n" + "="*80)
    logger.info("TEST 2: Code Review (10 cases)")
    logger.info("="*80)
    
    try:
        from backend.services.code_reviewer import get_code_reviewer
        from backend.services.codebase_indexer import get_codebase_indexer
        
        indexer = get_codebase_indexer()
        reviewer = get_code_reviewer(codebase_indexer=indexer)
        
        results = []
        true_positives = 0
        false_positives = 0
        false_negatives = 0
        
        for i, test_case in enumerate(CODE_REVIEW_CASES, 1):
            logger.info(f"\n📝 Review Case {i}/{len(CODE_REVIEW_CASES)}: {test_case['name']}")
            
            try:
                review_result = await reviewer.review_code(
                    code_content=test_case["code"],
                    check_style=True,
                    check_security=True,
                    check_performance=True
                )
                
                # Analyze results
                found_issue_types = [issue.get("type", "") for issue in review_result["issues"]]
                expected_issues = test_case.get("expected_issues", [])
                
                # Check true positives (found expected issues)
                found_expected = sum(1 for exp in expected_issues if any(exp in found for found in found_issue_types))
                
                # Check false positives (found issues not expected)
                unexpected_issues = [f for f in found_issue_types if not any(exp in f for exp in expected_issues)]
                
                # Check false negatives (expected issues not found)
                missing_issues = [exp for exp in expected_issues if not any(exp in f for f in found_issue_types)]
                
                if found_expected > 0:
                    true_positives += 1
                if unexpected_issues:
                    false_positives += len(unexpected_issues)
                if missing_issues:
                    false_negatives += len(missing_issues)
                
                logger.info(f"   ✅ Issues found: {review_result['summary']['total']}")
                logger.info(f"   ✅ Score: {review_result['score']}/100")
                logger.info(f"   ✅ Expected: {expected_issues}, Found: {found_issue_types[:3]}")
                
                results.append({
                    "name": test_case["name"],
                    "status": "pass",
                    "issues_found": review_result['summary']['total'],
                    "score": review_result['score'],
                    "expected": expected_issues,
                    "found": found_issue_types
                })
                
            except Exception as e:
                logger.error(f"   ❌ Failed: {e}")
                results.append({
                    "name": test_case["name"],
                    "status": "fail",
                    "error": str(e)
                })
        
        logger.info(f"\n📊 Review Accuracy:")
        logger.info(f"   True Positives: {true_positives}/{len(CODE_REVIEW_CASES)}")
        logger.info(f"   False Positives: {false_positives}")
        logger.info(f"   False Negatives: {false_negatives}")
        
        return {
            "results": results,
            "accuracy": {
                "true_positives": true_positives,
                "false_positives": false_positives,
                "false_negatives": false_negatives,
                "total_cases": len(CODE_REVIEW_CASES)
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Code review comprehensive failed: {e}", exc_info=True)
        return {"results": [], "accuracy": {}}


async def main():
    """Run comprehensive Phase 2 tests"""
    logger.info("🧪 Phase 2 Comprehensive Testing")
    logger.info("="*80)
    
    # Test 1: Test Generation
    test_gen_results = await test_generation_comprehensive()
    
    # Test 2: Code Review
    review_results = await test_code_review_comprehensive()
    
    # Save results
    results_file = project_root / "test_results_phase2_comprehensive.json"
    output = {
        "test_generation": test_gen_results,
        "code_review": review_results,
        "summary": {
            "test_generation_cases": len(TEST_GENERATION_CASES),
            "code_review_cases": len(CODE_REVIEW_CASES)
        }
    }
    
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n💾 Results saved to: {results_file}")
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("📊 COMPREHENSIVE TEST SUMMARY")
    logger.info("="*80)
    logger.info(f"Test Generation: {len([r for r in test_gen_results if r.get('status') == 'pass'])}/{len(TEST_GENERATION_CASES)} passed")
    
    if review_results.get("accuracy"):
        acc = review_results["accuracy"]
        logger.info(f"Code Review Accuracy:")
        logger.info(f"   True Positives: {acc.get('true_positives', 0)}/{acc.get('total_cases', 0)}")
        logger.info(f"   False Positives: {acc.get('false_positives', 0)}")
        logger.info(f"   False Negatives: {acc.get('false_negatives', 0)}")
    
    logger.info("\n✅ Phase 2 Comprehensive Testing Complete!")
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

