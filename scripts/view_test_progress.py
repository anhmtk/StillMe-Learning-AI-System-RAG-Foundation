#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
View test progress in real-time
Monitors test results file and displays progress
"""

import json
import time
import glob
from pathlib import Path
from datetime import datetime

RESULTS_DIR = Path(__file__).parent.parent / "tests" / "results"

def get_latest_results_file():
    """Get the most recent test results file"""
    files = sorted(glob.glob(str(RESULTS_DIR / "comprehensive_test_*.json")))
    if not files:
        return None
    return files[-1]

def view_progress():
    """View test progress in real-time"""
    print("=" * 60)
    print("TEST PROGRESS MONITOR")
    print("=" * 60)
    print("Watching for test results...")
    print("Press Ctrl+C to stop\n")
    
    last_count = 0
    last_file = None
    
    try:
        while True:
            results_file = get_latest_results_file()
            
            if results_file and results_file != last_file:
                print(f"\n📁 Found results file: {Path(results_file).name}")
                last_file = results_file
            
            if results_file and Path(results_file).exists():
                try:
                    with open(results_file, "r", encoding="utf-8") as f:
                        results = json.load(f)
                    
                    current_count = len(results)
                    
                    if current_count > last_count:
                        # New results added
                        success = sum(1 for r in results if r.get("status") == "success")
                        errors = sum(1 for r in results if r.get("status") == "error")
                        timeouts = sum(1 for r in results if r.get("status") == "timeout")
                        
                        if current_count > 0:
                            avg_latency = sum(r.get("latency", 0) for r in results if r.get("status") == "success" and r.get("latency")) / max(1, success)
                            avg_confidence = sum(r.get("confidence_score", 0) for r in results if r.get("status") == "success" and r.get("confidence_score")) / max(1, success)
                        else:
                            avg_latency = 0
                            avg_confidence = 0
                        
                        # Clear line and print progress
                        print(f"\r✅ Progress: {current_count} completed | Success: {success} | Errors: {errors} | Timeouts: {timeouts} | Avg Latency: {avg_latency:.2f}s | Avg Confidence: {avg_confidence:.2f}", end="", flush=True)
                        
                        last_count = current_count
                except (json.JSONDecodeError, KeyError) as e:
                    # File might be incomplete, wait for more data
                    pass
            
            time.sleep(1)  # Check every second
            
    except KeyboardInterrupt:
        print("\n\n" + "=" * 60)
        print("FINAL SUMMARY")
        print("=" * 60)
        
        if results_file and Path(results_file).exists():
            with open(results_file, "r", encoding="utf-8") as f:
                results = json.load(f)
            
            total = len(results)
            success = sum(1 for r in results if r.get("status") == "success")
            errors = sum(1 for r in results if r.get("status") == "error")
            timeouts = sum(1 for r in results if r.get("status") == "timeout")
            
            print(f"Total: {total}")
            print(f"Success: {success} ({success/total*100:.1f}%)" if total > 0 else "Success: 0")
            print(f"Errors: {errors}")
            print(f"Timeouts: {timeouts}")
            
            if success > 0:
                avg_latency = sum(r.get("latency", 0) for r in results if r.get("status") == "success" and r.get("latency")) / success
                avg_confidence = sum(r.get("confidence_score", 0) for r in results if r.get("status") == "success" and r.get("confidence_score")) / success
                print(f"Avg Latency: {avg_latency:.2f}s")
                print(f"Avg Confidence: {avg_confidence:.2f}")
            
            print(f"\nResults file: {results_file}")
        else:
            print("No results file found")

if __name__ == "__main__":
    view_progress()

