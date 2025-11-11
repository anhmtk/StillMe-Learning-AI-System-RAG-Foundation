"""
Analyze Validation Failures Script
Analyzes validation failures from test suite results or chat history
"""

import sys
import os
import csv
import json
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def analyze_test_suite_results(csv_file: str):
    """Analyze validation failures from test suite CSV results"""
    print("=" * 60)
    print("VALIDATION FAILURES ANALYSIS - TEST SUITE")
    print("=" * 60)
    
    if not os.path.exists(csv_file):
        print(f"[ERROR] File not found: {csv_file}")
        return
    
    failures = []
    total = 0
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            validation_passed = row.get("validation_passed", "")
            
            # Handle different formats: "True"/"False", "true"/"false", "1"/"0", True/False, None
            is_passed = False
            if validation_passed:
                validation_lower = str(validation_passed).lower().strip()
                if validation_lower in ["true", "1"]:
                    is_passed = True
                elif validation_lower in ["false", "0"]:
                    is_passed = False
                else:
                    # Try to parse as boolean
                    try:
                        is_passed = bool(validation_passed)
                    except:
                        is_passed = False
            
            if not is_passed:
                failures.append({
                    "question_id": row.get("question_id", "unknown"),
                    "question": row.get("question", "")[:100],
                    "domain": row.get("domain", "unknown"),
                    "confidence_score": row.get("confidence_score", "N/A"),
                    "validation_passed": validation_passed,
                    "error": row.get("error", "")
                })
    
    print(f"\nTotal questions: {total}")
    print(f"Failed validations: {len(failures)}")
    print(f"Pass rate: {((total - len(failures)) / total * 100):.1f}%\n")
    
    if not failures:
        print("[SUCCESS] No validation failures found!")
        return
    
    # Group by domain
    domain_failures = defaultdict(list)
    for failure in failures:
        domain_failures[failure["domain"]].append(failure)
    
    print("Failures by Domain:")
    print("-" * 60)
    for domain, domain_fails in sorted(domain_failures.items()):
        print(f"{domain}: {len(domain_fails)} failures")
    
    print("\n" + "=" * 60)
    print("DETAILED FAILURES")
    print("=" * 60)
    
    for i, failure in enumerate(failures, 1):
        print(f"\n[{i}] {failure['question_id']} ({failure['domain']})")
        # Handle Unicode encoding for Windows terminal
        try:
            question_text = failure['question'].encode('utf-8', errors='replace').decode('utf-8', errors='replace')
            print(f"Question: {question_text}")
        except:
            print(f"Question: {failure['question'][:50]}...")
        print(f"Confidence: {failure['confidence_score']}")
        if failure['error']:
            print(f"Error: {failure['error']}")
    
    return failures


def analyze_chat_history(db_path: str = "data/chat_history.db"):
    """Analyze validation failures from chat history database"""
    print("=" * 60)
    print("VALIDATION FAILURES ANALYSIS - CHAT HISTORY")
    print("=" * 60)
    
    if not os.path.exists(db_path):
        print(f"[ERROR] Database not found: {db_path}")
        return
    
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all messages with validation info
        cursor.execute("""
            SELECT 
                id, user_message, assistant_response,
                confidence_score, validation_passed,
                timestamp
            FROM chat_history
            WHERE validation_passed IS NOT NULL
            ORDER BY timestamp DESC
            LIMIT 100
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        total = len(rows)
        failures = []
        
        for row in rows:
            msg_id, user_msg, assistant_resp, conf_score, val_passed, timestamp = row
            if not val_passed:  # False or 0
                failures.append({
                    "id": msg_id,
                    "user_message": user_msg[:100],
                    "confidence_score": conf_score,
                    "timestamp": timestamp
                })
        
        print(f"\nTotal messages analyzed: {total}")
        print(f"Failed validations: {len(failures)}")
        if total > 0:
            print(f"Pass rate: {((total - len(failures)) / total * 100):.1f}%\n")
        
        if not failures:
            print("[SUCCESS] No validation failures found in recent chat history!")
            return
        
        print("Recent Failures:")
        print("-" * 60)
        for failure in failures[:10]:  # Show first 10
            print(f"\nID: {failure['id']}")
            # Handle Unicode encoding for Windows terminal
            try:
                question_text = failure['user_message'].encode('utf-8', errors='replace').decode('utf-8', errors='replace')
                print(f"Question: {question_text}")
            except:
                print(f"Question: {failure['user_message'][:50]}...")
            print(f"Confidence: {failure['confidence_score']}")
            print(f"Timestamp: {failure['timestamp']}")
        
        return failures
        
    except Exception as e:
        print(f"[ERROR] Error analyzing chat history: {e}")
        return None


def analyze_validation_patterns(failures: List[Dict[str, Any]]):
    """Analyze patterns in validation failures"""
    if not failures:
        return
    
    print("\n" + "=" * 60)
    print("PATTERN ANALYSIS")
    print("=" * 60)
    
    # Group by confidence score ranges
    low_confidence = [f for f in failures if f.get("confidence_score") and float(f.get("confidence_score", 0)) < 0.5]
    high_confidence = [f for f in failures if f.get("confidence_score") and float(f.get("confidence_score", 0)) >= 0.5]
    
    print(f"\nFailures with low confidence (<0.5): {len(low_confidence)}")
    print(f"Failures with high confidence (>=0.5): {len(high_confidence)}")
    
    # Group by domain
    domain_failures = defaultdict(int)
    for failure in failures:
        domain = failure.get("domain", "unknown")
        domain_failures[domain] += 1
    
    if domain_failures:
        print("\nFailures by Domain:")
        for domain, count in sorted(domain_failures.items(), key=lambda x: x[1], reverse=True):
            print(f"  {domain}: {count}")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze validation failures")
    parser.add_argument(
        "--csv",
        type=str,
        help="Path to test suite CSV results file"
    )
    parser.add_argument(
        "--db",
        type=str,
        default="data/chat_history.db",
        help="Path to chat history database (default: data/chat_history.db)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Analyze both CSV and database"
    )
    
    args = parser.parse_args()
    
    if args.csv:
        failures = analyze_test_suite_results(args.csv)
        if failures:
            analyze_validation_patterns(failures)
    elif args.db or args.all:
        failures = analyze_chat_history(args.db)
        if failures:
            analyze_validation_patterns(failures)
    elif args.all:
        print("Analyzing both sources...\n")
        if args.csv:
            failures_csv = analyze_test_suite_results(args.csv)
        failures_db = analyze_chat_history(args.db)
    else:
        # Default: analyze latest test suite result
        results_dir = Path(__file__).parent.parent / "tests" / "results"
        if results_dir.exists():
            csv_files = sorted(results_dir.glob("test_*.csv"), key=os.path.getmtime, reverse=True)
            if csv_files:
                latest_csv = csv_files[0]
                print(f"Analyzing latest test suite result: {latest_csv.name}\n")
                failures = analyze_test_suite_results(str(latest_csv))
                if failures:
                    analyze_validation_patterns(failures)
            else:
                print("[ERROR] No test suite results found. Use --csv to specify a file.")
        else:
            print("[ERROR] Test results directory not found. Use --csv to specify a file.")


if __name__ == "__main__":
    main()

