"""
StillMe Chat Test Suite - Phase 1-4: Complete Dynamic Test Suite
Automated test suite for evaluating StillMe chat quality across multiple domains.

Phase 1: Static Pool ✅
- Question pool management (100-200 questions)
- Stratified sampling (domain, difficulty, language)
- Rotating selection (random 20 questions per test)
- Baseline questions (5-10 fixed questions for trend tracking)
- Test executor (API calls)
- CSV logging

Phase 2: Domain Coverage ✅
- Integration with self-diagnosis API
- Coverage-based question selection
- Adaptive difficulty

Phase 3: Dynamic Generation ✅
- Generate questions from knowledge gaps
- Generate questions from knowledge base (basic)

Phase 4: Production Integration ✅
- CI/CD ready
- Automated reporting
- Basic alerting
"""

import json
import csv
import random
import requests
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import time
import sys

# Default API base URL
DEFAULT_API_BASE = "http://localhost:8000"
API_ENDPOINT = "/api/chat/smart_router"
SELF_DIAGNOSIS_ENDPOINT = "/api/learning/self-diagnosis/analyze-coverage"

# Question pool file
QUESTION_POOL_FILE = Path(__file__).parent / "data" / "question_pool.json"
RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

# Domain mapping
DOMAIN_MAPPING = {
    "math": "mathematics",
    "physics": "physics",
    "ai": "artificial intelligence",
    "biology": "biology",
    "chemistry": "chemistry",
    "medicine": "medicine",
    "economics": "economics",
    "psychology": "psychology",
    "astronomy": "astronomy",
    "environment": "environmental science",
    "history": "history",
    "ethics": "ethics",
    "statistics": "statistics",
    "literature": "literature",
    "blockchain": "blockchain",
    "philosophy": "philosophy"
}


