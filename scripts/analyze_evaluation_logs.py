"""
Analyze Backend Logs for Evaluation Issues

This script filters and analyzes backend logs to find:
1. Fallback messages being triggered
2. LLM API failures
3. Validation failures
4. Empty responses
5. Error patterns

Usage:
    python scripts/analyze_evaluation_logs.py [log_file_path]
    
If no path provided, will look for logs in common locations.
"""

import os
import sys
import re
from collections import defaultdict
from datetime import datetime
from typing import List, Dict, Tuple

# Patterns to search for
PATTERNS = {
    "fallback_triggered": [
        r"fallback.*message",
        r"using fallback",
        r"get_fallback_message_for_error",
        r"StillMe is experiencing a technical issue",
    ],
    "llm_failed": [
        r"LLM.*failed",
        r"LLM.*error",
        r"LLM.*returned.*empty",
        r"LLM.*returned.*None",
        r"generate_ai_response.*error",
        r"API.*error",
        r"timeout",
        r"rate.*limit",
    ],
    "validation_failed": [
        r"validation.*failed",
        r"Validation.*failed",
        r"validation.*reject",
        r"missing_citation",
        r"language_mismatch",
        r"validation.*pass.*False",
    ],
    "empty_response": [
        r"empty response",
        r"None.*response",
        r"response.*is.*None",
        r"response.*empty",
    ],
    "exception": [
        r"Exception:",
        r"Traceback",
        r"Error:",
        r"ERROR",
    ],
}


def find_log_files() -> List[str]:
    """Find log files in common locations"""
    possible_locations = [
        "logs/server.log",
        "logs/server_error.log",
        "logs/backend.log",
        "logs/app.log",
        "server.log",
        "backend.log",
    ]
    
    found_files = []
    for location in possible_locations:
        if os.path.exists(location):
            found_files.append(location)
    
    return found_files


def analyze_log_file(file_path: str) -> Dict:
    """Analyze a log file for evaluation issues"""
    print(f"📄 Analyzing: {file_path}")
    print("=" * 60)
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return {}
    
    # Get file size
    file_size = os.path.getsize(file_path)
    print(f"📊 File size: {file_size / 1024 / 1024:.2f} MB")
    
    # Read last N lines if file is too large
    max_lines = 10000  # Last 10k lines
    lines_to_read = max_lines if file_size > 10 * 1024 * 1024 else None
    
    matches = defaultdict(list)
    line_numbers = defaultdict(list)
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            if lines_to_read:
                # Read last N lines
                all_lines = f.readlines()
                lines = all_lines[-lines_to_read:]
                print(f"📖 Reading last {len(lines)} lines (file has {len(all_lines)} total lines)")
            else:
                lines = f.readlines()
                print(f"📖 Reading {len(lines)} lines")
            
            for line_num, line in enumerate(lines, start=1):
                line_lower = line.lower()
                
                # Check each pattern category
                for category, patterns in PATTERNS.items():
                    for pattern in patterns:
                        if re.search(pattern, line_lower, re.IGNORECASE):
                            matches[category].append(line.strip())
                            line_numbers[category].append(line_num)
                            break  # Only count once per line
    
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return {}
    
    return {
        "matches": matches,
        "line_numbers": line_numbers,
        "total_lines": len(lines)
    }


def print_summary(results: Dict):
    """Print analysis summary"""
    print("\n" + "=" * 60)
    print("📊 ANALYSIS SUMMARY")
    print("=" * 60)
    
    if not results:
        print("❌ No results to display")
        return
    
    for category, matches in results["matches"].items():
        count = len(matches)
        if count > 0:
            print(f"\n🔍 {category.upper().replace('_', ' ')}: {count} occurrences")
            print("-" * 60)
            
            # Show first 5 examples
            for i, match in enumerate(matches[:5], 1):
                # Truncate long lines
                display = match[:200] + "..." if len(match) > 200 else match
                print(f"  {i}. {display}")
            
            if count > 5:
                print(f"  ... and {count - 5} more")
            
            # Show line numbers
            if category in results["line_numbers"]:
                line_nums = results["line_numbers"][category]
                if line_nums:
                    print(f"  📍 Line numbers: {line_nums[:10]}{'...' if len(line_nums) > 10 else ''}")


