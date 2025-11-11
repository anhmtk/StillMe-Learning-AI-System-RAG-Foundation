"""
Helper script to view test results from Dynamic Test Suite
Displays results in a readable format from CSV files
"""

import csv
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

RESULTS_DIR = Path(__file__).parent / "results"


def load_results(csv_file: Path) -> List[Dict[str, Any]]:
    """Load results from CSV file"""
    results = []
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
    
    return results


def calculate_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate summary metrics"""
    valid_results = [
        r for r in results
        if r.get("error") == "" or r.get("error") is None
        and r.get("confidence_score") and r.get("confidence_score") != ""
    ]
    
    if not valid_results:
        return {
            "total": len(results),
            "valid": 0,
            "error_rate": 1.0
        }
    
    confidence_scores = [float(r["confidence_score"]) for r in valid_results if r.get("confidence_score")]
    validation_passed = [r.get("validation_passed", "").lower() == "true" for r in valid_results]
    response_lengths = [int(r["response_length"]) for r in valid_results if r.get("response_length")]
    latencies = [float(r["latency"]) for r in valid_results if r.get("latency") and r.get("latency") != ""]
    
    # Domain breakdown
    domain_scores = {}
    for domain in set(r["domain"] for r in valid_results):
        domain_results = [r for r in valid_results if r["domain"] == domain]
        domain_confidences = [float(r["confidence_score"]) for r in domain_results if r.get("confidence_score")]
        domain_validations = [r.get("validation_passed", "").lower() == "true" for r in domain_results]
        
        if domain_confidences:
            domain_scores[domain] = {
                "count": len(domain_results),
                "avg_confidence": sum(domain_confidences) / len(domain_confidences),
                "validation_pass_rate": sum(domain_validations) / len(domain_validations) if domain_validations else 0.0
            }
    
    return {
        "total": len(results),
        "valid": len(valid_results),
        "error_rate": (len(results) - len(valid_results)) / len(results) if results else 0.0,
        "avg_confidence": sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0,
        "min_confidence": min(confidence_scores) if confidence_scores else 0.0,
        "max_confidence": max(confidence_scores) if confidence_scores else 0.0,
        "validation_pass_rate": sum(validation_passed) / len(validation_passed) if validation_passed else 0.0,
        "avg_response_length": sum(response_lengths) / len(response_lengths) if response_lengths else 0.0,
        "avg_latency": sum(latencies) / len(latencies) if latencies else None,
        "domain_scores": domain_scores
    }


def print_summary(summary: Dict[str, Any], test_run_id: str):
    """Print formatted summary"""
    print("\n" + "="*70)
    print(f"TEST SUITE RESULTS: {test_run_id}")
    print("="*70)
    print(f"Total Questions: {summary['total']}")
    print(f"Valid Results: {summary['valid']}")
    print(f"Error Rate: {summary['error_rate']:.1%}")
    
    if summary['valid'] > 0:
        print(f"\n📊 Overall Metrics:")
        print(f"  Average Confidence: {summary['avg_confidence']:.2f}")
        print(f"  Min Confidence: {summary['min_confidence']:.2f}")
        print(f"  Max Confidence: {summary['max_confidence']:.2f}")
        print(f"  Validation Pass Rate: {summary['validation_pass_rate']:.1%}")
        print(f"  Average Response Length: {summary['avg_response_length']:.0f} chars")
        if summary.get('avg_latency'):
            print(f"  Average Latency: {summary['avg_latency']:.2f}s")
        
        if summary.get('domain_scores'):
            print(f"\n📈 Domain Breakdown:")
            for domain, scores in sorted(summary['domain_scores'].items()):
                print(f"  {domain}:")
                print(f"    Questions: {scores['count']}")
                print(f"    Avg Confidence: {scores['avg_confidence']:.2f}")
                print(f"    Validation Pass Rate: {scores['validation_pass_rate']:.1%}")
    
    print("="*70 + "\n")


def list_test_runs():
    """List all available test runs"""
    if not RESULTS_DIR.exists():
        print(f"No results directory found: {RESULTS_DIR}")
        return []
    
    csv_files = sorted(RESULTS_DIR.glob("*.csv"), key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not csv_files:
        print("No test results found.")
        return []
    
    print("\n📋 Available Test Runs:")
    print("-" * 70)
    for i, csv_file in enumerate(csv_files, 1):
        size = csv_file.stat().st_size
        mtime = datetime.fromtimestamp(csv_file.stat().st_mtime)
        print(f"{i}. {csv_file.name}")
        print(f"   Size: {size:,} bytes | Modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 70)
    
    return csv_files


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="View StillMe Chat Test Suite Results"
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="CSV file to view (default: latest)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available test runs"
    )
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Show detailed results for each question"
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_test_runs()
        return 0
    
    # Find CSV file
    if args.file:
        csv_file = Path(args.file)
        if not csv_file.is_absolute():
            # Check if it's just filename or relative path
            if csv_file.name == csv_file:
                # Just filename, look in results dir
                csv_file = RESULTS_DIR / csv_file
            else:
                # Relative path, resolve from current directory
                csv_file = Path.cwd() / csv_file
    else:
        # Get latest file
        csv_files = list_test_runs()
        if not csv_files:
            return 1
        csv_file = csv_files[0]
        print(f"\n📊 Viewing latest test run: {csv_file.name}\n")
    
    if not csv_file.exists():
        print(f"ERROR: File not found: {csv_file}", file=sys.stderr)
        return 1
    
    # Load and display results
    results = load_results(csv_file)
    test_run_id = csv_file.stem
    
    summary = calculate_summary(results)
    print_summary(summary, test_run_id)
    
    if args.detailed:
        print("\n📝 Detailed Results:")
        print("-" * 70)
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.get('question_id', 'unknown')} ({result.get('domain', 'unknown')})")
            print(f"   Question: {result.get('question', '')[:80]}...")
            if result.get('confidence_score'):
                print(f"   Confidence: {result.get('confidence_score')}")
            if result.get('validation_passed'):
                print(f"   Validation: {'✅ Passed' if result.get('validation_passed', '').lower() == 'true' else '❌ Failed'}")
            if result.get('error'):
                print(f"   Error: {result.get('error')}")
        print("-" * 70)
    
    print(f"\n💾 Full results saved to: {csv_file}")
    print(f"   Open with Excel, Google Sheets, or any CSV viewer\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