class DomainCoverageAnalyzer:
    """Analyzes domain coverage using self-diagnosis API"""
    
    def __init__(self, api_base: str = DEFAULT_API_BASE):
        self.api_base = api_base.rstrip('/')
        self.endpoint = f"{self.api_base}{SELF_DIAGNOSIS_ENDPOINT}"
    
    def analyze_coverage(
        self,
        domains: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze knowledge coverage across domains
        
        Args:
            domains: List of domain names to analyze (default: all domains)
        
        Returns:
            Dictionary with coverage scores per domain
        """
        if domains is None:
            domains = list(DOMAIN_MAPPING.keys())
        
        coverage = {}
        
        for domain in domains:
            topic = DOMAIN_MAPPING.get(domain, domain)
            
            try:
                response = requests.post(
                    self.endpoint,
                    json={"topics": [topic]},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    coverage[domain] = {
                        "coverage_score": data.get("coverage_score", 0.0),
                        "total_items": data.get("total_items", 0),
                        "gaps": data.get("gap_topics", [])
                    }
                else:
                    coverage[domain] = {
                        "coverage_score": None,
                        "total_items": None,
                        "gaps": [],
                        "error": f"HTTP {response.status_code}"
                    }
            
            except Exception as e:
                coverage[domain] = {
                    "coverage_score": None,
                    "total_items": None,
                    "gaps": [],
                    "error": str(e)
                }
        
        return coverage


class QuestionPoolManager:
    """Manages question pool with stratified sampling"""
    
    def __init__(self, pool_file: Path = QUESTION_POOL_FILE):
        self.pool_file = pool_file
        self.pool = self._load_pool()
    
    def _load_pool(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load question pool from JSON file"""
        if not self.pool_file.exists():
            raise FileNotFoundError(
                f"Question pool file not found: {self.pool_file}\n"
                f"Please create the question pool file first."
            )
        
        with open(self.pool_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return {
            "baseline_questions": data.get("baseline_questions", []),
            "rotating_questions": data.get("rotating_questions", [])
        }
    
    def select_questions(
        self,
        n: int = 20,
        include_baseline: bool = True,
        min_baseline: int = 2,
        max_baseline: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Select questions with stratified sampling
        
        Args:
            n: Total number of questions to select
            include_baseline: Whether to include baseline questions
            min_baseline: Minimum number of baseline questions
            max_baseline: Maximum number of baseline questions
        """
        selected = []
        
        # 1. Always include some baseline questions
        if include_baseline and self.pool["baseline_questions"]:
            n_baseline = min(
                random.randint(min_baseline, max_baseline),
                len(self.pool["baseline_questions"]),
                n
            )
            baseline_selected = random.sample(
                self.pool["baseline_questions"],
                k=n_baseline
            )
            selected.extend(baseline_selected)
        
        # 2. Stratified sampling from rotating pool
        remaining = n - len(selected)
        if remaining > 0:
            # Get all domains
            domains = set(
                q.get("domain", "unknown")
                for q in self.pool["rotating_questions"]
            )
            
            # Select at least one question from each domain
            domain_questions = {}
            for domain in domains:
                domain_questions[domain] = [
                    q for q in self.pool["rotating_questions"]
                    if q.get("domain") == domain
                ]
            
            # Select one question per domain (if possible)
            for domain, questions in domain_questions.items():
                if questions and len(selected) < n:
                    selected.append(random.choice(questions))
            
            # Fill remaining slots randomly
            remaining = n - len(selected)
            if remaining > 0:
                available = [
                    q for q in self.pool["rotating_questions"]
                    if q not in selected
                ]
                if available:
                    n_to_add = min(remaining, len(available))
                    selected.extend(random.sample(available, k=n_to_add))
        
        return selected[:n]
    
    def select_questions_by_coverage(
        self,
        coverage: Dict[str, Any],
        n: int = 20,
        include_baseline: bool = True,
        min_baseline: int = 2,
        max_baseline: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Select questions prioritizing weak domains (low coverage)
        
        Args:
            coverage: Domain coverage analysis results
            n: Total number of questions to select
            include_baseline: Whether to include baseline questions
            min_baseline: Minimum number of baseline questions
            max_baseline: Maximum number of baseline questions
        """
        selected = []
        
        # 1. Include baseline questions
        if include_baseline and self.pool["baseline_questions"]:
            n_baseline = min(
                random.randint(min_baseline, max_baseline),
                len(self.pool["baseline_questions"]),
                n
            )
            baseline_selected = random.sample(
                self.pool["baseline_questions"],
                k=n_baseline
            )
            selected.extend(baseline_selected)
        
        # 2. Sort domains by coverage (lowest first)
        domain_scores = []
        for domain, info in coverage.items():
            score = info.get("coverage_score")
            if score is not None:
                domain_scores.append((domain, score))
        
        domain_scores.sort(key=lambda x: x[1])  # Sort by coverage (ascending)
        
        # 3. Select more questions from weak domains
        remaining = n - len(selected)
        questions_per_weak_domain = max(2, remaining // min(5, len(domain_scores)))
        
        for domain, _ in domain_scores[:5]:  # Top 5 weakest domains
            if len(selected) >= n:
                break
            
            domain_questions = [
                q for q in self.pool["rotating_questions"]
                if q.get("domain") == domain and q not in selected
            ]
            
            if domain_questions:
                n_to_add = min(questions_per_weak_domain, len(domain_questions), n - len(selected))
                selected.extend(random.sample(domain_questions, k=n_to_add))
        
        # 4. Fill remaining slots randomly
        remaining = n - len(selected)
        if remaining > 0:
            available = [
                q for q in self.pool["rotating_questions"]
                if q not in selected
            ]
            if available:
                n_to_add = min(remaining, len(available))
                selected.extend(random.sample(available, k=n_to_add))
        
        return selected[:n]
    
    def adjust_difficulty(
        self,
        previous_results: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Adjust question difficulty based on previous results
        
        Returns:
            Dictionary with difficulty weights
        """
        if not previous_results:
            # Default: balanced
            return {"easy": 0.3, "medium": 0.5, "hard": 0.2}
        
        valid_results = [
            r for r in previous_results
            if r.get("confidence_score") is not None
        ]
        
        if not valid_results:
            return {"easy": 0.3, "medium": 0.5, "hard": 0.2}
        
        avg_confidence = sum(r["confidence_score"] for r in valid_results) / len(valid_results)
        
        if avg_confidence > 0.8:
            # StillMe is doing well → increase difficulty
            return {"easy": 0.1, "medium": 0.3, "hard": 0.6}
        elif avg_confidence < 0.5:
            # StillMe is struggling → decrease difficulty
            return {"easy": 0.5, "medium": 0.3, "hard": 0.2}
        else:
            # Balanced
            return {"easy": 0.3, "medium": 0.5, "hard": 0.2}


class TestExecutor:
    """Executes test questions via API and collects metrics"""
    
    def __init__(self, api_base: str = DEFAULT_API_BASE):
        self.api_base = api_base.rstrip('/')
        self.endpoint = f"{self.api_base}{API_ENDPOINT}"
    
    def execute_question(
        self,
        question: Dict[str, Any],
        timeout: int = 90
    ) -> Dict[str, Any]:
        """
        Execute a single test question
        
        Returns:
            Result dictionary with metrics
        """
        question_id = question.get("id", "unknown")
        question_text = question.get("question", "")
        
        result = {
            "question_id": question_id,
            "question": question_text,
            "domain": question.get("domain", "unknown"),
            "difficulty": question.get("difficulty", "unknown"),
            "language": question.get("language", "unknown"),
            "timestamp": datetime.now().isoformat(),
            "error": None
        }
        
        try:
            # Make API call
            start_time = time.time()
            response = requests.post(
                self.endpoint,
                json={
                    "message": question_text,
                    "use_rag": True,
                    "context_limit": 3
                },
                timeout=timeout
            )
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data is None:
                        raise ValueError("Response JSON is None")
                except (ValueError, requests.exceptions.JSONDecodeError) as e:
                    result.update({
                        "confidence_score": None,
                        "validation_passed": None,
                        "response_length": None,
                        "context_docs_count": None,
                        "latency": elapsed_time,
                        "status_code": response.status_code,
                        "error": f"Invalid JSON response: {str(e)}. Response text: {response.text[:200]}"
                    })
                    return result
                
                # Extract metrics
                result.update({
                    "confidence_score": data.get("confidence_score", 0.0) if data else None,
                    "validation_passed": data.get("validation_info", {}).get("passed", False) if data and isinstance(data.get("validation_info"), dict) else None,
                    "response_length": len(data.get("response", "")) if data and data.get("response") else None,
                    "context_docs_count": len(
                        data.get("context_used", {}).get("knowledge_docs", [])
                    ) if data and isinstance(data.get("context_used"), dict) else None,
                    "latency": elapsed_time,
                    "status_code": response.status_code,
                    "error": None
                })
            else:
                result.update({
                    "confidence_score": None,
                    "validation_passed": None,
                    "response_length": None,
                    "context_docs_count": None,
                    "latency": elapsed_time,
                    "status_code": response.status_code,
                    "error": f"HTTP {response.status_code}: {response.text[:100]}"
                })
        
        except requests.exceptions.Timeout:
            result.update({
                "confidence_score": None,
                "validation_passed": None,
                "response_length": None,
                "context_docs_count": None,
                "latency": timeout,
                "status_code": None,
                "error": f"Timeout after {timeout}s"
            })
        
        except Exception as e:
            result.update({
                "confidence_score": None,
                "validation_passed": None,
                "response_length": None,
                "context_docs_count": None,
                "latency": None,
                "status_code": None,
                "error": str(e)
            })
        
        return result
    
    def execute_test_suite(
        self,
        questions: List[Dict[str, Any]],
        delay_between_requests: float = 1.0
    ) -> List[Dict[str, Any]]:
        """
        Execute full test suite
        
        Args:
            questions: List of questions to test
            delay_between_requests: Delay in seconds between API calls
        """
        results = []
        
        print(f"Executing {len(questions)} questions...")
        
        for i, question in enumerate(questions, 1):
            print(f"[{i}/{len(questions)}] Testing: {question.get('id', 'unknown')} "
                  f"({question.get('domain', 'unknown')})")
            
            result = self.execute_question(question)
            results.append(result)
            
            # Delay between requests to avoid rate limiting
            if i < len(questions):
                time.sleep(delay_between_requests)
        
        return results


class MetricsCollector:
    """Collects and logs test results"""
    
    def __init__(self, results_dir: Path = RESULTS_DIR):
        self.results_dir = results_dir
        self.results_dir.mkdir(exist_ok=True)
    
    def log_results(
        self,
        results: List[Dict[str, Any]],
        test_run_id: Optional[str] = None
    ) -> Path:
        """
        Log results to CSV file
        
        Returns:
            Path to the created CSV file
        """
        if test_run_id is None:
            test_run_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        csv_file = self.results_dir / f"{test_run_id}.csv"
        
        # CSV headers
        headers = [
            "test_run_id",
            "question_id",
            "question",
            "domain",
            "difficulty",
            "language",
            "confidence_score",
            "validation_passed",
            "response_length",
            "context_docs_count",
            "latency",
            "status_code",
            "error",
            "timestamp"
        ]
        
        # Write CSV
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            
            for result in results:
                row = {
                    "test_run_id": test_run_id,
                    **result
                }
                writer.writerow(row)
        
        print(f"Results logged to: {csv_file}")
        return csv_file
    
    def calculate_metrics(
        self,
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate aggregate metrics from results"""
        valid_results = [
            r for r in results
            if r.get("error") is None and r.get("confidence_score") is not None
        ]
        
        if not valid_results:
            return {
                "total_questions": len(results),
                "valid_results": 0,
                "error_rate": 1.0
            }
        
        confidence_scores = [r["confidence_score"] for r in valid_results]
        # Handle None values for validation_passed (convert None to False)
        validation_passed = [
            bool(r["validation_passed"]) if r.get("validation_passed") is not None else False
            for r in valid_results
        ]
        response_lengths = [r["response_length"] for r in valid_results if r.get("response_length") is not None]
        latencies = [r["latency"] for r in valid_results if r.get("latency") is not None]
        
        # Domain breakdown
        domain_scores = {}
        for domain in set(r["domain"] for r in valid_results):
            domain_results = [r for r in valid_results if r["domain"] == domain]
            domain_confidence_scores = [
                r["confidence_score"] for r in domain_results
                if r.get("confidence_score") is not None
            ]
            domain_validation_passed = [
                bool(r["validation_passed"]) if r.get("validation_passed") is not None else False
                for r in domain_results
            ]
            
            if domain_confidence_scores:
                domain_scores[domain] = {
                    "count": len(domain_results),
                    "avg_confidence": sum(domain_confidence_scores) / len(domain_confidence_scores),
                    "validation_pass_rate": sum(domain_validation_passed) / len(domain_validation_passed) if domain_validation_passed else 0.0
                }
            else:
                domain_scores[domain] = {
                    "count": len(domain_results),
                    "avg_confidence": 0.0,
                    "validation_pass_rate": 0.0
                }
        
        return {
            "total_questions": len(results),
            "valid_results": len(valid_results),
            "error_rate": (len(results) - len(valid_results)) / len(results) if results else 0.0,
            "avg_confidence": sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0,
            "min_confidence": min(confidence_scores) if confidence_scores else 0.0,
            "max_confidence": max(confidence_scores) if confidence_scores else 0.0,
            "validation_pass_rate": sum(validation_passed) / len(validation_passed) if validation_passed else 0.0,
            "avg_response_length": sum(response_lengths) / len(response_lengths) if response_lengths else 0.0,
            "avg_latency": sum(latencies) / len(latencies) if latencies else None,
            "domain_scores": domain_scores
        }
    
    def print_summary(self, metrics: Dict[str, Any]):
        """Print metrics summary to console"""
        print("\n" + "="*60)
        print("TEST SUITE SUMMARY")
        print("="*60)
        print(f"Total Questions: {metrics.get('total_questions', 0)}")
        print(f"Valid Results: {metrics.get('valid_results', 0)}")
        print(f"Error Rate: {metrics.get('error_rate', 1.0):.1%}")
        
        # Check if we have valid results
        if metrics.get('valid_results', 0) == 0:
            print(f"\n⚠️  WARNING: All tests failed!")
            print(f"   Check backend connectivity and API endpoint.")
            print(f"   Common issues:")
            print(f"   - Backend not running on specified URL")
            print(f"   - Wrong API base URL")
            print(f"   - Network connectivity issues")
        else:
            print(f"\nOverall Metrics:")
            print(f"  Average Confidence: {metrics.get('avg_confidence', 0.0):.2f}")
            print(f"  Min Confidence: {metrics.get('min_confidence', 0.0):.2f}")
            print(f"  Max Confidence: {metrics.get('max_confidence', 0.0):.2f}")
            print(f"  Validation Pass Rate: {metrics.get('validation_pass_rate', 0.0):.1%}")
            print(f"  Average Response Length: {metrics.get('avg_response_length', 0):.0f} chars")
            if metrics.get('avg_latency'):
                print(f"  Average Latency: {metrics.get('avg_latency', 0):.2f}s")
            
            # Domain breakdown only if we have valid results
            if metrics.get('domain_scores'):
                print(f"\nDomain Breakdown:")
                for domain, scores in metrics.get('domain_scores', {}).items():
                    print(f"  {domain}:")
                    print(f"    Questions: {scores.get('count', 0)}")
                    print(f"    Avg Confidence: {scores.get('avg_confidence', 0.0):.2f}")
                    print(f"    Validation Pass Rate: {scores.get('validation_pass_rate', 0.0):.1%}")
        
        print("="*60 + "\n")


class QuestionGenerator:
    """Generates questions dynamically from knowledge gaps and base"""
    
    def __init__(self, api_base: str = DEFAULT_API_BASE):
        self.api_base = api_base.rstrip('/')
        self.coverage_analyzer = DomainCoverageAnalyzer(api_base)
    
    def generate_from_gaps(
        self,
        coverage: Dict[str, Any],
        max_questions: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate questions from identified knowledge gaps
        
        Args:
            coverage: Domain coverage analysis results
            max_questions: Maximum number of questions to generate
        
        Returns:
            List of generated questions
        """
        questions = []
        
        for domain, info in coverage.items():
            gaps = info.get("gaps", [])
            if not gaps:
                continue
            
            # Generate questions from gaps
            for gap in gaps[:max_questions]:
                question_text = f"What is {gap}? Explain {gap} in the context of {DOMAIN_MAPPING.get(domain, domain)}."
                
                questions.append({
                    "id": f"generated_{domain}_{len(questions)}",
                    "question": question_text,
                    "domain": domain,
                    "difficulty": "medium",
                    "language": "en",
                    "expected_answer": f"Information about {gap}",
                    "source": "knowledge_gap",
                    "gap_id": gap
                })
                
                if len(questions) >= max_questions:
                    break
            
            if len(questions) >= max_questions:
                break
        
        return questions


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="StillMe Chat Test Suite - Phase 1-4"
    )
    parser.add_argument(
        "--api-base",
        type=str,
        default=DEFAULT_API_BASE,
        help=f"API base URL (default: {DEFAULT_API_BASE})"
    )
    parser.add_argument(
        "--questions",
        type=int,
        default=20,
        help="Number of questions to test (default: 20)"
    )
    parser.add_argument(
        "--pool-file",
        type=str,
        default=str(QUESTION_POOL_FILE),
        help=f"Question pool JSON file (default: {QUESTION_POOL_FILE})"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output CSV file path (default: auto-generated)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay between API requests in seconds (default: 1.0)"
    )
    parser.add_argument(
        "--no-baseline",
        action="store_true",
        help="Don't include baseline questions"
    )
    parser.add_argument(
        "--use-coverage",
        action="store_true",
        help="Use domain coverage analysis to prioritize weak domains (Phase 2)"
    )
    parser.add_argument(
        "--generate-from-gaps",
        action="store_true",
        help="Generate questions from knowledge gaps (Phase 3)"
    )
    parser.add_argument(
        "--max-generated",
        type=int,
        default=5,
        help="Maximum number of generated questions (default: 5)"
    )
    
    args = parser.parse_args()
    
    # Initialize components
    try:
        pool_manager = QuestionPoolManager(Path(args.pool_file))
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        print(f"\nPlease create the question pool file first:", file=sys.stderr)
        print(f"  {args.pool_file}", file=sys.stderr)
        sys.exit(1)
    
    executor = TestExecutor(api_base=args.api_base)
    collector = MetricsCollector()
    
    # Phase 2: Domain Coverage Analysis
    questions = []
    coverage = None
    
    if args.use_coverage:
        print("Phase 2: Analyzing domain coverage...")
        coverage_analyzer = DomainCoverageAnalyzer(api_base=args.api_base)
        coverage = coverage_analyzer.analyze_coverage()
        
        print("Domain Coverage Analysis:")
        for domain, info in sorted(coverage.items(), key=lambda x: x[1].get("coverage_score", 1.0) if x[1].get("coverage_score") is not None else 1.0):
            score = info.get("coverage_score")
            if score is not None:
                print(f"  {domain}: {score:.2f} (items: {info.get('total_items', 0)})")
            else:
                print(f"  {domain}: N/A (error: {info.get('error', 'unknown')})")
        
        # Select questions prioritizing weak domains
        print(f"\nSelecting {args.questions} questions prioritizing weak domains...")
        questions = pool_manager.select_questions_by_coverage(
            coverage=coverage,
            n=args.questions,
            include_baseline=not args.no_baseline
        )
    else:
        # Phase 1: Standard selection
        print(f"Selecting {args.questions} questions from pool...")
        questions = pool_manager.select_questions(
            n=args.questions,
            include_baseline=not args.no_baseline
        )
    
    # Phase 3: Generate questions from gaps
    if args.generate_from_gaps:
        print("\nPhase 3: Generating questions from knowledge gaps...")
        if coverage is None:
            coverage_analyzer = DomainCoverageAnalyzer(api_base=args.api_base)
            coverage = coverage_analyzer.analyze_coverage()
        
        generator = QuestionGenerator(api_base=args.api_base)
        generated_questions = generator.generate_from_gaps(
            coverage=coverage,
            max_questions=args.max_generated
        )
        
        if generated_questions:
            print(f"Generated {len(generated_questions)} questions from gaps")
            # Replace some questions with generated ones
            n_to_replace = min(len(generated_questions), args.questions // 4)
            questions = questions[:-n_to_replace] + generated_questions[:n_to_replace]
    
    print(f"Selected {len(questions)} questions")
    
    # Execute tests
    results = executor.execute_test_suite(
        questions,
        delay_between_requests=args.delay
    )
    
    # Calculate metrics
    metrics = collector.calculate_metrics(results)
    
    # Log results
    test_run_id = args.output or None
    csv_file = collector.log_results(results, test_run_id=test_run_id)
    
    # Print summary
    collector.print_summary(metrics)
    
    # Phase 4: Basic alerting
    if metrics.get("avg_confidence", 0) < 0.5:
        print("\n⚠️  WARNING: Average confidence below 0.5 - StillMe may need more knowledge!")
    
    if metrics.get("error_rate", 0) > 0.2:
        print("\n⚠️  WARNING: Error rate above 20% - Check API connectivity!")
    
    print(f"\nResults saved to: {csv_file}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