def find_evaluation_requests(results: Dict) -> List[str]:
    """Find log entries related to evaluation requests"""
    evaluation_keywords = [
        "evaluation_bot",
        "truthfulqa",
        "halu_eval",
        "citation_rate",
        "hallucination",
    ]
    
    evaluation_lines = []
    for category, matches in results["matches"].items():
        for match in matches:
            match_lower = match.lower()
            if any(keyword in match_lower for keyword in evaluation_keywords):
                evaluation_lines.append(match)
    
    return evaluation_lines


def print_evaluation_context(results: Dict, log_file: str):
    """Print context around evaluation-related errors"""
    print("\n" + "=" * 60)
    print("🔍 EVALUATION-SPECIFIC ERRORS")
    print("=" * 60)
    
    evaluation_lines = find_evaluation_requests(results)
    
    if not evaluation_lines:
        print("ℹ️  No evaluation-specific errors found")
        return
    
    print(f"Found {len(evaluation_lines)} evaluation-related log entries:\n")
    
    for i, line in enumerate(evaluation_lines[:10], 1):
        print(f"{i}. {line[:300]}{'...' if len(line) > 300 else ''}")
    
    if len(evaluation_lines) > 10:
        print(f"\n... and {len(evaluation_lines) - 10} more")


def suggest_fixes(results: Dict):
    """Suggest fixes based on analysis"""
    print("\n" + "=" * 60)
    print("💡 SUGGESTED FIXES")
    print("=" * 60)
    
    suggestions = []
    
    if results["matches"].get("llm_failed"):
        suggestions.append("""
🔴 LLM API FAILURES DETECTED:
   - Check API keys are valid
   - Check rate limits / quotas
   - Verify network connectivity
   - Consider adding retry logic
        """)
    
    if results["matches"].get("validation_failed"):
        suggestions.append("""
🟡 VALIDATION FAILURES DETECTED:
   - Review validation thresholds
   - Check if validators are too strict
   - Consider adjusting citation requirements
   - Review language mismatch detection
        """)
    
    if results["matches"].get("fallback_triggered"):
        suggestions.append("""
🟠 FALLBACK MESSAGES TRIGGERED:
   - This is expected when errors occur
   - But too many = system issue
   - Check root cause (LLM failures, validation failures)
        """)
    
    if results["matches"].get("empty_response"):
        suggestions.append("""
🔴 EMPTY RESPONSES DETECTED:
   - LLM may be returning None/empty
   - Check LLM provider configuration
   - Verify prompt is not too long
   - Check for context overflow errors
        """)
    
    if not suggestions:
        print("✅ No obvious issues found in logs")
        print("   Consider checking:")
        print("   - LLM provider configuration")
        print("   - Validation chain thresholds")
        print("   - Network/API connectivity")
    else:
        for suggestion in suggestions:
            print(suggestion)


def main():
    """Main analysis function"""
    print("=" * 60)
    print("🔍 BACKEND LOG ANALYSIS FOR EVALUATION ISSUES")
    print("=" * 60)
    print()
    
    # Get log file path
    if len(sys.argv) > 1:
        log_file = sys.argv[1]
    else:
        # Try to find log files
        log_files = find_log_files()
        if not log_files:
            print("❌ No log files found in common locations")
            print("\nPlease provide log file path:")
            print("  python scripts/analyze_evaluation_logs.py <log_file_path>")
            return
        
        if len(log_files) == 1:
            log_file = log_files[0]
            print(f"📁 Using found log file: {log_file}")
        else:
            print("📁 Found multiple log files:")
            for i, f in enumerate(log_files, 1):
                print(f"  {i}. {f}")
            choice = input("\nEnter number to analyze (or path to custom file): ")
            try:
                idx = int(choice) - 1
                log_file = log_files[idx]
            except:
                log_file = choice
    
    # Analyze
    results = analyze_log_file(log_file)
    
    if not results:
        return
    
    # Print summary
    print_summary(results)
    
    # Print evaluation-specific context
    print_evaluation_context(results, log_file)
    
    # Suggest fixes
    suggest_fixes(results)
    
    print("\n" + "=" * 60)
    print("✅ Analysis complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()




